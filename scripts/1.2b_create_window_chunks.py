#!/usr/bin/env python3
"""
Script 1.2c: Criação de Chunks com Janelamento Fixo (Sliding Window)

Processa documentos markdown (Exposição de Motivos, Leis, Pareceres) com 
janelamento de tamanho fixo para RAG.

Estratégia:
- Janelas de tamanho fixo (ex: 500 palavras)
- Sobreposição entre janelas (ex: 100 palavras)
- Título completo do documento adicionado como prefixo de cada chunk
- Rastreamento de referências legais (Lei nº X, art. Y)
- Metadados extraídos do dicionário document_metadata.py

Estrutura de entrada:  data/processed/markdown/legislation/*.md
Estrutura de saída:    data/processed/json/legislation/*.json

Cada chunk contém:
- chunk_id: ID único da janela
- window_num: Número da janela
- content: "PROJETO DE LEI... - Lei nº X - Tipo\\n\\n[conteúdo da janela]"
- legal_references: Leis/artigos mencionados
- word_count: Contagem de palavras
- document_name: Nome do documento
- document_type: Tipo ("Exposição de Motivos", "Lei", etc)
- project_number: Número do projeto ("PL Nº 1.087, DE 2025")
- converted_to_law: Lei resultante ("Lei nº 15.270, de 2025")
- created_at: Timestamp

Uso:
    python scripts/1.2c_create_window_chunks.py \\
        --file pl-1087-25_Exm-0019-25-MF_doc.md \\
        --window-size 500 --overlap 100

    python scripts/1.2c_create_window_chunks.py \\
        --window-size 600 --overlap 150
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import sys

# Importar metadados dos documentos
sys.path.insert(0, str(Path(__file__).parent))
try:
    from document_metadata import get_document_metadata
except ImportError:
    def get_document_metadata(doc_stem: str) -> dict:
        return {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class WindowChunk:
    """Representa um chunk de janelamento fixo"""
    chunk_id: str
    window_num: int
    content: str  # Inclui título completo como prefixo
    legal_references: List[str]
    word_count: int
    char_count: int
    document_name: str
    document_type: str
    project_number: Optional[str]
    converted_to_law: Optional[str]
    created_at: str


class SlidingWindowChunker:
    """Cria chunks com janelamento fixo"""
    
    LAW_CITATION_PATTERN = re.compile(
        r'(?:Lei\s+n[ºo]?\s*(?:[\d.]+|[IVXLCDM]+)|'
        r'art\.?\s*\d+[º°a-z]?|'
        r'artigo\s+\d+[º°a-z]?|'
        r'§\s*\d+)',
        re.IGNORECASE
    )
    
    def __init__(
        self,
        window_size: int = 500,
        overlap: int = 100,
        base_dir: Optional[Path] = None
    ):
        self.window_size = window_size
        self.overlap = overlap
        
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        self.base_dir = Path(base_dir)
    
    def process_file(self, md_path: Path) -> List[WindowChunk]:
        """Processa arquivo markdown e cria chunks com janelamento"""
        if not md_path.exists():
            logger.error(f"Arquivo não encontrado: {md_path}")
            return []
        
        logger.info(f"Processando: {md_path.name}")
        text = md_path.read_text(encoding='utf-8')
        # Limpar non-breaking spaces
        text = text.replace('\xa0', ' ')
        
        chunks: List[WindowChunk] = []
        doc_name = md_path.stem
        
        # Obter metadados do documento
        doc_metadata = get_document_metadata(doc_name)
        doc_type = doc_metadata.get('type', 'Documento')
        project_number = doc_metadata.get('project_number')
        converted_to_law = doc_metadata.get('converted_to_law')
        
        # Construir título completo para prefixo
        title_parts = []
        if project_number:
            title_parts.append(project_number)
        if converted_to_law:
            title_parts.append(f"Convertido na {converted_to_law}")
        title_parts.append(f"{doc_type}")
        
        full_title = " - ".join(title_parts) if title_parts else doc_name
        
        # Dividir texto em palavras
        words = text.split()
        total_words = len(words)
        
        # Criar janelas
        step = self.window_size - self.overlap
        window_num = 1
        
        for start in range(0, total_words, step):
            end = min(start + self.window_size, total_words)
            
            # Conteúdo da janela
            window_words = words[start:end]
            window_text = ' '.join(window_words)
            
            # Adicionar título completo como prefixo
            full_content = f"{full_title}\n\n{window_text}"
            
            # Extrair referências legais
            legal_refs = self._extract_citations(window_text)
            
            chunk_id = f"{doc_name}_window_{window_num:04d}"
            
            chunk = WindowChunk(
                chunk_id=chunk_id,
                window_num=window_num,
                content=full_content,
                legal_references=legal_refs,
                word_count=len(window_words),
                char_count=len(window_text),
                document_name=doc_name,
                document_type=doc_type,
                project_number=project_number,
                converted_to_law=converted_to_law,
                created_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
            window_num += 1
        
        logger.info(f"   ✅ Extraídas {len(chunks)} janelas de {self.window_size}w")
        logger.info(f"   📋 Tipo: {doc_type} | Lei: {converted_to_law or 'N/A'}")
        return chunks
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extrai referências legais mencionadas no texto"""
        matches = self.LAW_CITATION_PATTERN.findall(text)
        # Normalizar e remover duplicatas
        normalized = []
        for m in matches:
            norm = ' '.join(m.split())
            if norm not in normalized:
                normalized.append(norm)
        return normalized
    
    def save_chunks(self, chunks: List[WindowChunk], output_path: Path) -> None:
        """Salva chunks em arquivo JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "document": chunks[0].document_name if chunks else "unknown",
            "document_type": chunks[0].document_type if chunks else "unknown",
            "project_number": chunks[0].project_number if chunks else None,
            "converted_to_law": chunks[0].converted_to_law if chunks else None,
            "total_chunks": len(chunks),
            "chunking_method": "sliding_window",
            "parameters": {
                "window_size": self.window_size,
                "overlap": self.overlap
            },
            "created_at": datetime.now().isoformat(),
            "chunks": [asdict(c) for c in chunks]
        }
        
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        try:
            rel_path = output_path.relative_to(self.base_dir)
        except ValueError:
            rel_path = output_path
        logger.info(f"   ✅ Salvo em: {rel_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cria chunks com janelamento fixo para RAG"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Processar um único arquivo"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/processed/markdown/legislation"),
        help="Diretório de entrada"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/json/legislation"),
        help="Diretório de saída (padrão: data/processed/json/legislation)"
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=500,
        help="Tamanho de cada janela em palavras"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=100,
        help="Sobreposição entre janelas em palavras"
    )
    
    args = parser.parse_args()
    
    chunker = SlidingWindowChunker(
        window_size=args.window_size,
        overlap=args.overlap,
        base_dir=Path(__file__).parent.parent
    )
    
    logger.info("=" * 70)
    logger.info("🪟 Chunking com Janelamento Fixo (Sliding Window)")
    logger.info("=" * 70)
    logger.info(f"   Window size: {args.window_size}w")
    logger.info(f"   Overlap    : {args.overlap}w")
    logger.info("=" * 70)
    
    if args.file:
        # Processar arquivo específico
        if not args.file.is_absolute():
            args.file = args.input_dir / args.file
        
        chunks = chunker.process_file(args.file)
        if chunks:
            output_file = args.output_dir / f"{args.file.stem}_window.json"
            chunker.save_chunks(chunks, output_file)
    else:
        # Processar todos os MDs do diretório
        logger.info(f"Processando MDs em: {args.input_dir}")
        md_files = sorted(args.input_dir.glob("*.md"))
        
        total_chunks = 0
        for md_file in md_files:
            chunks = chunker.process_file(md_file)
            if chunks:
                output_file = args.output_dir / f"{md_file.stem}_window.json"
                chunker.save_chunks(chunks, output_file)
                total_chunks += len(chunks)
        
        logger.info("=" * 70)
        logger.info(f"✅ Processamento concluído! Total: {total_chunks} chunks")
        logger.info("=" * 70)


if __name__ == "__main__":
    main()
