"""
Gemini Provider - LION
Implementação do provedor Google Gemini
"""

import os
import time
from typing import List, Dict, Optional

import google.generativeai as genai
from dotenv import load_dotenv

from ..llm_provider import LLMProvider, GenerationConfig, GenerationResult

load_dotenv()


class GeminiProvider(LLMProvider):
    """
    Provedor para Google Gemini.
    
    Implementa interface LLMProvider para Google Gemini API.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        api_key: Optional[str] = None
    ):
        """
        Inicializa Gemini provider.
        
        Args:
            model_name: Nome do modelo (default: gemini-2.0-flash-exp)
            config: Configuração de geração
            api_key: Chave API (usa GEMINI_API_KEY do .env se None)
        """
        self._model_name = model_name or os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')
        self.config = config or GenerationConfig(
            temperature=float(os.getenv('TEMPERATURE', '0.2')),
            max_tokens=int(os.getenv('MAX_TOKENS', '800')),
            top_p=0.95,
            top_k=40
        )
        
        # Configurar API
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")
        
        genai.configure(api_key=api_key)
        
        # Inicializar modelo base
        self.model = self._create_model()
    
    def _create_model(self, system_instruction: Optional[str] = None):
        """Cria instância do modelo Gemini."""
        return genai.GenerativeModel(
            model_name=self._model_name,
            generation_config={
                'temperature': self.config.temperature,
                'max_output_tokens': self.config.max_tokens,
                'top_p': self.config.top_p,
                'top_k': self.config.top_k
            },
            system_instruction=system_instruction
        )
    
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
        start_time = time.time()
        
        # Usar modelo com system instruction se fornecida
        model = self._create_model(system_instruction) if system_instruction else self.model
        
        try:
            if stream:
                # Streaming mode
                response = model.generate_content(prompt, stream=True)
                return response  # Retorna generator
            else:
                # Modo síncrono
                response = model.generate_content(prompt)
                
                generation_time = time.time() - start_time
                
                # Extrair dados
                text = response.text if hasattr(response, 'text') else ""
                tokens_used = self.count_tokens(text)
                finish_reason = (
                    response.candidates[0].finish_reason.name
                    if response.candidates else "UNKNOWN"
                )
                
                return GenerationResult(
                    text=text,
                    model=self._model_name,
                    provider='gemini',
                    tokens_used=tokens_used,
                    finish_reason=finish_reason,
                    generation_time=generation_time,
                    metadata={'response_obj': response}
                )
        
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar resposta com Gemini: {e}")
    
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
        # Construir contexto
        context = self._build_context(context_chunks, max_context_length)
        
        # Montar prompt RAG
        prompt = f"""Contexto:
{context}

Pergunta: {query}

Resposta:"""
        
        return self.generate(prompt, system_instruction)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None
    ) -> GenerationResult:
        """
        Conversação multi-turno.
        
        Args:
            messages: Lista de mensagens [{'role': 'user/assistant', 'content': '...'}]
            system_instruction: Instrução de sistema (opcional)
            
        Returns:
            GenerationResult
        """
        start_time = time.time()
        
        # Criar modelo com system instruction
        model = self._create_model(system_instruction) if system_instruction else self.model
        
        try:
            # Iniciar chat
            chat = model.start_chat(history=[])
            
            # Adicionar mensagens anteriores ao histórico
            for msg in messages[:-1]:  # Todas exceto a última
                role = 'user' if msg['role'] == 'user' else 'model'
                chat.history.append({
                    'role': role,
                    'parts': [msg['content']]
                })
            
            # Enviar última mensagem
            last_message = messages[-1]
            response = chat.send_message(last_message['content'])
            
            generation_time = time.time() - start_time
            
            # Extrair resposta
            text = response.text if hasattr(response, 'text') else ""
            tokens_used = self.count_tokens(text)
            finish_reason = (
                response.candidates[0].finish_reason.name
                if response.candidates else "UNKNOWN"
            )
            
            return GenerationResult(
                text=text,
                model=self._model_name,
                provider='gemini',
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                generation_time=generation_time,
                metadata={'chat_obj': chat}
            )
        
        except Exception as e:
            raise RuntimeError(f"Erro no chat com Gemini: {e}")
    
    def count_tokens(self, text: str) -> int:
        """
        Conta tokens (aproximado para Gemini).
        
        Args:
            text: Texto para contar
            
        Returns:
            Número aproximado de tokens
        """
        # Aproximação: ~4 caracteres por token em média
        # Para contagem exata, usar model.count_tokens()
        return len(text) // 4
    
    def _build_context(self, chunks: List[str], max_length: int) -> str:
        """
        Constrói contexto a partir dos chunks.
        
        Args:
            chunks: Lista de chunks de texto
            max_length: Tamanho máximo do contexto em caracteres
            
        Returns:
            Contexto formatado
        """
        context_parts = []
        current_length = 0
        
        for i, chunk in enumerate(chunks, 1):
            chunk_text = f"[Trecho {i}]\n{chunk}\n"
            chunk_length = len(chunk_text)
            
            if current_length + chunk_length > max_length:
                break
            
            context_parts.append(chunk_text)
            current_length += chunk_length
        
        return "\n".join(context_parts)
    
    @property
    def model_name(self) -> str:
        """Nome do modelo."""
        return self._model_name
    
    @property
    def provider_name(self) -> str:
        """Nome do provedor."""
        return 'gemini'


def create_gemini_provider(
    model_name: Optional[str] = None,
    config: Optional[GenerationConfig] = None
) -> GeminiProvider:
    """
    Factory function para criar GeminiProvider.
    
    Args:
        model_name: Nome do modelo (opcional)
        config: Configuração de geração (opcional)
        
    Returns:
        GeminiProvider configurado
    """
    return GeminiProvider(model_name=model_name, config=config)
