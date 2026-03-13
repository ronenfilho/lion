"""
Cross-Encoder Reranker para LION RAG
Usa modelo cross-encoder para reranking pós-retrieval
Melhora significativa em relevância com latência controlada
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import time

try:
    from sentence_transformers import CrossEncoder, util
except ImportError:
    CrossEncoder = None
    util = None

from src.retrieval.hybrid_retriever import RetrievalResult


@dataclass
class RerankedResult:
    """Resultado de busca após reranking"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    rank: int
    original_rank: int  # Posição original antes do reranking
    source: str = 'cross_encoder_rerank'


class CrossEncoderReranker:
    """
    Reranker usando Cross-Encoder para refinar resultados de retrieval.
    
    Arquitetura:
    - Input: Query + N chunks (tipicamente N=10 do BM25)
    - Process: Cross-encoder score para cada (query, chunk) pair
    - Output: Top-k chunks reordenados por relevância
    
    Modelos suportados:
    - cross-encoder/mmarco-MiniLMv2-L12-H384 (recomendado)
    - cross-encoder/qnli-distilroberta-base
    - cross-encoder/stsb-roberta-base
    """
    
    DEFAULT_MODEL = 'cross-encoder/mmarco-MiniLMv2-L12-H384'
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        batch_size: int = 32,
        confidence_threshold: float = 0.0
    ):
        """
        Inicializa reranker com cross-encoder.
        
        Args:
            model_name: Nome do modelo HuggingFace
            device: 'cuda' ou 'cpu' (auto-detect se None)
            batch_size: Tamanho do batch para processamento
            confidence_threshold: Score mínimo para retornar chunk
        """
        if CrossEncoder is None:
            raise ImportError(
                "sentence-transformers não está instalado. "
                "Instale com: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.batch_size = batch_size
        self.confidence_threshold = confidence_threshold
        
        try:
            self.model = CrossEncoder(model_name, device=device)
            self.device = device or self.model.device
            print(f"✅ CrossEncoder loaded: {model_name}")
            print(f"   Device: {self.device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load cross-encoder {model_name}: {e}")
    
    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> List[RerankedResult]:
        """
        Rerank chunks usando cross-encoder.
        
        Args:
            query: Query string
            results: Lista de resultados iniciais (de BM25 ou Dense)
            top_k: Número de resultados a retornar (default: len(results))
            batch_size: Tamanho do batch (usa default se None)
            
        Returns:
            Lista de RerankedResult ordenada por score
        """
        if not results:
            return []
        
        k = top_k or len(results)
        batch_size = batch_size or self.batch_size
        
        start_time = time.time()
        
        # Preparar pares (query, chunk_text)
        pairs = [
            (query, r.content) for r in results
        ]
        
        # Computar scores com cross-encoder
        try:
            scores = self.model.predict(pairs, batch_size=batch_size, show_progress_bar=False)
            scores = scores.tolist() if hasattr(scores, 'tolist') else list(scores)
        except Exception as e:
            raise RuntimeError(f"Error computing cross-encoder scores: {e}")
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Combinar scores com metadados originais
        scored_results = [
            {
                'original_rank': idx + 1,
                'result': results[idx],
                'score': scores[idx]
            }
            for idx in range(len(results))
        ]
        
        # Filtrar por confidence_threshold se configurado
        if self.confidence_threshold > 0:
            scored_results = [
                r for r in scored_results 
                if r['score'] >= self.confidence_threshold
            ]
        
        # Ordenar por score (descendente)
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Criar RerankedResult
        reranked = []
        for new_rank, item in enumerate(scored_results[:k], 1):
            result = item['result']
            reranked.append(RerankedResult(
                id=result.id,
                content=result.content,
                score=item['score'],
                metadata={
                    **result.metadata,
                    'cross_encoder_score': item['score'],
                    'original_rank': item['original_rank'],
                    'latency_ms': latency_ms / len(results)  # Latência per-chunk
                },
                rank=new_rank,
                original_rank=item['original_rank']
            ))
        
        return reranked
    
    def rerank_batch(
        self,
        queries: List[str],
        results_list: List[List[RetrievalResult]],
        top_k: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> List[List[RerankedResult]]:
        """
        Rerank para múltiplas queries em lote.
        
        Args:
            queries: Lista de queries
            results_list: Lista de lista de resultados (um por query)
            top_k: Número de resultados por query
            batch_size: Tamanho do batch
            
        Returns:
            Lista de listas de RerankedResult
        """
        return [
            self.rerank(query, results, top_k, batch_size)
            for query, results in zip(queries, results_list)
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do reranker.
        
        Returns:
            Dict com informações sobre o modelo
        """
        return {
            'model_name': self.model_name,
            'model_type': 'cross_encoder',
            'device': str(self.device),
            'batch_size': self.batch_size,
            'confidence_threshold': self.confidence_threshold,
            'default_top_k': 'None (retorna todos os resultados)'
        }


class PipelinedRetriever:
    """
    Pipeline otimizado: BM25 (rápido) → CrossEncoder Rerank (qualidade).
    
    Estratégia:
    1. BM25 recupera 10 documentos rápidamente (~7.6ms)
    2. CrossEncoder rerank para top-3 (~50ms)
    3. Total: ~57.6ms vs 560ms de Dense puro
    4. Qualidade: Melhor que BM25 puro, latência controlada
    """
    
    def __init__(
        self,
        bm25_retriever,
        cross_encoder_model: str = CrossEncoderReranker.DEFAULT_MODEL,
        bm25_fetch_k: int = 10,
        final_top_k: int = 3,
        use_reranking: bool = True
    ):
        """
        Inicializa pipeline otimizado.
        
        Args:
            bm25_retriever: BM25Retriever inicializado
            cross_encoder_model: Modelo do cross-encoder
            bm25_fetch_k: Quantos docs buscar com BM25
            final_top_k: Quantos retornar após reranking
            use_reranking: Aplicar reranking? (sim por padrão)
        """
        self.bm25_retriever = bm25_retriever
        self.bm25_fetch_k = bm25_fetch_k
        self.final_top_k = final_top_k
        self.use_reranking = use_reranking
        
        if use_reranking:
            self.reranker = CrossEncoderReranker(model_name=cross_encoder_model)
        else:
            self.reranker = None
        
        print(f"✅ PipelinedRetriever inicializado")
        print(f"   BM25 fetch_k: {bm25_fetch_k}")
        print(f"   Reranking: {'Enabled' if use_reranking else 'Disabled'}")
        print(f"   Final top_k: {final_top_k}")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RerankedResult]:
        """
        Retrieve com pipeline: BM25 → (CrossEncoder Rerank).
        
        Args:
            query: Query string
            top_k: Top-k final (usa self.final_top_k se None)
            
        Returns:
            Lista de RerankedResult
        """
        k = top_k or self.final_top_k
        
        # 1. BM25: rápido
        bm25_results = self.bm25_retriever.retrieve(query, top_k=self.bm25_fetch_k)
        
        # 2. CrossEncoder Rerank (se habilitado)
        if self.use_reranking and self.reranker and len(bm25_results) > k:
            reranked = self.reranker.rerank(query, bm25_results, top_k=k)
            return reranked
        else:
            # Retornar como RerankedResult
            return [
                RerankedResult(
                    id=r.id,
                    content=r.content,
                    score=r.score,
                    metadata=r.metadata,
                    rank=idx + 1,
                    original_rank=idx + 1,
                    source='bm25'
                )
                for idx, r in enumerate(bm25_results[:k])
            ]
    
    def retrieve_batch(
        self,
        queries: List[str],
        top_k: Optional[int] = None
    ) -> List[List[RerankedResult]]:
        """
        Retrieve em lote.
        
        Args:
            queries: Lista de queries
            top_k: Top-k por query
            
        Returns:
            Lista de listas de RerankedResult
        """
        return [self.retrieve(query, top_k) for query in queries]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do pipeline.
        
        Returns:
            Dict com infos sobre BM25 e CrossEncoder
        """
        stats = {
            'type': 'pipelined',
            'bm25_fetch_k': self.bm25_fetch_k,
            'final_top_k': self.final_top_k,
            'use_reranking': self.use_reranking,
            'bm25_stats': self.bm25_retriever.get_stats() if hasattr(self.bm25_retriever, 'get_stats') else {}
        }
        
        if self.reranker:
            stats['reranker_stats'] = self.reranker.get_stats()
        
        return stats


# Exemplo de uso
if __name__ == "__main__":
    from src.retrieval.bm25_retriever import BM25Retriever
    from src.ingestion.vector_store import VectorStore
    
    print("=" * 80)
    print("🔄 Cross-Encoder Reranker Demo")
    print("=" * 80)
    
    # Inicializar
    vs = VectorStore(collection_name="irpf_2025")
    bm25 = BM25Retriever.from_vector_store(vector_store=vs, top_k=10)
    pipeline = PipelinedRetriever(bm25, final_top_k=3)
    
    print("\n📊 Pipeline Stats:")
    stats = pipeline.get_stats()
    print(f"   BM25 fetch: {stats['bm25_fetch_k']}")
    print(f"   Final top_k: {stats['final_top_k']}")
    print(f"   Reranking: {stats['use_reranking']}")
    
    # Teste
    query = "Quais são as deduções permitidas no IRPF 2025?"
    print(f"\n🔍 Query: {query}")
    
    results = pipeline.retrieve(query, top_k=3)
    
    print(f"\n📄 Top 3 Resultados:")
    for r in results:
        print(f"   [{r.rank}] Score: {r.score:.4f} (orig rank: {r.original_rank})")
        print(f"       ID: {r.id}")
        print(f"       Content: {r.content[:100]}...")
