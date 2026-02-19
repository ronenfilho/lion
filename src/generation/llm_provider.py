"""
LLM Provider - LION
Interface abstrata para provedores de LLM
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class GenerationConfig:
    """Configuração de geração (agnóstica ao provedor)"""
    temperature: float = 0.2
    max_tokens: int = 800
    top_p: float = 0.95
    top_k: int = 40
    stop_sequences: Optional[List[str]] = None


@dataclass
class GenerationResult:
    """Resultado de geração (agnóstico ao provedor)"""
    text: str
    model: str
    provider: str  # 'gemini', 'openai', 'anthropic', etc.
    tokens_used: int
    finish_reason: str
    generation_time: float
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """
    Interface abstrata para provedores de LLM.
    
    Implementações concretas: GeminiProvider, OpenAIProvider, AnthropicProvider
    """
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        stream: bool = False
    ) -> GenerationResult:
        """
        Gera resposta para um prompt.
        
        Args:
            prompt: Texto do prompt
            system_instruction: Instrução de sistema (opcional)
            stream: Se True, retorna generator para streaming
            
        Returns:
            GenerationResult
        """
        pass
    
    @abstractmethod
    def generate_with_context(
        self,
        query: str,
        context_chunks: List[str],
        system_instruction: Optional[str] = None,
        max_context_length: int = 8000
    ) -> GenerationResult:
        """
        Gera resposta usando contexto RAG.
        
        Args:
            query: Pergunta do usuário
            context_chunks: Chunks recuperados
            system_instruction: Instrução de sistema (opcional)
            max_context_length: Limite de caracteres do contexto
            
        Returns:
            GenerationResult
        """
        pass
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None
    ) -> GenerationResult:
        """
        Conversação multi-turno.
        
        Args:
            messages: Lista de mensagens [{'role': 'user', 'content': '...'}]
            system_instruction: Instrução de sistema (opcional)
            
        Returns:
            GenerationResult
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Conta tokens no texto.
        
        Args:
            text: Texto para contar
            
        Returns:
            Número de tokens
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nome do modelo."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nome do provedor (gemini, openai, anthropic, etc.)."""
        pass
