"""
BaseExtractor - LION
Classe base abstrata para todos os extractors do pipeline de ingestão.

Provê métodos compartilhados de:
  - Leitura de arquivos com detecção de encoding
  - Correção de mojibake (cp1252 lido como latin-1)
  - Persistência em Markdown estruturado
  - Heurísticas de estrutura para documentos jurídicos brasileiros
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Mapeamento de heurísticas legais para documentos sem CSS semântico
# ---------------------------------------------------------------------------
LEGAL_HEURISTICS: List[Tuple[re.Pattern, str, int]] = [
    # (padrão, prefixo_markdown, nível_numérico)
    (re.compile(r"^\s*(LIVRO\s+[IVXLCDM]+\b.*)$", re.I), "# ", 1),
    (re.compile(r"^\s*(TÍTULO\s+[IVXLCDM]+\b.*)$", re.I), "## ", 2),
    (re.compile(r"^\s*(CAPÍTULO\s+[IVXLCDM0-9]+[-\w]*\b.*)$", re.I), "### ", 3),
    (re.compile(r"^\s*(SEÇÃO\s+[IVXLCDM0-9]+[-\w]*\b.*)$", re.I), "#### ", 4),
    (re.compile(r"^\s*(SUBSEÇÃO\s+[IVXLCDM0-9]+[-\w]*\b.*)$", re.I), "##### ", 5),
    (re.compile(r"^\s*(Art\.\s*\d+[º°]?(?:-[A-Z])?\.?\s*.*)$"), "######-art ", 6),
    (re.compile(r"^\s*(§\s*(?:único|Único|\d+[º°]?)\.?\s*.*)$"), "**§** ", None),
]

INCISO_PATTERN = re.compile(r"^\s*([IVX]+)\s*[-–—]\s*")
ALINEA_PATTERN = re.compile(r"^\s*([a-z])\)\s*")
NUMERO_PATTERN = re.compile(r"^\s*(\d+)\.\s+")


class BaseExtractor(ABC):
    """
    Classe base para todos os extractors do LION.

    Subclasses devem implementar `extract(file_path) -> Dict[str, Any]`.
    O dict retornado deve conter pelo menos:
        - metadata: Dict com campos do documento
        - sections: List de seções (objetos dataclass com .title/.content/.level)
        - full_text: str com texto concatenado

    Métodos utilitários disponíveis para subclasses:
        - _read_with_encoding(path) → str
        - _fix_mojibake(text) → str
        - _apply_legal_heuristics(lines) → List[str]
        - save_to_markdown(source_path, result, output_dir) → Path
    """

    # Encodings tentados nesta ordem ao ler arquivos
    ENCODING_PRIORITY = ["utf-8", "cp1252", "latin-1", "iso-8859-1"]

    # ------------------------------------------------------------------
    # Interface pública obrigatória
    # ------------------------------------------------------------------

    @abstractmethod
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extrai conteúdo estruturado do arquivo informado."""
        ...

    # ------------------------------------------------------------------
    # Leitura de arquivos
    # ------------------------------------------------------------------

    def _read_with_encoding(self, path: Path) -> str:
        """
        Lê arquivo tentando encodings em ordem de prioridade.
        Nunca lança UnicodeDecodeError — usa 'replace' como fallback final.

        Args:
            path: Caminho do arquivo

        Returns:
            Conteúdo do arquivo como string
        """
        for enc in self.ENCODING_PRIORITY:
            try:
                return path.read_text(encoding=enc)
            except (UnicodeDecodeError, LookupError):
                continue
        # Fallback absoluto
        return path.read_text(encoding="latin-1", errors="replace")

    def _detect_encoding(self, path: Path) -> str:
        """
        Detecta o encoding mais provável para o arquivo.
        Retorna o primeiro encoding que consegue ler sem erros.
        """
        for enc in self.ENCODING_PRIORITY:
            try:
                path.read_text(encoding=enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue
        return "latin-1"

    # ------------------------------------------------------------------
    # Correção de texto
    # ------------------------------------------------------------------

    def _fix_mojibake(self, text: str) -> str:
        """
        Corrige mojibake típico de documentos brasileiros (cp1252 lido como latin-1).

        Situação: o HTML declara charset=utf-8, mas o arquivo está em cp1252.
        Ao ler com latin-1 os bytes ficam "mal mapeados" — ex. 'Ã§' em vez de 'ç'.

        A correção re-encode o texto como latin-1 e decodifica como cp1252.
        """
        try:
            return text.encode("latin-1").decode("cp1252")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text

    def _clean_text(self, text: str) -> str:
        """Limpeza básica: múltiplos espaços, espaços em torno de newlines."""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Heurísticas jurídicas
    # ------------------------------------------------------------------

    def _apply_legal_heuristics(self, lines: List[str]) -> List[str]:
        """
        Aplica heurísticas de estrutura para documentos jurídicos brasileiros.

        Transforma linhas de texto puro em Markdown hierárquico usando padrões
        como LIVRO, TÍTULO, CAPÍTULO, SEÇÃO, Art., §, incisos e alíneas.

        Args:
            lines: Lista de linhas de texto puro

        Returns:
            Lista de linhas com marcadores Markdown inseridos
        """
        result: List[str] = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                result.append("")
                continue

            matched = False

            # Testar heurísticas hierárquicas
            for pattern, prefix, level in LEGAL_HEURISTICS:
                m = pattern.match(line)
                if m:
                    if prefix == "######-art ":
                        # Artigos: headline com âncora
                        art_text = m.group(1)
                        art_num_m = re.search(r"(\d+[º°]?(?:-[A-Z])?)", art_text)
                        art_id = art_num_m.group(1).replace("º", "").replace("°", "").lower() if art_num_m else ""
                        result.append("")
                        result.append(f"###### {art_text} {{#art-{art_id}}}")
                        result.append("")
                    elif prefix == "**§** ":
                        # Parágrafos: negrito
                        result.append("")
                        result.append(f"**{m.group(1)}**")
                        result.append("")
                    else:
                        result.append("")
                        result.append(f"{prefix}{m.group(1)}")
                        result.append("")
                    matched = True
                    break

            if matched:
                continue

            # Incisos romanos
            if INCISO_PATTERN.match(line):
                result.append(f"- {line}")
                continue

            # Alíneas
            if ALINEA_PATTERN.match(line):
                result.append(f"  - {line}")
                continue

            # Numeração ordinal
            if NUMERO_PATTERN.match(line):
                result.append(f"  - {line}")
                continue

            # Texto normal
            result.append(line)

        return result

    # ------------------------------------------------------------------
    # Persistência em Markdown
    # ------------------------------------------------------------------

    def save_to_markdown(
        self,
        source_path: Path,
        result: Dict[str, Any],
        output_dir: Optional[Path] = None,
        suffix: str = "_processed",
    ) -> Path:
        """
        Salva o resultado da extração em arquivo Markdown estruturado.

        O arquivo gerado contém:
            - Cabeçalho YAML-like com metadados
            - Corpo com texto hierárquico em Markdown

        Args:
            source_path: Caminho do arquivo de origem
            result: Dict retornado por extract()
            output_dir: Pasta de saída (padrão: data/processed/markdown/legislation/)
            suffix: Sufixo adicionado ao nome do arquivo de saída

        Returns:
            Path do arquivo .md gerado
        """
        if output_dir is None:
            output_dir = Path("data/processed/markdown/legislation")
        output_dir.mkdir(parents=True, exist_ok=True)

        md_path = output_dir / f"{source_path.stem}{suffix}.md"
        metadata = result.get("metadata", {})
        full_text = result.get("full_text", "")
        sections = result.get("sections", [])

        lines: List[str] = []

        # ---- Título ----
        title = metadata.get("title") or source_path.stem
        lines += [f"# {title}", ""]

        # ---- Bloco de metadados ----
        lines += [
            "<details>",
            "<summary>📋 Metadados do Documento</summary>",
            "",
            f"- **Arquivo**: `{source_path.name}`",
            f"- **Processado em**: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ]
        for key, value in metadata.items():
            if value and key != "title":
                lines.append(f"- **{key}**: {value}")
        lines += ["", "</details>", "", "---", ""]

        # ---- Índice de artigos ----
        articles = re.findall(r"Art\.?\s*(\d+[º°]?(?:-[A-Z])?)", full_text)
        seen: List[str] = []
        for a in articles:
            if a not in seen:
                seen.append(a)
        if seen:
            lines += ["## 📑 Índice de Artigos", ""]
            for art in seen[:30]:
                art_id = art.replace("º", "").replace("°", "").lower()
                lines.append(f"- [Art. {art}](#art-{art_id})")
            lines += ["", "---", ""]

        # ---- Conteúdo ----
        if sections:
            for section in sections:
                prefix = "#" * max(1, min(section.level, 6))
                lines += [f"{prefix}# {section.title}", ""]
                if section.content:
                    lines += section.content.split("\n")
                    lines.append("")
        else:
            # Fallback: texto puro com heurísticas
            raw_lines = full_text.split("\n")
            processed = self._apply_legal_heuristics(raw_lines)
            lines.extend(processed)

        # ---- Rodapé ----
        lines += ["", "---", "", "*Processado automaticamente pelo LION RAG System*"]

        md_path.write_text("\n".join(lines), encoding="utf-8")
        return md_path
