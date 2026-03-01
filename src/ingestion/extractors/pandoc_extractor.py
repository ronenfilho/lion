"""
Pandoc Extractor - LION
Converte documentos (PDF, HTML, DOC, DOCX) para Markdown e JSON usando Pandoc

Funcionalidades:
- Conversão de múltiplos formatos via Pandoc
- Geração de AST JSON (Pandoc native format)
- Salvamento de metadados com hash SHA256 (cache incremental)
- Suporte a processamento paralelo via ThreadPoolExecutor
"""

import subprocess
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

logger = logging.getLogger(__name__)


@dataclass
class PandocSection:
    """Representa uma seção extraída via Pandoc (baseada em headers Markdown)."""
    title: str
    content: str
    level: int
    metadata: Dict[str, any]


@dataclass
class ConversionMetadata:
    """Metadados de conversão de documentos."""
    source_file: str
    source_hash: str
    source_type: str
    file_type: str
    processing_date: str
    markdown_path: str
    json_path: str
    file_size_bytes: int
    markdown_size_bytes: int


class PandocExtractor:
    """
    Extrai e converte documentos para Markdown/JSON usando Pandoc.

    Segue o mesmo contrato dos demais extractors:
        extractor.extract(file_path) → Dict[metadata, sections, full_text, source]

    Formatos suportados pelo Pandoc: .html, .htm, .docx, .txt, .md
    PDFs são delegados automaticamente ao PDFExtractor (PyMuPDF).
    Arquivos .doc são convertidos para .docx via LibreOffice antes do Pandoc.
    """

    # Formatos que o Pandoc consegue ler diretamente
    PANDOC_EXTENSIONS = {'.html', '.htm', '.docx', '.txt', '.md'}
    # Formatos suportados no total (incluindo delegação)
    SUPPORTED_EXTENSIONS = PANDOC_EXTENSIONS | {'.pdf', '.doc'}

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        markdown_dir: Optional[Path] = None,
        json_dir: Optional[Path] = None,
        metadata_dir: Optional[Path] = None,
        pandoc_timeout: int = 300,
    ):
        """
        Inicializa o extractor.

        Args:
            base_dir: Raiz do projeto (default: dois níveis acima deste arquivo)
            markdown_dir: Diretório de saída para .md (default: data/processed/markdown)
            json_dir: Diretório de saída para .json AST (default: data/processed/json)
            metadata_dir: Diretório de metadados de cache (default: data/processed/metadata)
            pandoc_timeout: Timeout em segundos para chamadas ao Pandoc
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent  # src/ingestion/extractors → raiz

        self.base_dir = Path(base_dir)
        self.pandoc_timeout = pandoc_timeout

        self.markdown_dir = Path(markdown_dir) if markdown_dir else self.base_dir / "data" / "processed" / "markdown"
        self.json_dir = Path(json_dir) if json_dir else self.base_dir / "data" / "processed" / "json"
        self.metadata_dir = Path(metadata_dir) if metadata_dir else self.base_dir / "data" / "processed" / "metadata"

        self._check_pandoc()

        # PDFExtractor é instanciado sob demanda (lazy) para não forçar importação
        self._pdf_extractor = None

    # ------------------------------------------------------------------
    # Contrato público: extract()
    # ------------------------------------------------------------------

    def extract(self, file_path: str, source_type: str = "legislation") -> Dict[str, any]:
        """
        Converte um documento para Markdown via Pandoc e retorna estrutura padronizada.

        Args:
            file_path: Caminho do arquivo de entrada
            source_type: Subcategoria ("legislation", "qa_reference", etc.)

        Returns:
            Dict contendo:
                - metadata: metadados do documento
                - sections: lista de PandocSection
                - full_text: texto completo em Markdown
                - source: nome do arquivo
                - markdown_path: caminho do .md gerado
                - json_path: caminho do .json AST gerado
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        ext = file_path.suffix.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Formato não suportado: {ext}")

        if ext == '.doc':
            return self._extract_doc(file_path, source_type)

        # PDFs são lidos pelo PyMuPDF (Pandoc não lê PDF)
        if ext == '.pdf':
            return self._extract_pdf(file_path, source_type)

        md_file = self._convert_to_markdown(file_path, source_type)
        json_file = self._convert_md_to_json(md_file, source_type)

        full_text = md_file.read_text(encoding="utf-8")
        sections = self._parse_markdown_sections(full_text)
        metadata = self._build_metadata(file_path, md_file, json_file, source_type)

        self._save_conversion_metadata(file_path, md_file, json_file, source_type)

        return {
            "metadata": {
                "title": file_path.stem,
                "source_type": source_type,
                "file_type": file_path.suffix,
                "processing_date": datetime.now().isoformat(),
                "file_size_bytes": file_path.stat().st_size,
            },
            "sections": sections,
            "full_text": full_text,
            "source": file_path.name,
            "markdown_path": str(md_file),
            "json_path": str(json_file),
        }

    # ------------------------------------------------------------------
    # Processamento em lote
    # ------------------------------------------------------------------

    def extract_directory(
        self,
        source_dir: Path,
        source_type: str,
        max_workers: int = 4,
        skip_cached: bool = True,
        extensions: Optional[set] = None,
    ) -> Tuple[int, int]:
        """
        Processa todos os arquivos de um diretório em paralelo.

        Args:
            source_dir: Diretório com arquivos a converter
            source_type: Tipo de documento ("legislation", "qa_reference", etc.)
            max_workers: Número de threads paralelas
            skip_cached: Pular arquivos já processados (via hash SHA256)
            extensions: Conjunto de extensões a filtrar, ex: {'.html', '.pdf'}.
                        Se None, processa todas as extensões suportadas.

        Returns:
            (sucessos, falhas)
        """
        files = self._get_files_to_process(Path(source_dir), skip_cached=skip_cached, extensions=extensions)

        if not files:
            logger.info(f"✓ Nenhum arquivo novo em '{source_type}'")
            return 0, 0

        success_count = 0
        failure_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.extract, str(f), source_type): f
                for f in files
            }
            with tqdm(total=len(files), desc=f"Convertendo {source_type}") as pbar:
                for future in as_completed(futures):
                    file_path = futures[future]
                    try:
                        future.result()
                        success_count += 1
                        logger.info(f"✅ {file_path.name}")
                    except Exception as e:
                        failure_count += 1
                        logger.error(f"❌ {file_path.name}: {e}")
                    finally:
                        pbar.update(1)

        return success_count, failure_count

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Internos: extração .doc via antiword
    # ------------------------------------------------------------------

    def _extract_doc(self, file_path: Path, source_type: str) -> Dict[str, any]:
        """
        Extrai texto de .doc preservando formatação via pipeline:
            antiword -x db → DocBook XML → Pandoc → Markdown

        O DocBook preserva bold, itálico e estrutura de parágrafos do Word.
        Headers hierárquicos (##) são gerados quando o .doc usa estilos Word de Heading;
        caso contrário (apenas bold), o texto é mantido com **negrito** Markdown.

        Args:
            file_path: Arquivo .doc de entrada
            source_type: Tipo de documento

        Returns:
            Dict com mesmo contrato de extract()

        Raises:
            RuntimeError: Se antiword não estiver disponível ou falhar
        """
        # 1. antiword → DocBook XML (preserva bold/italic/estrutura)
        try:
            antiword_proc = subprocess.run(
                ['antiword', '-x', 'db', str(file_path)],
                check=True,
                capture_output=True,
                timeout=120,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                "antiword não encontrado. Instale com: sudo apt install antiword"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Timeout ao extrair '{file_path.name}' com antiword") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"antiword falhou ao processar '{file_path.name}': {e.stderr.decode()}"
            ) from e

        # 2. Pandoc: DocBook → Markdown (pipe direto, sem arquivo intermediário)
        output_dir = self.markdown_dir / source_type
        output_dir.mkdir(parents=True, exist_ok=True)
        md_file = output_dir / f"{file_path.stem}_{file_path.suffix.lstrip('.')}.md"

        try:
            subprocess.run(
                [
                    'pandoc', '-f', 'docbook',
                    '-t', 'markdown+smart+fenced_code_blocks+pipe_tables+strikeout',
                    '--wrap=none',
                    '-o', str(md_file),
                ],
                input=antiword_proc.stdout,
                check=True,
                capture_output=True,
                timeout=self.pandoc_timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Timeout ao converter DocBook→MD para '{file_path.name}'") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Pandoc falhou ao converter DocBook de '{file_path.name}': {e.stderr}"
            ) from e

        md_text = md_file.read_text(encoding='utf-8')

        # 3. AST JSON via Pandoc
        json_file = self._convert_md_to_json(md_file, source_type)

        self._save_conversion_metadata(file_path, md_file, json_file, source_type)

        sections = self._parse_markdown_sections(md_text)

        return {
            "metadata": {
                "title": file_path.stem,
                "source_type": source_type,
                "file_type": file_path.suffix,
                "processing_date": datetime.now().isoformat(),
                "file_size_bytes": file_path.stat().st_size,
            },
            "sections": sections,
            "full_text": md_text,
            "source": file_path.name,
            "markdown_path": str(md_file),
            "json_path": str(json_file),
        }

    # ------------------------------------------------------------------
    # Internos: delegação PDF
    # ------------------------------------------------------------------

    def _extract_pdf(self, file_path: Path, source_type: str) -> Dict[str, any]:
        """
        Delega extração de PDF ao PDFExtractor (PyMuPDF) e salva o resultado
        como Markdown no diretório padrão, mantendo o mesmo contrato de retorno.
        """
        from .pdf_extractor import PDFExtractor

        if self._pdf_extractor is None:
            self._pdf_extractor = PDFExtractor()

        result = self._pdf_extractor.extract(str(file_path))

        # Salvar full_text como .md para manter pipeline uniforme
        output_dir = self.markdown_dir / source_type
        output_dir.mkdir(parents=True, exist_ok=True)
        md_file = output_dir / f"{file_path.stem}.md"

        sections_md = []
        for section in result.get("sections", []):
            sections_md.append(f"## {section.title}\n\n{section.content}")
        md_content = "\n\n".join(sections_md) if sections_md else result.get("full_text", "")
        md_file.write_text(md_content, encoding="utf-8")

        # JSON com estrutura simplificada (sem AST Pandoc)
        json_output_dir = self.json_dir / source_type
        json_output_dir.mkdir(parents=True, exist_ok=True)
        json_file = json_output_dir / f"{file_path.stem}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(
                {"source": file_path.name, "sections": [
                    {"title": s.title, "content": s.content, "level": s.level}
                    for s in result.get("sections", [])
                ]},
                f, ensure_ascii=False, indent=2
            )

        self._save_conversion_metadata(file_path, md_file, json_file, source_type)

        return {
            "metadata": result.get("metadata", {}),
            "sections": self._parse_markdown_sections(md_content),
            "full_text": md_content,
            "source": file_path.name,
            "markdown_path": str(md_file),
            "json_path": str(json_file),
        }

    # ------------------------------------------------------------------
    # Internos: conversão
    # ------------------------------------------------------------------

    def _convert_to_markdown(self, input_file: Path, source_type: str) -> Path:
        """Converte arquivo para Markdown usando Pandoc."""
        output_dir = self.markdown_dir / source_type
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{input_file.stem}.md"

        cmd = [
            "pandoc", str(input_file), "-o", str(output_file),
            "-t", "markdown+smart+fenced_code_blocks+pipe_tables+strikeout",
            "--wrap=none",
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=self.pandoc_timeout)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Timeout ao converter '{input_file.name}'") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pandoc falhou para '{input_file.name}': {e.stderr}") from e

        return output_file

    def _convert_md_to_json(self, md_file: Path, source_type: str) -> Path:
        """Converte Markdown para AST JSON (formato nativo do Pandoc)."""
        output_dir = self.json_dir / source_type
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{md_file.stem}.json"

        cmd = ["pandoc", str(md_file), "-t", "json", "-o", str(output_file)]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=self.pandoc_timeout)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Timeout ao gerar JSON de '{md_file.name}'") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pandoc falhou para '{md_file.name}': {e.stderr}") from e

        return output_file

    # ------------------------------------------------------------------
    # Internos: parsing e metadados
    # ------------------------------------------------------------------

    def _parse_markdown_sections(self, text: str) -> List[PandocSection]:
        """
        Divide o Markdown em seções baseadas em headers (#, ##, ###…).

        Returns:
            Lista de PandocSection em ordem de aparição
        """
        import re

        sections: List[PandocSection] = []
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        matches = list(header_pattern.finditer(text))

        if not matches:
            return [PandocSection(title="Documento", content=text.strip(), level=1, metadata={})]

        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            sections.append(PandocSection(
                title=title,
                content=content,
                level=level,
                metadata={"header_pos": match.start()},
            ))

        return sections

    def _build_metadata(
        self, input_file: Path, md_file: Path, json_file: Path, source_type: str
    ) -> Dict:
        return {
            "title": input_file.stem,
            "source_type": source_type,
            "file_type": input_file.suffix,
            "processing_date": datetime.now().isoformat(),
            "file_size_bytes": input_file.stat().st_size,
            "markdown_path": str(md_file),
            "json_path": str(json_file),
        }

    def _save_conversion_metadata(
        self, input_file: Path, md_file: Path, json_file: Path, source_type: str
    ) -> None:
        """Salva metadados de conversão para cache incremental (via SHA256)."""
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        meta = ConversionMetadata(
            source_file=str(input_file),
            source_hash=self._file_hash(input_file),
            source_type=source_type,
            file_type=input_file.suffix,
            processing_date=datetime.now().isoformat(),
            markdown_path=str(md_file),
            json_path=str(json_file),
            file_size_bytes=input_file.stat().st_size,
            markdown_size_bytes=md_file.stat().st_size,
        )

        metadata_file = self.metadata_dir / f"{input_file.stem}.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(asdict(meta), f, ensure_ascii=False, indent=2)

    def _get_files_to_process(
        self,
        source_dir: Path,
        skip_cached: bool = True,
        extensions: Optional[set] = None,
    ) -> List[Path]:
        """Retorna arquivos que ainda precisam ser processados.

        Args:
            source_dir: Diretório de origem
            skip_cached: Pular arquivos já processados (cache SHA256)
            extensions: Subconjunto de extensões a processar.
                        Se None, usa todas as SUPPORTED_EXTENSIONS.

        Quando existem versões .html e .pdf do mesmo documento, prioriza .html
        (Pandoc lê HTML nativamente; PDF é lido via PyMuPDF com menor fidelidade).
        """
        exts_to_scan = extensions if extensions else self.SUPPORTED_EXTENSIONS
        # Garantir que não escapem extensões fora das suportadas
        exts_to_scan = exts_to_scan & self.SUPPORTED_EXTENSIONS

        # Coletar arquivos das extensões solicitadas
        all_files: List[Path] = []
        for ext in exts_to_scan:
            all_files.extend(source_dir.glob(f"*{ext}"))

        # Deduplicar: se existir .html e .pdf com mesmo stem, manter apenas .html
        stems_with_html = {f.stem for f in all_files if f.suffix.lower() in {'.html', '.htm'}}
        all_files = [
            f for f in all_files
            if not (f.suffix.lower() == '.pdf' and f.stem in stems_with_html)
        ]

        if not skip_cached:
            return all_files

        to_process = []
        for file_path in all_files:
            metadata_file = self.metadata_dir / f"{file_path.stem}.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached.get("source_hash") == self._file_hash(file_path):
                    continue  # Não mudou — pular
            to_process.append(file_path)

        logger.info(f"📊 {len(all_files)} arquivos, {len(to_process)} para processar")
        return to_process

    @staticmethod
    def _file_hash(file_path: Path) -> str:
        """Calcula hash SHA256 do arquivo."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                h.update(block)
        return h.hexdigest()

    @staticmethod
    def _check_pandoc() -> None:
        """Verifica se o Pandoc está instalado."""
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True, text=True, check=True
            )
            version = result.stdout.split("\n")[0]
            logger.info(f"✅ {version}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError("Pandoc não encontrado. Instale com: sudo apt install pandoc") from e


def extract_with_pandoc(file_path: str, source_type: str = "legislation", **kwargs) -> Dict[str, any]:
    """
    Função helper para extração rápida com Pandoc.

    Args:
        file_path: Caminho do arquivo
        source_type: Tipo de documento
        **kwargs: Argumentos adicionais para PandocExtractor

    Returns:
        Dict com conteúdo extraído
    """
    extractor = PandocExtractor(**kwargs)
    return extractor.extract(file_path, source_type)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        print("Uso: python pandoc_extractor.py <arquivo> [source_type]")
        sys.exit(1)

    path = sys.argv[1]
    stype = sys.argv[2] if len(sys.argv) > 2 else "legislation"

    result = extract_with_pandoc(path, source_type=stype)

    print(f"\n✅ Extraído: {result['source']}")
    print(f"   Seções   : {len(result['sections'])}")
    print(f"   Caracteres: {len(result['full_text'])}")
    print(f"   Markdown  : {result['markdown_path']}")
    print(f"   JSON AST  : {result['json_path']}")
