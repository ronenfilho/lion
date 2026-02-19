"""
LLM Factory - LION
Factory para criar provedores de LLM baseado em configuração
"""

import os
from typing import Optional
from dotenv import load_dotenv

from .llm_provider import LLMProvider, GenerationConfig
from .providers.gemini_provider import GeminiProvider

load_dotenv()


class LLMFactory:
    """
    Factory para criar provedores de LLM.
    
    Suporta:
    - Google Gemini
    - OpenAI (futuro)
    - Anthropic Claude (futuro)
    - Outros (futuro)
    """
    
    SUPPORTED_PROVIDERS = {
        'gemini': GeminiProvider,
        # 'openai': OpenAIProvider,  # Implementar depois
        # 'anthropic': AnthropicProvider,  # Implementar depois
    }
    
    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> LLMProvider:
        """
        Cria provedor de LLM.
        
        Args:
            provider: Nome do provedor ('gemini', 'openai', 'anthropic')
                     Se None, usa LLM_PROVIDER do .env (default: 'gemini')
            model_name: Nome do modelo (opcional, usa default do provedor)
            config: Configuração de geração (opcional)
            
        Returns:
            Instância de LLMProvider
            
        Raises:
            ValueError: Se provedor não for suportado
            
        Examples:
            >>> # Usar provedor padrão (gemini)
            >>> llm = LLMFactory.create()
            
            >>> # Especificar provedor
            >>> llm = LLMFactory.create(provider='gemini', model_name='gemini-2.0-flash-exp')
            
            >>> # Com configuração customizada
            >>> config = GenerationConfig(temperature=0.7, max_tokens=1000)
            >>> llm = LLMFactory.create(config=config)
        """
        # Determinar provedor
        provider = provider or os.getenv('LLM_PROVIDER', 'gemini')
        provider = provider.lower()
        
        # Validar provedor
        if provider not in cls.SUPPORTED_PROVIDERS:
            supported = ', '.join(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(
                f"Provedor '{provider}' não suportado. "
                f"Provedores disponíveis: {supported}"
            )
        
        # Criar instância
        provider_class = cls.SUPPORTED_PROVIDERS[provider]
        return provider_class(model_name=model_name, config=config)
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """
        Lista provedores suportados.
        
        Returns:
            Lista de nomes de provedores
        """
        return list(cls.SUPPORTED_PROVIDERS.keys())


def create_llm_client(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    config: Optional[GenerationConfig] = None
) -> LLMProvider:
    """
    Função helper para criar cliente LLM.
    
    Args:
        provider: Nome do provedor (gemini, openai, etc.)
        model_name: Nome do modelo
        config: Configuração de geração
        
    Returns:
        LLMProvider configurado
        
    Examples:
        >>> # Modo mais simples - usa configuração do .env
        >>> llm = create_llm_client()
        
        >>> # Com provedor específico
        >>> llm = create_llm_client(provider='gemini')
        
        >>> # Configuração customizada
        >>> config = GenerationConfig(temperature=0.1, max_tokens=500)
        >>> llm = create_llm_client(config=config)
    """
    return LLMFactory.create(provider=provider, model_name=model_name, config=config)
