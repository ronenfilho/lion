"""
Vector Store - LION
Gerencia armazenamento e busca de embeddings usando ChromaDB
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from datetime import datetime

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class VectorStore:
    """
    Abstração para vector store usando ChromaDB.
    
    Gerencia coleções de embeddings com metadata, permitindo
    busca por similaridade e filtragem.
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/embeddings/chroma_db",
        collection_name: str = "irpf_2025",
        distance_metric: str = "cosine"
    ):
        """
        Inicializa vector store com ChromaDB.
        
        Args:
            persist_directory: Diretório para persistência
            collection_name: Nome da coleção
            distance_metric: Métrica de distância ("cosine", "l2", "ip")
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        
        # Criar diretório se não existir
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Inicializar cliente ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Obter ou criar coleção
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✓ Coleção '{collection_name}' carregada ({self.collection.count()} documentos)")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": distance_metric}
            )
            print(f"✓ Coleção '{collection_name}' criada")
    
    def add_documents(
        self,
        ids: List[str],
        embeddings: List[np.ndarray],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Adiciona documentos com embeddings à coleção.
        
        Args:
            ids: IDs únicos dos documentos
            embeddings: Lista de embeddings (numpy arrays)
            documents: Textos dos documentos
            metadatas: Metadados opcionais (source, chunk_id, etc)
        """
        if len(ids) != len(embeddings) != len(documents):
            raise ValueError(
                f"Tamanhos incompatíveis: ids={len(ids)}, "
                f"embeddings={len(embeddings)}, documents={len(documents)}"
            )
        
        # Converter embeddings para lista de floats
        embeddings_list = [emb.tolist() if isinstance(emb, np.ndarray) else emb 
                          for emb in embeddings]
        
        # Adicionar timestamp aos metadados
        if metadatas is None:
            metadatas = [{}] * len(ids)
        
        for metadata in metadatas:
            if 'indexed_at' not in metadata:
                metadata['indexed_at'] = datetime.now().isoformat()
        
        # Adicionar à coleção
        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✓ Adicionados {len(ids)} documentos à coleção '{self.collection_name}'")
    
    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, str]] = None
    ) -> Dict[str, List]:
        """
        Busca documentos similares.
        
        Args:
            query_embedding: Embedding da query
            n_results: Número de resultados
            where: Filtros de metadata (ex: {"source": "D9580"})
            where_document: Filtros no conteúdo (ex: {"$contains": "artigo"})
            
        Returns:
            Dict com 'ids', 'documents', 'metadatas', 'distances'
        """
        # Converter embedding para lista
        query_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
        
        results = self.collection.query(
            query_embeddings=[query_list],
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        
        # Desempacotar resultados (query retorna listas aninhadas)
        return {
            'ids': results['ids'][0] if results['ids'] else [],
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else []
        }
    
    def search_batch(
        self,
        query_embeddings: List[np.ndarray],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, List]]:
        """
        Busca em lote para múltiplas queries.
        
        Args:
            query_embeddings: Lista de embeddings de queries
            n_results: Número de resultados por query
            where: Filtros de metadata
            
        Returns:
            Lista de dicts com resultados para cada query
        """
        # Converter embeddings para listas
        query_lists = [emb.tolist() if isinstance(emb, np.ndarray) else emb 
                      for emb in query_embeddings]
        
        results = self.collection.query(
            query_embeddings=query_lists,
            n_results=n_results,
            where=where
        )
        
        # Formatar resultados
        batch_results = []
        for i in range(len(query_embeddings)):
            batch_results.append({
                'ids': results['ids'][i],
                'documents': results['documents'][i],
                'metadatas': results['metadatas'][i],
                'distances': results['distances'][i]
            })
        
        return batch_results
    
    def delete(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None):
        """
        Remove documentos da coleção.
        
        Args:
            ids: IDs específicos para remover
            where: Filtro de metadata para remoção em lote
        """
        if ids:
            self.collection.delete(ids=ids)
            print(f"✓ Removidos {len(ids)} documentos")
        elif where:
            self.collection.delete(where=where)
            print(f"✓ Removidos documentos com filtro: {where}")
        else:
            raise ValueError("Forneça 'ids' ou 'where' para deleção")
    
    def update(
        self,
        ids: List[str],
        embeddings: Optional[List[np.ndarray]] = None,
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Atualiza documentos existentes.
        
        Args:
            ids: IDs dos documentos
            embeddings: Novos embeddings (opcional)
            documents: Novos textos (opcional)
            metadatas: Novos metadados (opcional)
        """
        update_dict = {'ids': ids}
        
        if embeddings:
            update_dict['embeddings'] = [
                emb.tolist() if isinstance(emb, np.ndarray) else emb 
                for emb in embeddings
            ]
        if documents:
            update_dict['documents'] = documents
        if metadatas:
            # Adicionar timestamp de atualização
            for metadata in metadatas:
                metadata['updated_at'] = datetime.now().isoformat()
            update_dict['metadatas'] = metadatas
        
        self.collection.update(**update_dict)
        print(f"✓ Atualizados {len(ids)} documentos")
    
    def get_by_ids(self, ids: List[str]) -> Dict[str, List]:
        """
        Recupera documentos por IDs.
        
        Args:
            ids: Lista de IDs
            
        Returns:
            Dict com 'ids', 'documents', 'metadatas', 'embeddings'
        """
        return self.collection.get(ids=ids, include=['documents', 'metadatas', 'embeddings'])
    
    def count(self) -> int:
        """Retorna número de documentos na coleção."""
        return self.collection.count()
    
    def reset(self):
        """Remove todos os documentos da coleção."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": self.distance_metric}
        )
        print(f"✓ Coleção '{self.collection_name}' resetada")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da coleção.
        
        Returns:
            Dict com estatísticas (count, metadata_keys, etc)
        """
        count = self.count()
        
        if count == 0:
            return {
                'count': 0,
                'collection_name': self.collection_name,
                'persist_directory': str(self.persist_directory)
            }
        
        # Pegar amostra para análise
        sample = self.collection.peek(limit=min(100, count))
        
        # Analisar metadados
        metadata_keys = set()
        if sample['metadatas']:
            for metadata in sample['metadatas']:
                metadata_keys.update(metadata.keys())
        
        # Analisar tamanhos de documentos
        doc_lengths = [len(doc) for doc in sample['documents']] if sample['documents'] else []
        
        return {
            'count': count,
            'collection_name': self.collection_name,
            'persist_directory': str(self.persist_directory),
            'distance_metric': self.distance_metric,
            'metadata_keys': list(metadata_keys),
            'avg_doc_length': sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0,
            'sample_size': len(sample['ids']) if sample['ids'] else 0
        }


def create_vector_store(
    persist_directory: Optional[str] = None,
    collection_name: Optional[str] = None
) -> VectorStore:
    """
    Factory function para criar vector store.
    
    Args:
        persist_directory: Diretório (usa .env se None)
        collection_name: Nome da coleção (usa padrão se None)
        
    Returns:
        VectorStore configurado
    """
    persist_dir = persist_directory or os.getenv(
        'CHROMA_PERSIST_DIR', 
        './data/embeddings/chroma_db'
    )
    collection = collection_name or os.getenv(
        'CHROMA_COLLECTION',
        'irpf_2025'
    )
    
    return VectorStore(
        persist_directory=persist_dir,
        collection_name=collection
    )


# Exemplo de uso
if __name__ == "__main__":
    # Criar vector store
    store = create_vector_store()
    
    # Exemplo de adição
    test_ids = ["doc1", "doc2", "doc3"]
    test_embeddings = [np.random.rand(3072) for _ in range(3)]
    test_documents = [
        "Artigo 1º da Lei do Imposto de Renda",
        "Seção II sobre deduções permitidas",
        "Capítulo III das alíquotas aplicáveis"
    ]
    test_metadatas = [
        {"source": "test", "type": "artigo"},
        {"source": "test", "type": "secao"},
        {"source": "test", "type": "capitulo"}
    ]
    
    store.add_documents(test_ids, test_embeddings, test_documents, test_metadatas)
    
    # Busca
    query_emb = np.random.rand(3072)
    results = store.search(query_emb, n_results=2)
    
    print(f"\n📊 Estatísticas: {store.get_stats()}")
    print(f"\n🔍 Resultados da busca:")
    for i, (doc, dist) in enumerate(zip(results['documents'], results['distances']), 1):
        print(f"   {i}. {doc[:60]}... (dist={dist:.4f})")
