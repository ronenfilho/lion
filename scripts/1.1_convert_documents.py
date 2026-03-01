"""
Script 1.1: Conversão de Documentos
Ponto de entrada CLI para o PandocExtractor.

Pipeline:
    data/raw/legislation/*.{pdf,html,doc,docx}
    → data/processed/markdown/legislation/*.md
    → data/processed/json/legislation/*.json
    → data/processed/metadata/*.json (cache SHA256)

Uso:
    python scripts/1.1_convert_documents.py
    python scripts/1.1_convert_documents.py --source legislation
    python scripts/1.1_convert_documents.py --ext html
    python scripts/1.1_convert_documents.py --ext html pdf --source legislation
    python scripts/1.1_convert_documents.py --max-workers 8
"""

import argparse
import logging
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.extractors import PandocExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion_errors.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
RAW_DIRS = {
    "legislation": BASE_DIR / "data" / "raw" / "legislation",
    "qa_reference": BASE_DIR / "data" / "raw" / "qa_reference",
}


def main():
    parser = argparse.ArgumentParser(description='Converte documentos para Markdown e JSON via Pandoc')
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
    parser.add_argument(
        '--ext',
        nargs='+',
        metavar='EXT',
        default=None,
        help='Extensões a processar, ex: --ext html pdf docx (default: todas suportadas)'
    )
    args = parser.parse_args()

    # Normalizar extensões: garantir ponto no início e lowercase
    extensions = None
    if args.ext:
        extensions = {e if e.startswith('.') else f'.{e}' for e in args.ext}
        logger.info(f"🔍 Filtrando extensões: {', '.join(sorted(extensions))}")

    extractor = PandocExtractor(base_dir=BASE_DIR)

    logger.info("=" * 80)
    logger.info("🚀 CONVERSÃO DE DOCUMENTOS - Pandoc Pipeline")
    logger.info("=" * 80)

    sources = list(RAW_DIRS.keys()) if args.source == "all" else [args.source]
    total_success = total_failure = 0

    for source_type in sources:
        source_dir = RAW_DIRS[source_type]
        logger.info(f"\n📂 Processando '{source_type}': {source_dir}")
        success, failure = extractor.extract_directory(
            source_dir=source_dir,
            source_type=source_type,
            max_workers=args.max_workers,
            extensions=extensions,
        )
        total_success += success
        total_failure += failure

    logger.info("\n" + "=" * 80)
    logger.info("✅ Conversão concluída!")
    logger.info(f"   Sucessos : {total_success}")
    logger.info(f"   Falhas   : {total_failure}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
