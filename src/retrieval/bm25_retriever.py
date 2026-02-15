"""
BM25 Retriever - LION
Busca baseada em termos usando algoritmo BM25
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np
from rank_bm25 import BM25Okapi
import re


@dataclass
class RetrievalResult:
    """Resultado de busca"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    rank: int


class BM25Retriever:
    """
    Retriever baseado em BM25 (Best Matching 25).
    
    BM25 é um algoritmo de ranking baseado em frequência de termos
    e comprimento de documentos. Complementa busca vetorial capturando
    matches exatos de termos.
    """
    
    def __init__(
        self,
        documents: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 5,
        tokenizer: str = "simple"
    ):
        """
        Inicializa BM25 retriever.
        
        Args:
            documents: Lista de docs com 'id', 'content', 'metadata'
            top_k: Número de documentos a retornar
            tokenizer: Tipo de tokenização ("simple" ou "legal")
        """
        self.top_k = top_k
        self.tokenizer_type = tokenizer
        
        self.documents = documents or []
        self.doc_ids = []
        self.doc_contents = []
        self.doc_metadatas = []
        self.bm25 = None
        
        if documents:
            self._index_documents(documents)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokeniza texto.
        
        Args:
            text: Texto para tokenizar
            
        Returns:
            Lista de tokens (lowercase, sem stopwords básicas)
        """
        # Lowercase
        text = text.lower()
        
        if self.tokenizer_type == "legal":
            # Tokenização especializada para textos legais
            # Preserva artigos, parágrafos, incisos
            tokens = re.findall(
                r'art\.?\s*\d+|§\s*\d+|inciso\s+[ivxlcdm]+|\b\w+\b',
                text
            )
        else:
            # Tokenização simples
            tokens = re.findall(r'\b\w+\b', text)
        
        # Remover stopwords básicas (português)
        stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
            'em', 'no', 'na', 'nos', 'nas', 'por', 'para', 'com', 'sem',
            'e', 'ou', 'que', 'se', 'é', 'são', 'foi', 'ser', 'ter'
        }
        
        tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
        
        return tokens
    
    def _index_documents(self, documents: List[Dict[str, Any]]):
        """
        Indexa documentos para BM25.
        
        Args:
            documents: Lista de dicts com 'id', 'content', 'metadata'
        """
        self.documents = documents
        self.doc_ids = [doc['id'] for doc in documents]
        self.doc_contents = [doc['content'] for doc in documents]
        self.doc_metadatas = [doc.get('metadata', {}) for doc in documents]
        
        # Tokenizar documentos
        tokenized_docs = [self._tokenize(content) for content in self.doc_contents]
        
        # Criar índice BM25
        self.bm25 = BM25Okapi(tokenized_docs)
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Adiciona novos documentos ao índice.
        
        Args:
            documents: Lista de dicts com 'id', 'content', 'metadata'
        """
        all_docs = self.documents + documents
        self._index_documents(all_docs)
    
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
            Lista de RetrievalResult ordenada por score BM25
        """
        if not self.bm25:
            return []
        
        k = top_k or self.top_k
        
        # 1. Tokenizar query
        query_tokens = self._tokenize(query)
        
        # 2. Calcular scores BM25
        scores = self.bm25.get_scores(query_tokens)
        
        # 3. Aplicar filtros (se fornecidos)
        if filters:
            filtered_indices = []
            for i, metadata in enumerate(self.doc_metadatas):
                match = all(
                    metadata.get(key) == value
                    for key, value in filters.items()
                )
                if match:
                    filtered_indices.append(i)
            
            # Zerar scores de docs que não passaram no filtro
            mask = np.ones_like(scores)
            mask[filtered_indices] = 0
            scores = scores * mask
        
        # 4. Pegar top-k
        top_indices = np.argsort(scores)[::-1][:k]
        
        # 5. Criar resultados
        results = []
        for rank, idx in enumerate(top_indices, 1):
            score = float(scores[idx])
            if score > 0:  # Apenas docs com score > 0
                results.append(RetrievalResult(
                    id=self.doc_ids[idx],
                    content=self.doc_contents[idx],
                    score=score,
                    metadata=self.doc_metadatas[idx],
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
        return [
            self.retrieve(query, top_k, filters)
            for query in queries
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do retriever.
        
        Returns:
            Dict com estatísticas
        """
        avg_doc_length = (
            sum(len(self._tokenize(doc)) for doc in self.doc_contents) / len(self.doc_contents)
            if self.doc_contents else 0
        )
        
        return {
            'retriever_type': 'bm25',
            'top_k': self.top_k,
            'tokenizer': self.tokenizer_type,
            'num_documents': len(self.documents),
            'avg_doc_length': avg_doc_length,
            'indexed': self.bm25 is not None
        }
    
    @classmethod
    def from_vector_store(
        cls,
        vector_store,
        top_k: int = 5,
        tokenizer: str = "legal"
    ) -> 'BM25Retriever':
        """
        Cria BM25Retriever a partir de um VectorStore.
        
        Args:
            vector_store: VectorStore com documentos
            top_k: Número de resultados
            tokenizer: Tipo de tokenização
            
        Returns:
            BM25Retriever com docs do vector store
        """
        # Pegar todos os documentos do vector store
        count = vector_store.count()
        
        if count == 0:
            return cls(top_k=top_k, tokenizer=tokenizer)
        
        # Pegar sample (ou todos se poucos docs)
        sample_size = min(count, 10000)  # Limitar para performance
        sample = vector_store.collection.peek(limit=sample_size)
        
        # Converter para formato esperado
        documents = []
        for doc_id, content, metadata in zip(
            sample['ids'],
            sample['documents'],
            sample['metadatas']
        ):
            documents.append({
                'id': doc_id,
                'content': content,
                'metadata': metadata
            })
        
        return cls(documents=documents, top_k=top_k, tokenizer=tokenizer)


def create_bm25_retriever(
    vector_store=None,
    top_k: Optional[int] = None,
    tokenizer: str = "legal"
) -> BM25Retriever:
    """
    Factory function para criar BM25 retriever.
    
    Args:
        vector_store: VectorStore para carregar documentos
        top_k: Número de documentos (usa .env TOP_K se None)
        tokenizer: Tipo de tokenização
        
    Returns:
        BM25Retriever configurado
    """
    import os
    
    k = top_k or int(os.getenv('TOP_K', '5'))
    
    if vector_store:
        return BM25Retriever.from_vector_store(vector_store, top_k=k, tokenizer=tokenizer)
    
    return BM25Retriever(top_k=k, tokenizer=tokenizer)


# Exemplo de uso
if __name__ == "__main__":
    # Criar retriever com documentos de exemplo
    docs = [
        {
            'id': 'doc1',
            'content': 'Art. 68. O contribuinte que perceber rendimentos do trabalho pode deduzir despesas escrituradas no livro-caixa.',
            'metadata': {'source': 'test'}
        },
        {
            'id': 'doc2',
            'content': '§ 2º As deduções glosadas por falta de comprovação não poderão ser restabelecidas.',
            'metadata': {'source': 'test'}
        },
        {
            'id': 'doc3',
            'content': 'CAPÍTULO III das deduções do imposto sobre a renda e das alíquotas aplicáveis.',
            'metadata': {'source': 'test'}
        }
    ]
    
    retriever = create_bm25_retriever(top_k=3)
    retriever.add_documents(docs)
    
    print("📊 BM25 Retriever Stats:")
    stats = retriever.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Busca de exemplo
    query = "deduções permitidas livro-caixa"
    print(f"\n🔍 Query: {query}")
    
    results = retriever.retrieve(query, top_k=3)
    
    print(f"\n📄 Resultados ({len(results)}):")
    for result in results:
        print(f"\n   [{result.rank}] Score: {result.score:.4f}")
        print(f"       ID: {result.id}")
        print(f"       {result.content[:100]}...")
