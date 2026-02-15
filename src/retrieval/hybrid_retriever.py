"""
Hybrid Retriever - LION
Combina busca vetorial (dense) e baseada em termos (BM25)
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
import numpy as np

from src.retrieval.dense_retriever import DenseRetriever, create_dense_retriever
from src.retrieval.bm25_retriever import BM25Retriever, create_bm25_retriever


@dataclass
class RetrievalResult:
    """Resultado de busca"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    rank: int
    source: Optional[str] = None  # 'dense', 'bm25', ou 'hybrid'


class HybridRetriever:
    """
    Retriever híbrido combinando busca vetorial e BM25.
    
    Usa Reciprocal Rank Fusion (RRF) para combinar rankings:
    - Dense retriever: captura similaridade semântica
    - BM25: captura matches exatos de termos
    - RRF: combina rankings de forma robusta
    
    Formula RRF: score = sum(1 / (k + rank)) para cada retriever
    onde k=60 é uma constante típica
    """
    
    def __init__(
        self,
        dense_retriever: Optional[DenseRetriever] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        alpha: float = 0.7,  # Peso do dense (0.7 = 70% dense, 30% BM25)
        top_k: int = 5,
        rrf_k: int = 60
    ):
        """
        Inicializa hybrid retriever.
        
        Args:
            dense_retriever: Retriever vetorial
            bm25_retriever: Retriever BM25
            alpha: Peso do dense retriever (0-1)
            top_k: Número de documentos finais
            rrf_k: Constante RRF (tipicamente 60)
        """
        self.dense_retriever = dense_retriever or create_dense_retriever()
        self.bm25_retriever = bm25_retriever
        self.alpha = alpha
        self.top_k = top_k
        self.rrf_k = rrf_k
        
        # Inicializar BM25 com docs do vector store se não fornecido
        if not self.bm25_retriever:
            self.bm25_retriever = create_bm25_retriever(
                vector_store=self.dense_retriever.vector_store,
                tokenizer="legal"
            )
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        method: str = "rrf"  # "rrf", "weighted", ou "dense_only"
    ) -> List[RetrievalResult]:
        """
        Busca documentos relevantes combinando métodos.
        
        Args:
            query: Texto da pergunta/query
            top_k: Número de resultados (usa self.top_k se None)
            filters: Filtros de metadata
            method: Método de fusão ("rrf", "weighted", "dense_only")
            
        Returns:
            Lista de RetrievalResult ordenada por score combinado
        """
        k = top_k or self.top_k
        
        # Buscar com cada retriever (pegar mais docs que o necessário)
        fetch_k = max(k * 2, 20)  # Buscar 2x mais docs
        
        dense_results = self.dense_retriever.retrieve(query, top_k=fetch_k, filters=filters)
        
        # BM25 apenas se não for dense_only
        if method != "dense_only":
            bm25_results = self.bm25_retriever.retrieve(query, top_k=fetch_k, filters=filters)
        else:
            bm25_results = []
        
        # Combinar resultados
        if method == "rrf":
            combined = self._reciprocal_rank_fusion(dense_results, bm25_results)
        elif method == "weighted":
            combined = self._weighted_fusion(dense_results, bm25_results)
        else:  # dense_only
            combined = dense_results
        
        # Retornar top-k
        return combined[:k]
    
    def _reciprocal_rank_fusion(
        self,
        dense_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Combina resultados usando Reciprocal Rank Fusion.
        
        RRF score = sum(1 / (k + rank)) para cada sistema
        
        Args:
            dense_results: Resultados do dense retriever
            bm25_results: Resultados do BM25
            
        Returns:
            Lista combinada ordenada por RRF score
        """
        # Mapear doc_id -> score RRF
        rrf_scores: Dict[str, float] = {}
        doc_data: Dict[str, tuple] = {}  # id -> (content, metadata)
        
        # Adicionar scores do dense retriever
        for result in dense_results:
            rrf_score = self.alpha / (self.rrf_k + result.rank)
            rrf_scores[result.id] = rrf_scores.get(result.id, 0) + rrf_score
            doc_data[result.id] = (result.content, result.metadata)
        
        # Adicionar scores do BM25
        for result in bm25_results:
            rrf_score = (1 - self.alpha) / (self.rrf_k + result.rank)
            rrf_scores[result.id] = rrf_scores.get(result.id, 0) + rrf_score
            if result.id not in doc_data:
                doc_data[result.id] = (result.content, result.metadata)
        
        # Criar lista ordenada
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        combined = []
        for rank, doc_id in enumerate(sorted_ids, 1):
            content, metadata = doc_data[doc_id]
            combined.append(RetrievalResult(
                id=doc_id,
                content=content,
                score=rrf_scores[doc_id],
                metadata=metadata,
                rank=rank,
                source='hybrid'
            ))
        
        return combined
    
    def _weighted_fusion(
        self,
        dense_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Combina resultados usando média ponderada de scores.
        
        Score final = alpha * dense_score + (1-alpha) * bm25_score_norm
        
        Args:
            dense_results: Resultados do dense retriever
            bm25_results: Resultados do BM25
            
        Returns:
            Lista combinada ordenada por score ponderado
        """
        # Normalizar scores BM25 para [0, 1]
        if bm25_results:
            max_bm25 = max(r.score for r in bm25_results)
            if max_bm25 > 0:
                for result in bm25_results:
                    result.score = result.score / max_bm25
        
        # Mapear doc_id -> score combinado
        combined_scores: Dict[str, float] = {}
        doc_data: Dict[str, tuple] = {}
        
        # Adicionar scores do dense
        for result in dense_results:
            combined_scores[result.id] = self.alpha * result.score
            doc_data[result.id] = (result.content, result.metadata)
        
        # Adicionar scores do BM25
        for result in bm25_results:
            bm25_contribution = (1 - self.alpha) * result.score
            combined_scores[result.id] = combined_scores.get(result.id, 0) + bm25_contribution
            if result.id not in doc_data:
                doc_data[result.id] = (result.content, result.metadata)
        
        # Criar lista ordenada
        sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
        
        combined = []
        for rank, doc_id in enumerate(sorted_ids, 1):
            content, metadata = doc_data[doc_id]
            combined.append(RetrievalResult(
                id=doc_id,
                content=content,
                score=combined_scores[doc_id],
                metadata=metadata,
                rank=rank,
                source='hybrid'
            ))
        
        return combined
    
    def retrieve_batch(
        self,
        queries: List[str],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        method: str = "rrf"
    ) -> List[List[RetrievalResult]]:
        """
        Busca em lote para múltiplas queries.
        
        Args:
            queries: Lista de queries
            top_k: Número de resultados por query
            filters: Filtros de metadata
            method: Método de fusão
            
        Returns:
            Lista de listas de RetrievalResult
        """
        return [
            self.retrieve(query, top_k, filters, method)
            for query in queries
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do retriever.
        
        Returns:
            Dict com estatísticas
        """
        dense_stats = self.dense_retriever.get_stats()
        bm25_stats = self.bm25_retriever.get_stats() if self.bm25_retriever else {}
        
        return {
            'retriever_type': 'hybrid',
            'alpha': self.alpha,
            'top_k': self.top_k,
            'rrf_k': self.rrf_k,
            'dense_stats': dense_stats,
            'bm25_stats': bm25_stats
        }


def create_hybrid_retriever(
    alpha: Optional[float] = None,
    top_k: Optional[int] = None
) -> HybridRetriever:
    """
    Factory function para criar hybrid retriever.
    
    Args:
        alpha: Peso do dense (usa .env HYBRID_ALPHA se None)
        top_k: Número de documentos (usa .env TOP_K se None)
        
    Returns:
        HybridRetriever configurado
    """
    import os
    
    weight = alpha or float(os.getenv('HYBRID_ALPHA', '0.7'))
    k = top_k or int(os.getenv('TOP_K', '5'))
    
    return HybridRetriever(alpha=weight, top_k=k)


# Exemplo de uso
if __name__ == "__main__":
    # Criar retriever
    retriever = create_hybrid_retriever(alpha=0.7, top_k=5)
    
    print("📊 Hybrid Retriever Stats:")
    stats = retriever.get_stats()
    print(f"   Type: {stats['retriever_type']}")
    print(f"   Alpha (dense weight): {stats['alpha']}")
    print(f"   Top K: {stats['top_k']}")
    print(f"   Dense docs: {stats['dense_stats']['vector_store_docs']}")
    print(f"   BM25 docs: {stats['bm25_stats'].get('num_documents', 0)}")
    
    # Busca de exemplo
    query = "Quais são as deduções permitidas no IRPF 2025?"
    print(f"\n🔍 Query: {query}")
    
    # Testar diferentes métodos
    for method in ["rrf", "weighted", "dense_only"]:
        results = retriever.retrieve(query, top_k=3, method=method)
        
        print(f"\n📄 Método: {method} ({len(results)} resultados)")
        for result in results[:2]:  # Mostrar top 2
            print(f"   [{result.rank}] Score: {result.score:.4f} | {result.id}")
