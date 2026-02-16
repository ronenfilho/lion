"""
Groq LLM Client - LION
Interface para Groq API (modelos rápidos de inferência)
"""

import os
from typing import Optional
from dataclasses import dataclass
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


@dataclass
class GroqGenerationResult:
    """Resultado de geração compatível com GenerationResult."""
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    generation_time: float


class GroqLLMClient:
    """
    Cliente para interação com Groq API.
    
    Suporta modelos como:
    - llama-3.1-8b-instant (rápido, 8B parâmetros)
    - llama-3.1-70b-versatile (poderoso, 70B parâmetros)
    - mixtral-8x7b-32768 (longo contexto)
    """
    
    def __init__(
        self,
        model_name: str = "llama-3.1-8b-instant",
        api_key: Optional[str] = None
    ):
        """
        Inicializa cliente Groq.
        
        Args:
            model_name: Nome do modelo Groq
            api_key: Chave API (ou via GROQ_API_KEY env var)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY não encontrada. "
                "Configure via .env ou parâmetro api_key"
            )
        
        self.client = Groq(api_key=self.api_key)
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        **kwargs
    ) -> GroqGenerationResult:
        """
        Gera resposta usando Groq API.
        
        Args:
            prompt: Prompt de entrada
            max_tokens: Máximo de tokens a gerar
            temperature: Temperatura de amostragem (0-2)
            **kwargs: Parâmetros adicionais
        
        Returns:
            GroqGenerationResult com texto gerado e metadados
        """
        start_time = time.time()
        
        try:
            # Criar mensagens no formato Chat
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Chamar API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            generation_time = time.time() - start_time
            
            # Extrair resultado
            text = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Tokens usados
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return GroqGenerationResult(
                text=text.strip(),
                model=self.model_name,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                generation_time=generation_time
            )
        
        except Exception as e:
            raise RuntimeError(f"Erro na geração Groq: {e}")
    
    def __repr__(self) -> str:
        return f"GroqLLMClient(model={self.model_name})"


def create_groq_client(
    model_name: str = "llama-3.1-8b-instant"
) -> GroqLLMClient:
    """
    Cria cliente Groq.
    
    Args:
        model_name: Nome do modelo (padrão: llama-3.1-8b-instant)
    
    Returns:
        Instância de GroqLLMClient
    """
    return GroqLLMClient(model_name=model_name)
