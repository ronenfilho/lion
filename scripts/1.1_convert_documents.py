"""
Script 1.1: Conversão de Documentos — LION Pipeline
Ponto de entrada CLI para converter documentos brutos em Markdown estruturado.

Usa os extractors do pipeline (HTMLExtractor, PDFExtractor) que herdam de
BaseExtractor, chamando save_to_markdown() para persistir os resultados em:

    data/processed/markdown/legislation/*.md

Fontes suportadas:
    .html  → HTMLExtractor  (Padrão Planalto e Padrão RFB/Normas.RFB)
    .pdf   → PDFExtractor   (via PyMuPDF)

Diretório padrão de entrada:
    data/raw/legislation/

Uso:
    # Converter todos os HTMLs de legislation
    python scripts/1.1_convert_documents.py --ext html

    # Converter todos os PDFs
    python scripts/1.1_convert_documents.py --ext pdf

    # Converter tudo (html + pdf)
    python scripts/1.1_convert_documents.py

    # Converter arquivo específico
    python scripts/1.1_convert_documents.py --file data/raw/legislation/L15270.html

    # Alterar diretório de entrada
    python scripts/1.1_convert_documents.py --input-dir data/raw/legislation --ext html

    # Alterar diretório de saída
    python scripts/1.1_convert_documents.py --output-dir data/processed/markdown/legislation

    # Forçar reprocessamento (ignorar arquivos já existentes)
    python scripts/1.1_convert_documents.py --force
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.extractors.base_extractor import BaseExtractor
from src.ingestion.extractors.html_extractor import HTMLExtractor
from src.ingestion.extractors.pdf_extractor import PDFExtractor

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
DEFAULT_INPUT_DIR  = BASE_DIR / "data" / "raw" / "legislation"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "processed" / "markdown" / "legislation"

# Mapeamento extensão → extractor
EXTRACTOR_MAP: dict[str, type[BaseExtractor]] = {
    ".html": HTMLExtractor,
    ".pdf":  PDFExtractor,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_files(
    input_dir: Path,
    extensions: Optional[set[str]],
    single_file: Optional[Path],
) -> List[Path]:
    """Retorna lista de arquivos a processar."""
    if single_file:
        if not single_file.exists():
            logger.error(f"Arquivo não encontrado: {single_file}")
            sys.exit(1)
        return [single_file]

    if not input_dir.exists():
        logger.error(f"Diretório de entrada não encontrado: {input_dir}")
        sys.exit(1)

    exts = extensions or set(EXTRACTOR_MAP.keys())
    files = sorted(f for f in input_dir.iterdir() if f.suffix.lower() in exts)
    return files


def _get_extractor(ext: str) -> Optional[BaseExtractor]:
    """Retorna instância do extractor para a extensão, ou None se não suportado."""
    cls = EXTRACTOR_MAP.get(ext.lower())
    if cls is None:
        return None
    return cls()


def _already_processed(source: Path, output_dir: Path) -> bool:
    """Verifica se o arquivo de saída já existe."""
    out = output_dir / f"{source.stem}_processed.md"
    return out.exists()


# ---------------------------------------------------------------------------
# Processamento principal
# ---------------------------------------------------------------------------

def convert_file(
    source: Path,
    output_dir: Path,
    force: bool = False,
) -> Optional[bool]:
    """
    Converte um único arquivo para Markdown usando o extractor adequado.

    Args:
        source:     Caminho do arquivo de entrada
        output_dir: Pasta de saída para o .md gerado
        force:      Se True, reprocessa mesmo se saída já existir

    Returns:
        True se convertido com sucesso, False caso contrário
    """
    ext = source.suffix.lower()
    extractor = _get_extractor(ext)

    if extractor is None:
        logger.warning(f"⏭️  Extensão não suportada, pulando: {source.name}")
        return None

    if not force and _already_processed(source, output_dir):
        logger.info(f"⏩ Já processado, pulando (use --force para reprocessar): {source.name}")
        return None

    logger.info(f"📄 Convertendo [{ext}]: {source.name}")

    try:
        result = extractor.extract(str(source))
        md_path = extractor.save_to_markdown(
            source_path=source,
            result=result,
            output_dir=output_dir,
        )
        words = len(result.get("full_text", "").split())
        logger.info(f"   ✅ Salvo em: {md_path.relative_to(BASE_DIR)}  ({words:,} palavras)")
        return True

    except Exception as exc:
        logger.error(f"   ❌ Falha ao converter {source.name}: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte documentos brutos em Markdown estruturado via BaseExtractor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/1.1_convert_documents.py --ext html
  python scripts/1.1_convert_documents.py --ext pdf
  python scripts/1.1_convert_documents.py --ext html pdf
  python scripts/1.1_convert_documents.py --file data/raw/legislation/L15270.html
  python scripts/1.1_convert_documents.py --force
        """,
    )

    parser.add_argument(
        "--ext",
        nargs="+",
        metavar="EXT",
        default=None,
        help="Extensões a processar: html, pdf (padrão: todas suportadas)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        metavar="ARQUIVO",
        help="Processar um único arquivo específico",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        metavar="DIR",
        help=f"Diretório de entrada (padrão: {DEFAULT_INPUT_DIR.relative_to(BASE_DIR)})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        metavar="DIR",
        help=f"Diretório de saída (padrão: {DEFAULT_OUTPUT_DIR.relative_to(BASE_DIR)})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Reprocessar arquivos mesmo que o .md de saída já exista",
    )

    args = parser.parse_args()

    # Normalizar extensões (garantir ponto + lowercase)
    extensions: Optional[set[str]] = None
    if args.ext:
        extensions = {e if e.startswith(".") else f".{e}" for e in args.ext}
        unsupported = extensions - set(EXTRACTOR_MAP.keys())
        if unsupported:
            logger.error(
                f"Extensões não suportadas: {', '.join(unsupported)}\n"
                f"Suportadas: {', '.join(EXTRACTOR_MAP.keys())}"
            )
            sys.exit(1)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Coletar arquivos
    files = _collect_files(args.input_dir, extensions, args.file)

    if not files:
        logger.warning("⚠️  Nenhum arquivo encontrado para processar.")
        sys.exit(0)

    # Resumo inicial
    logger.info("=" * 70)
    logger.info("🚀 LION — Conversão de Documentos (BaseExtractor)")
    logger.info("=" * 70)
    logger.info(f"   Entrada  : {args.input_dir}")
    logger.info(f"   Saída    : {output_dir}")
    logger.info(f"   Arquivos : {len(files)}")
    logger.info(f"   Forçar   : {'sim' if args.force else 'não'}")
    logger.info("=" * 70)

    # Processar
    success = failure = skipped = 0
    for f in files:
        ext = f.suffix.lower()
        if ext not in EXTRACTOR_MAP:
            skipped += 1
            logger.debug(f"Ignorado (sem extractor): {f.name}")
            continue

        result = convert_file(f, output_dir, force=args.force)
        if result is True:
            success += 1
        elif result is None:
            skipped += 1
        else:  # False → erro real
            failure += 1

    # Resumo final
    logger.info("=" * 70)
    logger.info("✅ Conversão concluída!")
    logger.info(f"   Convertidos : {success}")
    logger.info(f"   Pulados     : {skipped}")
    logger.info(f"   Erros       : {failure}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
