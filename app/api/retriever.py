"""Retrieval module - integração com src/retrieval (HybridRetriever, DenseRetriever, BM25Retriever)."""

from typing import List, Tuple, Optional
from app.api.config import settings

try:
    from src.retrieval.hybrid_retriever import HybridRetriever, RetrievalResult
    from src.retrieval.dense_retriever import DenseRetriever
    from src.retrieval.bm25_retriever import BM25Retriever
    RETRIEVAL_AVAILABLE = True
except ImportError:
    RETRIEVAL_AVAILABLE = False
    print("Warning: src.retrieval not available. Using mock retriever.")


class RetrieverBase:
    """Base retriever interface."""

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Retrieve relevant documents for a query.
        Returns: list of (document, similarity_score) tuples.
        """
        raise NotImplementedError


class SrcHybridRetriever(RetrieverBase):
    """Wrapper para usar HybridRetriever de src/retrieval."""

    def __init__(self):
        if not RETRIEVAL_AVAILABLE:
            raise ImportError("src.retrieval not available")
        
        try:
            self.dense_retriever = DenseRetriever()
            self.bm25_retriever = BM25Retriever()
            self.hybrid_retriever = HybridRetriever(
                dense_retriever=self.dense_retriever,
                bm25_retriever=self.bm25_retriever,
                alpha=settings.HYBRID_ALPHA,
                top_k=settings.TOP_K,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize HybridRetriever: {str(e)}")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """Retrieve using HybridRetriever from src/retrieval."""
        k = top_k or settings.TOP_K
        try:
            results = self.hybrid_retriever.retrieve(query, top_k=k)
            # Convert RetrievalResult objects to (content, score) tuples
            return [(result.content, result.score) for result in results]
        except Exception as e:
            print(f"Warning: HybridRetriever retrieval failed: {e}. Falling back to mock retriever.")
            return MockRetriever().retrieve(query, top_k)


class SrcDenseRetriever(RetrieverBase):
    """Wrapper para usar DenseRetriever de src/retrieval."""

    def __init__(self):
        if not RETRIEVAL_AVAILABLE:
            raise ImportError("src.retrieval not available")
        
        try:
            self.dense_retriever = DenseRetriever()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize DenseRetriever: {str(e)}")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """Retrieve using DenseRetriever from src/retrieval."""
        k = top_k or settings.TOP_K
        try:
            results = self.dense_retriever.retrieve(query, top_k=k)
            return [(result.content, result.score) for result in results]
        except Exception as e:
            print(f"Warning: DenseRetriever retrieval failed: {e}. Falling back to mock retriever.")
            return MockRetriever().retrieve(query, top_k)


class SrcBM25Retriever(RetrieverBase):
    """Wrapper para usar BM25Retriever de src/retrieval."""

    def __init__(self):
        if not RETRIEVAL_AVAILABLE:
            raise ImportError("src.retrieval not available")
        
        try:
            self.bm25_retriever = BM25Retriever()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize BM25Retriever: {str(e)}")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """Retrieve using BM25Retriever from src/retrieval."""
        k = top_k or settings.TOP_K
        try:
            results = self.bm25_retriever.retrieve(query, top_k=k)
            return [(result.content, result.score) for result in results]
        except Exception as e:
            print(f"Warning: BM25Retriever retrieval failed: {e}. Falling back to mock retriever.")
            return MockRetriever().retrieve(query, top_k)


class MockRetriever(RetrieverBase):
    """Mock retriever for demo/testing purposes."""

    def __init__(self):
        # Sample knowledge base
        self.documents = [
            "LION é um sistema de busca de informações baseado em RAG (Retrieval-Augmented Generation).",
            "O sistema LION utiliza embeddings para recuperar documentos relevantes.",
            "A arquitetura de LION combina BM25 para busca léxica com embeddings densos.",
            "O projeto LION está localizado em /home/decode/workspace/lion.",
            "LION suporta múltiplos provedores de LLM: Groq, OpenAI, Anthropic.",
            "A API de LION está sendo desenvolvida em FastAPI.",
            "O sistema RAG melhora a qualidade das respostas ao fornecer contexto relevante.",
            "Perguntas sobre IRPF podem ser respondidas pelo sistema de análise de documentos.",
            "Imposto de renda é o imposto federal sobre renda de pessoas físicas e jurídicas.",
            "A declaração de imposto de renda é obrigatória para residentes no Brasil com renda acima do limite.",
        ]

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """Simple keyword-based retrieval."""
        k = top_k or settings.TOP_K
        query_lower = query.lower()

        # Simple matching: score based on keyword overlap
        scored_docs = []
        for doc in self.documents:
            score = sum(1 for word in query_lower.split() if word in doc.lower()) / max(len(query_lower.split()), 1)
            if score > 0:
                scored_docs.append((doc, score))

        # Sort by score and return top-k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:k]


def get_retriever() -> RetrieverBase:
    """Factory function to get configured retriever."""
    retrieval_type = settings.RETRIEVAL_TYPE.lower()

    if retrieval_type == "hybrid" and RETRIEVAL_AVAILABLE:
        try:
            return SrcHybridRetriever()
        except Exception as e:
            print(f"Warning: HybridRetriever initialization failed: {e}. Using mock retriever.")
            return MockRetriever()
    elif retrieval_type == "dense" and RETRIEVAL_AVAILABLE:
        try:
            return SrcDenseRetriever()
        except Exception as e:
            print(f"Warning: DenseRetriever initialization failed: {e}. Using mock retriever.")
            return MockRetriever()
    elif retrieval_type == "bm25" and RETRIEVAL_AVAILABLE:
        try:
            return SrcBM25Retriever()
        except Exception as e:
            print(f"Warning: BM25Retriever initialization failed: {e}. Using mock retriever.")
            return MockRetriever()
    else:
        print(f"Using mock retriever (RETRIEVAL_TYPE={retrieval_type})")
        return MockRetriever()


# Lazy initialization
_retriever_instance = None


def get_retriever_instance() -> RetrieverBase:
    """Get or create retriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = get_retriever()
    return _retriever_instance

