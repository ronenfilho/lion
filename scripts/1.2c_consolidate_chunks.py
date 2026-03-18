#!/usr/bin/env python3
"""
Script de Consolidação: Reunir Chunks de Artigos e Janelas

Combina chunks gerados pelos scripts 1.2 (artigos) e 1.2c (janelas) 
num único arquivo de referência para RAG.

Estrutura de entrada:
  - data/processed/json/legislation/*_processed.json (chunks de artigos)
  - data/processed/json/legislation/*_window.json (chunks de janelas)

Estrutura de saída:
  - data/processed/json/legislation/CONSOLIDADO_chunks.json

Uso:
    python scripts/consolidate_chunks.py
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def consolidate_chunks(input_dir: Path = Path("data/processed/json/legislation"), 
                       output_file: Path = Path("data/processed/json/legislation/CONSOLIDADO_chunks.json")) -> None:
    """
    Consolida chunks de artigos e janelas em um único arquivo
    
    Args:
        input_dir: Diretório com arquivos JSON
        output_file: Arquivo de saída consolidado
    """
    logger.info("=" * 70)
    logger.info("📚 Consolidação de Chunks (Artigos + Janelas)")
    logger.info("=" * 70)
    
    input_dir = Path(input_dir)
    
    # Encontrar arquivos
    article_files = list(input_dir.glob("*_processed.json"))
    window_files = list(input_dir.glob("*_window.json"))
    
    # Filtrar arquivos de estatísticas
    article_files = [f for f in article_files if not f.name.startswith('_')]
    window_files = [f for f in window_files if not f.name.startswith('_')]
    
    logger.info(f"📁 Entrada: {input_dir}")
    logger.info(f"   Arquivos de artigos: {len(article_files)}")
    logger.info(f"   Arquivos de janelas: {len(window_files)}")
    
    consolidated = {
        "consolidated_at": datetime.now().isoformat(),
        "documents": {
            "articles": [],
            "windows": []
        },
        "statistics": {
            "total_article_chunks": 0,
            "total_window_chunks": 0,
            "documents_processed": {}
        }
    }
    
    # Processar chunks de artigos
    logger.info(f"\n📄 Processando {len(article_files)} documentos de artigos...")
    for article_file in sorted(article_files):
        logger.info(f"   ➜ {article_file.name}")
        with open(article_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc_name = article_file.stem
        consolidated["documents"]["articles"].append({
            "source": article_file.name,
            "document": doc_name,
            "chunks": data["chunks"]
        })
        
        consolidated["statistics"]["total_article_chunks"] += len(data["chunks"])
        consolidated["statistics"]["documents_processed"][doc_name] = {
            "type": "article_chunks",
            "count": len(data["chunks"])
        }
    
    # Processar chunks de janelas
    logger.info(f"\n🪟 Processando {len(window_files)} documentos de janelas...")
    for window_file in sorted(window_files):
        logger.info(f"   ➜ {window_file.name}")
        with open(window_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc_name = window_file.stem.replace("_window", "")
        consolidated["documents"]["windows"].append({
            "source": window_file.name,
            "document": doc_name,
            "chunks": data["chunks"]
        })
        
        consolidated["statistics"]["total_window_chunks"] += len(data["chunks"])
        if doc_name not in consolidated["statistics"]["documents_processed"]:
            consolidated["statistics"]["documents_processed"][doc_name] = {}
        consolidated["statistics"]["documents_processed"][doc_name]["type"] = "window_chunks"
        consolidated["statistics"]["documents_processed"][doc_name]["window_count"] = len(data["chunks"])
    
    # Salvar arquivo consolidado
    output_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"\n💾 Salvando arquivo consolidado...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2)
    
    logger.info("=" * 70)
    logger.info("✅ Consolidação concluída!")
    logger.info(f"   📁 Saída: {output_file.name}")
    logger.info(f"   📊 Chunks de artigos: {consolidated['statistics']['total_article_chunks']}")
    logger.info(f"   📊 Chunks de janelas: {consolidated['statistics']['total_window_chunks']}")
    logger.info(f"   📊 Total: {consolidated['statistics']['total_article_chunks'] + consolidated['statistics']['total_window_chunks']}")
    logger.info("=" * 70)
    
    # Exibir resumo de documentos
    logger.info("\n📋 RESUMO POR DOCUMENTO")
    logger.info("-" * 70)
    for doc, stats in sorted(consolidated["statistics"]["documents_processed"].items()):
        if "count" in stats:
            logger.info(f"  {doc}: {stats['count']} chunks (artigos)")
        if "window_count" in stats:
            logger.info(f"  {doc}: {stats['window_count']} chunks (janelas)")


if __name__ == "__main__":
    consolidate_chunks()
