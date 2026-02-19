"""
Embeddings Pipeline - LION
Gera embeddings para chunks usando Google Gemini Embedding (3072d)
"""

import os
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import json
import pickle

import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


@dataclass
class DocumentChunk:
    """Representa um chunk de documento (compatível com structural_chunker)"""
    chunk_id: str
    content: str
    source: str
    metadata: Dict[str, Any]
    
    def __len__(self):
        return len(self.content)


class EmbeddingsPipeline:
    """
    Pipeline para gerar embeddings de documentos.
    
    Usa Google Generative AI gemini-embedding-001 para gerar embeddings
    de 3072 dimensões com processamento em lote otimizado.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        dimension: Optional[int] = None,
        batch_size: int = 100,
        api_key: Optional[str] = None,
        rate_limit_delay: float = 0.1
    ):
        """
        Inicializa pipeline de embeddings.
        
        Args:
            model_name: Nome do modelo Google (usa EMBEDDING_MODEL do .env se None)
            dimension: Dimensão dos embeddings (usa EMBEDDING_DIMENSION do .env se None)
            batch_size: Tamanho do lote para processamento
            api_key: Chave API Google (usa GOOGLE_API_KEY se None)
            rate_limit_delay: Delay entre requests (segundos)
        """
        # Carregar configurações do .env se não fornecidas
        self.model_name = model_name or os.getenv('EMBEDDING_MODEL', 'models/gemini-embedding-001')
        self.dimension = dimension or int(os.getenv('EMBEDDING_DIMENSION', '3072'))
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        
        # Configurar API Google
        api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY não encontrada. "
                "Configure no .env ou passe como parâmetro."
            )
        
        genai.configure(api_key=api_key)
        
        # Validar modelo
        try:
            # Teste rápido de embedding
            result = genai.embed_content(
                model=self.model_name,
                content="teste",
                task_type="retrieval_document"
            )
            if len(result['embedding']) != self.dimension:
                raise ValueError(
                    f"Dimensão esperada: {self.dimension}, "
                    f"recebida: {len(result['embedding'])}"
                )
        except Exception as e:
            raise RuntimeError(f"Erro ao validar modelo {model_name}: {e}")
    
    def generate_embeddings(
        self,
        chunks: List[DocumentChunk],
        task_type: str = "retrieval_document",
        show_progress: bool = True
    ) -> List[np.ndarray]:
        """
        Gera embeddings para lista de chunks.
        
        Args:
            chunks: Lista de DocumentChunk
            task_type: Tipo de tarefa Google AI
                - "retrieval_document": Para indexação de documentos (padrão)
                - "retrieval_query": Para queries de busca
            show_progress: Mostrar barra de progresso
            
        Returns:
            Lista de arrays numpy com embeddings (768d)
        """
        embeddings = []
        
        # Processar em lotes
        iterator = range(0, len(chunks), self.batch_size)
        if show_progress:
            iterator = tqdm(
                iterator,
                desc="Gerando embeddings",
                unit="batch",
                total=(len(chunks) + self.batch_size - 1) // self.batch_size
            )
        
        for i in iterator:
            batch = chunks[i:i + self.batch_size]
            batch_texts = [chunk.content for chunk in batch]
            
            try:
                # Gerar embeddings do lote
                result = genai.embed_content(
                    model=self.model_name,
                    content=batch_texts,
                    task_type=task_type
                )
                
                # Converter para numpy arrays
                batch_embeddings = [
                    np.array(emb, dtype=np.float32)
                    for emb in result['embedding']
                ]
                embeddings.extend(batch_embeddings)
                
                # Rate limiting
                if i + self.batch_size < len(chunks):
                    time.sleep(self.rate_limit_delay)
                    
            except Exception as e:
                print(f"\n⚠️ Erro no lote {i//self.batch_size + 1}: {e}")
                # Em caso de erro, tentar chunks individuais
                for chunk in batch:
                    try:
                        result = genai.embed_content(
                            model=self.model_name,
                            content=chunk.content,
                            task_type=task_type
                        )
                        emb = np.array(result['embedding'], dtype=np.float32)
                        embeddings.append(emb)
                        time.sleep(self.rate_limit_delay * 2)
                    except Exception as e2:
                        print(f"⚠️ Erro no chunk {chunk.chunk_id}: {e2}")
                        # Embedding zero como fallback
                        embeddings.append(np.zeros(self.dimension, dtype=np.float32))
        
        return embeddings
    
    def save_embeddings(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[np.ndarray],
        output_path: str,
        format: str = "pickle"
    ):
        """
        Salva chunks e embeddings em arquivo.
        
        Args:
            chunks: Lista de chunks
            embeddings: Lista de embeddings
            output_path: Caminho para salvar
            format: Formato ("pickle" ou "json")
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) e embeddings ({len(embeddings)}) "
                "têm tamanhos diferentes"
            )
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Preparar dados
        data = {
            'chunks': [asdict(chunk) for chunk in chunks],
            'embeddings': [emb.tolist() for emb in embeddings],
            'metadata': {
                'model': self.model_name,
                'dimension': self.dimension,
                'total_chunks': len(chunks),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        if format == "pickle":
            with open(output_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        elif format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Formato inválido: {format}")
        
        print(f"✓ Salvo em: {output_path}")
    
    def load_embeddings(self, input_path: str) -> Dict[str, Any]:
        """
        Carrega chunks e embeddings de arquivo.
        
        Args:
            input_path: Caminho do arquivo
            
        Returns:
            Dict com 'chunks', 'embeddings' e 'metadata'
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
        
        if input_path.suffix == '.pkl':
            with open(input_path, 'rb') as f:
                data = pickle.load(f)
        elif input_path.suffix == '.json':
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Converter embeddings de volta para numpy
            data['embeddings'] = [
                np.array(emb, dtype=np.float32)
                for emb in data['embeddings']
            ]
        else:
            raise ValueError(f"Formato não suportado: {input_path.suffix}")
        
        # Reconstruir chunks
        chunks = [
            DocumentChunk(**chunk_dict)
            for chunk_dict in data['chunks']
        ]
        data['chunks'] = chunks
        
        return data
    
    def get_stats(self, embeddings: List[np.ndarray]) -> Dict[str, float]:
        """
        Calcula estatísticas dos embeddings.
        
        Args:
            embeddings: Lista de embeddings
            
        Returns:
            Dict com estatísticas (mean, std, norm, etc)
        """
        emb_matrix = np.array(embeddings)
        
        return {
            'count': len(embeddings),
            'dimension': emb_matrix.shape[1] if len(emb_matrix.shape) > 1 else 0,
            'mean': float(emb_matrix.mean()),
            'std': float(emb_matrix.std()),
            'min': float(emb_matrix.min()),
            'max': float(emb_matrix.max()),
            'norm_mean': float(np.linalg.norm(emb_matrix, axis=1).mean()),
            'norm_std': float(np.linalg.norm(emb_matrix, axis=1).std())
        }


def create_embeddings_pipeline(config: Optional[Dict[str, Any]] = None) -> EmbeddingsPipeline:
    """
    Factory function para criar pipeline de embeddings.
    
    Args:
        config: Configurações opcionais (usa .env e defaults se None)
        
    Returns:
        EmbeddingsPipeline configurado
    """
    if config is None:
        config = {}
    
    return EmbeddingsPipeline(
        model_name=config.get('model'),  # None = usar .env
        dimension=config.get('dimension'),  # None = usar .env
        batch_size=config.get('batch_size', 100),
        api_key=config.get('api_key'),
        rate_limit_delay=config.get('rate_limit_delay', 0.1)
    )


# Exemplo de uso
if __name__ == "__main__":
    from structural_chunker import StructuralChunker
    from text_cleaner import TextCleaner
    
    # 1. Criar chunks de exemplo
    chunker = StructuralChunker()
    text = "Exemplo de texto para chunking. " * 100
    chunks = chunker.chunk_text(text, source="teste")
    
    # 2. Gerar embeddings
    pipeline = create_embeddings_pipeline()
    embeddings = pipeline.generate_embeddings(chunks)
    
    # 3. Estatísticas
    stats = pipeline.get_stats(embeddings)
    print(f"\n📊 Estatísticas dos embeddings:")
    for key, value in stats.items():
        print(f"   {key}: {value:.4f}")
    
    # 4. Salvar
    pipeline.save_embeddings(
        chunks,
        embeddings,
        "data/embeddings/test_embeddings.pkl"
    )
