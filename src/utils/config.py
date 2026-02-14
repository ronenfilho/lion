"""
Módulo de Configuração - LION
Carrega e valida configurações do projeto com suporte a variáveis de ambiente
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


class EmbeddingsConfig(BaseModel):
    """Configuração de embeddings"""
    model: str = "models/text-embedding-004"
    dimension: int = 768
    batch_size: int = 100
    normalize: bool = True


class VectorStoreConfig(BaseModel):
    """Configuração do vector store"""
    type: str = "chromadb"
    persist_directory: str = "./data/embeddings/chroma_db"
    collection_name: str = "irpf_2025"
    distance_metric: str = "cosine"


class RetrievalConfig(BaseModel):
    """Configuração de retrieval"""
    strategy: str = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    hybrid_alpha: float = Field(default=0.7, ge=0.0, le=1.0)
    use_reranking: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_top_k: int = 15


class ChunkingConfig(BaseModel):
    """Configuração de chunking"""
    strategy: str = "structural"
    max_chunk_size: int = 800
    overlap: int = 0
    add_context_window: bool = True


class GenerationConfig(BaseModel):
    """Configuração de geração"""
    model: str = "gemini-2.0-flash-exp"
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=800, ge=100, le=4000)
    presence_penalty: float = 0.1
    frequency_penalty: float = 0.1
    stop_sequences: list[str] = ["###", "Contexto:"]


class GuardrailsConfig(BaseModel):
    """Configuração de guardrails"""
    input_validation: bool = True
    output_validation: bool = True
    pii_detection: bool = True
    prompt_injection_detection: bool = True
    min_query_length: int = 10
    max_query_length: int = 500
    min_response_length: int = 50


class CacheConfig(BaseModel):
    """Configuração de cache"""
    enabled: bool = True
    type: str = "semantic"
    similarity_threshold: float = 0.95
    ttl: int = 3600
    max_size: int = 1000


class MonitoringConfig(BaseModel):
    """Configuração de monitoramento"""
    enabled: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    metrics_enabled: bool = True
    tracing_enabled: bool = False


class Config(BaseModel):
    """Configuração principal do projeto"""
    embeddings: EmbeddingsConfig
    vector_store: VectorStoreConfig
    retrieval: RetrievalConfig
    chunking: ChunkingConfig
    generation: GenerationConfig
    guardrails: GuardrailsConfig
    cache: CacheConfig
    monitoring: MonitoringConfig


def load_config(env: str = "default") -> Config:
    """
    Carrega configuração do ambiente especificado
    Sobrescreve valores do YAML com variáveis de ambiente (.env)
    
    Args:
        env: Ambiente (default, development, production)
        
    Returns:
        Config: Objeto de configuração validado
    """
    config_dir = Path(__file__).parent.parent.parent / "config"
    
    # Carregar configuração base
    default_path = config_dir / "default.yaml"
    with open(default_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Se não for default, fazer merge com configuração específica
    if env != "default":
        env_path = config_dir / f"{env}.yaml"
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_data = yaml.safe_load(f)
                # Merge recursivo
                config_data = deep_merge(config_data, env_data)
    
    # Sobrescrever com variáveis de ambiente (.env tem prioridade)
    config_data = apply_env_overrides(config_data)
    
    # Validar e retornar
    return Config(**config_data)


def deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Faz merge recursivo de dicionários
    
    Args:
        base: Dicionário base
        override: Dicionário com valores para sobrescrever
        
    Returns:
        Dict: Dicionário merged
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def apply_env_overrides(config_data: Dict) -> Dict:
    """
    Sobrescreve configurações do YAML com variáveis de ambiente
    Variáveis de ambiente têm prioridade máxima
    
    Args:
        config_data: Dados de configuração do YAML
        
    Returns:
        Dict: Configuração com overrides aplicados
    """
    # Embeddings
    if os.getenv('EMBEDDING_MODEL'):
        config_data['embeddings']['model'] = os.getenv('EMBEDDING_MODEL')
    if os.getenv('EMBEDDING_DIMENSION'):
        config_data['embeddings']['dimension'] = int(os.getenv('EMBEDDING_DIMENSION'))
    
    # Vector Store
    if os.getenv('CHROMA_PERSIST_DIR'):
        config_data['vector_store']['persist_directory'] = os.getenv('CHROMA_PERSIST_DIR')
    
    # Retrieval
    if os.getenv('TOP_K'):
        config_data['retrieval']['top_k'] = int(os.getenv('TOP_K'))
    if os.getenv('SIMILARITY_THRESHOLD'):
        config_data['retrieval']['similarity_threshold'] = float(os.getenv('SIMILARITY_THRESHOLD'))
    if os.getenv('USE_RERANKING'):
        config_data['retrieval']['use_reranking'] = os.getenv('USE_RERANKING').lower() == 'true'
    if os.getenv('HYBRID_ALPHA'):
        config_data['retrieval']['hybrid_alpha'] = float(os.getenv('HYBRID_ALPHA'))
    
    # Generation
    if os.getenv('LLM_MODEL'):
        config_data['generation']['model'] = os.getenv('LLM_MODEL')
    if os.getenv('TEMPERATURE'):
        config_data['generation']['temperature'] = float(os.getenv('TEMPERATURE'))
    if os.getenv('MAX_TOKENS'):
        config_data['generation']['max_tokens'] = int(os.getenv('MAX_TOKENS'))
    
    # Monitoring
    if os.getenv('LOG_LEVEL'):
        config_data['monitoring']['log_level'] = os.getenv('LOG_LEVEL')
    if os.getenv('ENABLE_METRICS'):
        config_data['monitoring']['metrics_enabled'] = os.getenv('ENABLE_METRICS').lower() == 'true'
    
    # Cache
    if os.getenv('ENABLE_CACHE'):
        config_data['cache']['enabled'] = os.getenv('ENABLE_CACHE').lower() == 'true'
    if os.getenv('CACHE_TTL'):
        config_data['cache']['ttl'] = int(os.getenv('CACHE_TTL'))
    if os.getenv('SEMANTIC_CACHE_THRESHOLD'):
        config_data['cache']['similarity_threshold'] = float(os.getenv('SEMANTIC_CACHE_THRESHOLD'))
    
    return config_data


# Instância global de configuração
_config: Config = None


def get_config(env: str = None) -> Config:
    """
    Retorna a configuração global (singleton)
    
    Args:
        env: Ambiente (default, development, production)
        
    Returns:
        Config: Objeto de configuração
    """
    global _config
    
    if _config is None:
        # Determinar ambiente
        if env is None:
            env = os.getenv("LION_ENV", "default")
        
        _config = load_config(env)
    
    return _config


if __name__ == "__main__":
    # Teste de configuração
    config = get_config()
    print("=" * 60)
    print("📋 LION - Configuração Carregada")
    print("=" * 60)
    print(f"🤖 Modelo LLM: {config.generation.model}")
    print(f"📊 Modelo Embedding: {config.embeddings.model}")
    print(f"🔢 Dimensão: {config.embeddings.dimension}")
    print(f"🔍 Top-K: {config.retrieval.top_k}")
    print(f"🎯 Estratégia: {config.retrieval.strategy}")
    print(f"💾 Cache: {'✓' if config.cache.enabled else '✗'}")
    print(f"📈 Métricas: {'✓' if config.monitoring.metrics_enabled else '✗'}")
    print("=" * 60)
