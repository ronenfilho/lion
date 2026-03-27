"""Retrieval module - BM25 + embedding-based retrieval."""

from typing import List, Tuple, Optional
from app.api.config import settings


class RetrieverBase:
    """Base retriever interface."""

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Retrieve relevant documents for a query.
        Returns: list of (document, similarity_score) tuples.
        """
        raise NotImplementedError


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


class ChromaRetriever(RetrieverBase):
    """Chroma vector store retriever."""

    def __init__(self):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            self.collection = self.client.get_or_create_collection(name="documents")
        except ImportError:
            raise ImportError("chromadb package not installed. Run: pip install chromadb")
        except Exception as e:
            print(f"Warning: Chroma initialization failed: {e}. Falling back to mock retriever.")
            self.collection = None

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """Retrieve using Chroma vector store."""
        if self.collection is None or self.collection.count() == 0:
            # Fallback to mock if Chroma is empty
            return MockRetriever().retrieve(query, top_k)

        k = top_k or settings.TOP_K
        try:
            results = self.collection.query(query_texts=[query], n_results=k)
            docs = results["documents"][0] if results["documents"] else []
            distances = results["distances"][0] if results["distances"] else []

            # Convert distances to similarity scores (assuming cosine distance)
            scored_docs = [(doc, 1 - dist) for doc, dist in zip(docs, distances)]
            return scored_docs
        except Exception as e:
            print(f"Warning: Chroma retrieval failed: {e}. Falling back to mock retriever.")
            return MockRetriever().retrieve(query, top_k)


def get_retriever() -> RetrieverBase:
    """Factory function to get configured retriever."""
    try:
        return ChromaRetriever()
    except Exception:
        print("Using mock retriever (Chroma not available)")
        return MockRetriever()


# Lazy initialization
_retriever_instance = None


def get_retriever_instance() -> RetrieverBase:
    """Get or create retriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = get_retriever()
    return _retriever_instance
