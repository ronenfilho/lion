"""
Dense Retriever - LION
Busca vetorial usando embeddings e ChromaDB
"""

from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass

from src.ingestion.vector_store import VectorStore, create_vector_store
from src.ingestion.embeddings_pipeline import EmbeddingsPipeline, create_embeddings_pipeline


@dataclass
class RetrievalResult:
    """Resultado de busca"""
    id: str
    content: str
    score: float  # Similaridade (1 = idêntico, 0 = oposto para cosine)
    metadata: Dict[str, Any]
    rank: int


class DenseRetriever:
    """
    Retriever baseado em embeddings densos.
    
    Usa busca por similaridade vetorial (cosine, L2 ou inner product)
    no ChromaDB para encontrar documentos relevantes.
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embeddings_pipeline: Optional[EmbeddingsPipeline] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ):
        """
        Inicializa dense retriever.
        
        Args:
            vector_store: Vector store (ChromaDB)
            embeddings_pipeline: Pipeline de embeddings
            top_k: Número de documentos a retornar
            similarity_threshold: Score mínimo (0-1 para cosine)
        """
        self.vector_store = vector_store or create_vector_store()
        self.embeddings_pipeline = embeddings_pipeline or create_embeddings_pipeline()
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Busca documentos relevantes para a query.
        
        Args:
            query: Texto da pergunta/query
            top_k: Número de resultados (usa self.top_k se None)
            filters: Filtros de metadata (ex: {"source": "D9580"})
            
        Returns:
            Lista de RetrievalResult ordenada por score
        """
        k = top_k or self.top_k
        
        # 1. Gerar embedding da query
        query_embedding = self._embed_query(query)
        
        # 2. Buscar no vector store
        raw_results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=k,
            where=filters
        )
        
        # 3. Converter para RetrievalResult
        results = []
        for rank, (doc_id, content, metadata, distance) in enumerate(
            zip(
                raw_results['ids'],
                raw_results['documents'],
                raw_results['metadatas'],
                raw_results['distances']
            ),
            1
        ):
            # Converter distância para score de similaridade
            # ChromaDB retorna distâncias (menor = mais similar)
            # Para cosine: distance = 1 - similarity, então similarity = 1 - distance
            score = 1.0 - distance
            
            # Filtrar por threshold
            if score >= self.similarity_threshold:
                results.append(RetrievalResult(
                    id=doc_id,
                    content=content,
                    score=score,
                    metadata=metadata,
                    rank=rank
                ))
        
        return results
    
    def retrieve_batch(
        self,
        queries: List[str],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[RetrievalResult]]:
        """
        Busca em lote para múltiplas queries.
        
        Args:
            queries: Lista de queries
            top_k: Número de resultados por query
            filters: Filtros de metadata
            
        Returns:
            Lista de listas de RetrievalResult
        """
        k = top_k or self.top_k
        
        # 1. Gerar embeddings das queries
        query_embeddings = self._embed_queries(queries)
        
        # 2. Buscar em lote
        batch_raw_results = self.vector_store.search_batch(
            query_embeddings=query_embeddings,
            n_results=k,
            where=filters
        )
        
        # 3. Converter para RetrievalResult
        batch_results = []
        for raw_results in batch_raw_results:
            results = []
            for rank, (doc_id, content, metadata, distance) in enumerate(
                zip(
                    raw_results['ids'],
                    raw_results['documents'],
                    raw_results['metadatas'],
                    raw_results['distances']
                ),
                1
            ):
                score = 1.0 - distance
                if score >= self.similarity_threshold:
                    results.append(RetrievalResult(
                        id=doc_id,
                        content=content,
                        score=score,
                        metadata=metadata,
                        rank=rank
                    ))
            batch_results.append(results)
        
        return batch_results
    
    def _embed_query(self, query: str) -> np.ndarray:
        """
        Gera embedding para uma query.
        
        Args:
            query: Texto da query
            
        Returns:
            Embedding (numpy array)
        """
        # Criar chunk temporário para a query
        from ingestion.chunking.structural_chunker import DocumentChunk
        
        query_chunk = DocumentChunk(
            chunk_id="query",
            content=query,
            source="query",
            metadata={}
        )
        
        # Gerar embedding (task_type="retrieval_query" para queries)
        embeddings = self.embeddings_pipeline.generate_embeddings(
            [query_chunk],
            task_type="retrieval_query",
            show_progress=False
        )
        
        return embeddings[0]
    
    def _embed_queries(self, queries: List[str]) -> List[np.ndarray]:
        """
        Gera embeddings para múltiplas queries.
        
        Args:
            queries: Lista de queries
            
        Returns:
            Lista de embeddings
        """
        from ingestion.chunking.structural_chunker import DocumentChunk
        
        # Criar chunks temporários
        query_chunks = [
            DocumentChunk(
                chunk_id=f"query_{i}",
                content=query,
                source="query",
                metadata={}
            )
            for i, query in enumerate(queries)
        ]
        
        # Gerar embeddings
        embeddings = self.embeddings_pipeline.generate_embeddings(
            query_chunks,
            task_type="retrieval_query",
            show_progress=False
        )
        
        return embeddings
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do retriever.
        
        Returns:
            Dict com estatísticas
        """
        store_stats = self.vector_store.get_stats()
        
        return {
            'retriever_type': 'dense',
            'top_k': self.top_k,
            'similarity_threshold': self.similarity_threshold,
            'embedding_dimension': self.embeddings_pipeline.dimension,
            'embedding_model': self.embeddings_pipeline.model_name,
            'vector_store_docs': store_stats['count'],
            'collection_name': store_stats['collection_name']
        }


def create_dense_retriever(
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None
) -> DenseRetriever:
    """
    Factory function para criar dense retriever.
    
    Args:
        top_k: Número de documentos (usa .env TOP_K se None)
        similarity_threshold: Score mínimo (usa .env SIMILARITY_THRESHOLD se None)
        
    Returns:
        DenseRetriever configurado
    """
    import os
    
    k = top_k or int(os.getenv('TOP_K', '5'))
    threshold = similarity_threshold or float(os.getenv('SIMILARITY_THRESHOLD', '0.0'))
    
    return DenseRetriever(
        top_k=k,
        similarity_threshold=threshold
    )


# Exemplo de uso
if __name__ == "__main__":
    # Criar retriever
    retriever = create_dense_retriever(top_k=3)
    
    print("📊 Dense Retriever Stats:")
    stats = retriever.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Busca de exemplo
    query = "Quais são as deduções permitidas no IRPF 2025?"
    print(f"\n🔍 Query: {query}")
    
    results = retriever.retrieve(query, top_k=3)
    
    print(f"\n📄 Resultados ({len(results)}):")
    for result in results:
        print(f"\n   [{result.rank}] Score: {result.score:.4f}")
        print(f"       ID: {result.id}")
        print(f"       {result.content[:150]}...")
