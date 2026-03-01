"""
Script 2.1: Conversão de Documentos
Converte PDFs/HTMLs/DOC/DOCX para Markdown e JSON usando Pandoc

Pipeline:
    data/raw/legislation/*.{pdf,html} 
    → data/processed/markdown/legislation/*.md
    → data/processed/json/legislation/*.json
    → data/processed/metadata/*.json

Uso:
    python scripts/2.1_convert_documents.py
    python scripts/2.1_convert_documents.py --source legislation
    python scripts/2.1_convert_documents.py --max-workers 8
"""

import subprocess
import logging
import sys
from pathlib import Path
from typing import List, Optional
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion_errors.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


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


class DocumentConverter:
    """Conversor de documentos usando Pandoc."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.html', '.htm', '.doc', '.docx', '.txt', '.md'}
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Inicializa o conversor."""
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        
        # Estrutura de diretórios
        self.raw_legislation_dir = self.base_dir / "data" / "raw" / "legislation"
        self.raw_qa_dir = self.base_dir / "data" / "raw" / "qa_reference"
        
        self.processed_md_dir = self.base_dir / "data" / "processed" / "markdown"
        self.processed_json_dir = self.base_dir / "data" / "processed" / "json"
        self.processed_metadata_dir = self.base_dir / "data" / "processed" / "metadata"
        
        self._check_pandoc()
    
    def _check_pandoc(self) -> None:
        """Verifica se o Pandoc está instalado."""
        try:
            result = subprocess.run(
                ['pandoc', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.split('\n')[0]
            logger.info(f"✅ {version}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("❌ Pandoc não encontrado")
            raise RuntimeError("Instale Pandoc: sudo apt install pandoc") from e
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula hash SHA256 do arquivo."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_files_to_process(self, source_dir: Path) -> List[Path]:
        """Obtém arquivos que precisam ser processados."""
        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            files.extend(source_dir.glob(f"*{ext}"))
        
        # Filtra arquivos já processados
        files_to_process = []
        for file_path in files:
            metadata_file = self.processed_metadata_dir / f"{file_path.stem}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    current_hash = self._calculate_file_hash(file_path)
                    if metadata.get('source_hash') == current_hash:
                        continue  # Já processado
            
            files_to_process.append(file_path)
        
        logger.info(f"📊 {len(files)} arquivos, {len(files_to_process)} para processar")
        return files_to_process
    
    def convert_to_markdown(self, input_file: Path, source_type: str) -> Optional[Path]:
        """
        Converte arquivo para Markdown usando Pandoc.
        
        Args:
            input_file: Arquivo de entrada
            source_type: "legislation" ou "qa_reference"
            
        Returns:
            Caminho do arquivo Markdown ou None
        """
        output_subdir = self.processed_md_dir / source_type
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_subdir / f"{input_file.stem}.md"
        
        try:
            cmd = ['pandoc', str(input_file), '-o', str(output_file)]
            
            # Opções de conversão otimizadas
            cmd.extend([
                '-t', 'markdown+smart+fenced_code_blocks+pipe_tables+strikeout',
                '--wrap=none',
                '--extract-media=.'
            ])
            
            if input_file.suffix.lower() == '.pdf':
                cmd.extend(['--pdf-engine=xelatex'])
            
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
            logger.debug(f"✓ MD: {input_file.name}")
            return output_file
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Timeout ao converter {input_file.name}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao converter {input_file.name}: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado {input_file.name}: {str(e)}")
            return None
    
    def convert_md_to_json(self, md_file: Path, source_type: str) -> Optional[Path]:
        """
        Converte Markdown para JSON (AST do Pandoc).
        
        Args:
            md_file: Arquivo Markdown
            source_type: Tipo de documento
            
        Returns:
            Caminho do arquivo JSON ou None
        """
        output_subdir = self.processed_json_dir / source_type
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_subdir / f"{md_file.stem}.json"
        
        try:
            cmd = ['pandoc', str(md_file), '-t', 'json', '-o', str(output_file)]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
            
            logger.debug(f"✓ JSON: {md_file.name}")
            return output_file
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Timeout ao converter {md_file.name} para JSON")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao converter {md_file.name} para JSON: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {str(e)}")
            return None
    
    def _save_metadata(self, input_file: Path, md_file: Path, json_file: Path, 
                      source_type: str) -> None:
        """Salva metadados do processamento."""
        metadata = ConversionMetadata(
            source_file=str(input_file),
            source_hash=self._calculate_file_hash(input_file),
            source_type=source_type,
            file_type=input_file.suffix,
            processing_date=datetime.now().isoformat(),
            markdown_path=str(md_file),
            json_path=str(json_file),
            file_size_bytes=input_file.stat().st_size,
            markdown_size_bytes=md_file.stat().st_size
        )
        
        self.processed_metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = self.processed_metadata_dir / f"{input_file.stem}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)
    
    def process_file(self, input_file: Path, source_type: str) -> bool:
        """
        Pipeline: PDF/HTML → Markdown → JSON → Metadata.
        
        Args:
            input_file: Arquivo de entrada
            source_type: Tipo de documento
            
        Returns:
            True se sucesso
        """
        try:
            # 1. Converte para Markdown
            md_file = self.convert_to_markdown(input_file, source_type)
            if md_file is None:
                return False
            
            # 2. Converte para JSON
            json_file = self.convert_md_to_json(md_file, source_type)
            if json_file is None:
                return False
            
            # 3. Salva metadados
            self._save_metadata(input_file, md_file, json_file, source_type)
            
            logger.info(f"✅ {input_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {input_file.name}: {str(e)}")
            return False
    
    def process_directory(self, source_dir: Path, source_type: str, 
                         max_workers: int = 4) -> tuple[int, int]:
        """
        Processa todos os arquivos de um diretório em paralelo.
        
        Returns:
            (sucessos, falhas)
        """
        files = self._get_files_to_process(source_dir)
        
        if not files:
            logger.info(f"✓ Nenhum arquivo novo em {source_type}")
            return 0, 0
        
        success_count = 0
        failure_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_file, f, source_type): f 
                for f in files
            }
            
            with tqdm(total=len(files), desc=f"Convertendo {source_type}") as pbar:
                for future in as_completed(futures):
                    file_path = futures[future]
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                        else:
                            failure_count += 1
                    except Exception as e:
                        failure_count += 1
                        logger.error(f"❌ {file_path.name}: {str(e)}")
                    finally:
                        pbar.update(1)
        
        return success_count, failure_count
    
    def process_all(self, source: str = "all", max_workers: int = 4) -> None:
        """
        Processa documentos de acordo com a fonte especificada.
        
        Args:
            source: "legislation", "qa_reference" ou "all"
            max_workers: Número de workers paralelos
        """
        logger.info("=" * 80)
        logger.info("🚀 CONVERSÃO DE DOCUMENTOS - Pandoc Pipeline")
        logger.info("=" * 80)
        
        total_success = 0
        total_failure = 0
        
        if source in ["legislation", "all"]:
            logger.info("\n📚 Processando legislação...")
            leg_success, leg_failure = self.process_directory(
                self.raw_legislation_dir, "legislation", max_workers
            )
            total_success += leg_success
            total_failure += leg_failure
        
        if source in ["qa_reference", "all"]:
            logger.info("\n❓ Processando Q&A de referência...")
            qa_success, qa_failure = self.process_directory(
                self.raw_qa_dir, "qa_reference", max_workers
            )
            total_success += qa_success
            total_failure += qa_failure
        
        # Relatório
        logger.info("\n" + "=" * 80)
        logger.info("✅ Conversão concluída!")
        logger.info(f"   Sucessos: {total_success}")
        logger.info(f"   Falhas: {total_failure}")
        logger.info("=" * 80)


def main():
    """Executa o pipeline de conversão."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Converte documentos para Markdown e JSON')
    parser.add_argument(
        '--source',
        choices=['legislation', 'qa_reference', 'all'],
        default='all',
        help='Fonte de documentos para processar'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='Número de workers paralelos'
    )
    
    args = parser.parse_args()
    
    converter = DocumentConverter()
    converter.process_all(source=args.source, max_workers=args.max_workers)


if __name__ == "__main__":
    main()
