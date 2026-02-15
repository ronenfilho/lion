"""
LLM Client - LION
Interface para Google Gemini (Generative AI)
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


@dataclass
class GenerationConfig:
    """Configuração de geração"""
    temperature: float = 0.2
    max_tokens: int = 800
    top_p: float = 0.95
    top_k: int = 40


@dataclass
class GenerationResult:
    """Resultado de geração"""
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    generation_time: float


class LLMClient:
    """
    Cliente para interação com Google Gemini.
    
    Gerencia comunicação com a API do Gemini para geração de respostas
    em tarefas de RAG (Retrieval-Augmented Generation).
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        api_key: Optional[str] = None
    ):
        """
        Inicializa LLM client.
        
        Args:
            model_name: Nome do modelo (usa LLM_MODEL do .env se None)
            config: Configuração de geração
            api_key: Chave API (usa GOOGLE_API_KEY do .env se None)
        """
        self.model_name = model_name or os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')
        self.config = config or GenerationConfig(
            temperature=float(os.getenv('TEMPERATURE', '0.2')),
            max_tokens=int(os.getenv('MAX_TOKENS', '800')),
            top_p=0.95,
            top_k=40
        )
        
        # Configurar API
        api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada")
        
        genai.configure(api_key=api_key)
        
        # Inicializar modelo
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                'temperature': self.config.temperature,
                'max_output_tokens': self.config.max_tokens,
                'top_p': self.config.top_p,
                'top_k': self.config.top_k
            }
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
            GenerationResult com resposta e metadados
        """
        start_time = time.time()
        
        # Preparar mensagens
        if system_instruction:
            # Gemini aceita system instruction no construtor do modelo
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': self.config.temperature,
                    'max_output_tokens': self.config.max_tokens,
                    'top_p': self.config.top_p,
                    'top_k': self.config.top_k
                },
                system_instruction=system_instruction
            )
        else:
            model = self.model
        
        # Gerar resposta
        try:
            if stream:
                response = model.generate_content(prompt, stream=True)
                # Para streaming, retornar o generator
                return response
            else:
                response = model.generate_content(prompt)
                
                generation_time = time.time() - start_time
                
                # Extrair texto
                text = response.text if response.text else ""
                
                # Contar tokens (aproximado)
                tokens_used = len(text.split())  # Aproximação simples
                
                # Finish reason
                finish_reason = (
                    response.candidates[0].finish_reason.name
                    if response.candidates else "UNKNOWN"
                )
                
                return GenerationResult(
                    text=text,
                    model=self.model_name,
                    tokens_used=tokens_used,
                    finish_reason=finish_reason,
                    generation_time=generation_time
                )
        
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar resposta: {e}")
    
    def generate_with_context(
        self,
        query: str,
        context_chunks: List[str],
        system_instruction: Optional[str] = None,
        max_context_length: int = 8000
    ) -> GenerationResult:
        """
        Gera resposta usando chunks de contexto (RAG).
        
        Args:
            query: Pergunta do usuário
            context_chunks: Lista de chunks relevantes
            system_instruction: Instrução de sistema
            max_context_length: Tamanho máximo do contexto (chars)
            
        Returns:
            GenerationResult com resposta
        """
        # Construir contexto
        context = self._build_context(context_chunks, max_context_length)
        
        # Construir prompt RAG
        prompt = f"""Contexto:
{context}

Pergunta: {query}

Resposta:"""
        
        return self.generate(prompt, system_instruction)
    
    def _build_context(
        self,
        chunks: List[str],
        max_length: int
    ) -> str:
        """
        Constrói contexto a partir de chunks.
        
        Args:
            chunks: Lista de chunks
            max_length: Tamanho máximo (caracteres)
            
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
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None
    ) -> GenerationResult:
        """
        Chat multi-turno.
        
        Args:
            messages: Lista de dicts com 'role' e 'content'
                     role: 'user' ou 'model'
            system_instruction: Instrução de sistema
            
        Returns:
            GenerationResult com resposta
        """
        start_time = time.time()
        
        # Preparar modelo
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': self.config.temperature,
                    'max_output_tokens': self.config.max_tokens,
                    'top_p': self.config.top_p,
                    'top_k': self.config.top_k
                },
                system_instruction=system_instruction
            )
        else:
            model = self.model
        
        # Iniciar chat
        chat = model.start_chat(history=[])
        
        # Adicionar mensagens do histórico (exceto a última)
        for msg in messages[:-1]:
            if msg['role'] == 'user':
                chat.send_message(msg['content'])
        
        # Enviar última mensagem e obter resposta
        last_message = messages[-1]['content']
        response = chat.send_message(last_message)
        
        generation_time = time.time() - start_time
        
        return GenerationResult(
            text=response.text,
            model=self.model_name,
            tokens_used=len(response.text.split()),
            finish_reason=(
                response.candidates[0].finish_reason.name
                if response.candidates else "UNKNOWN"
            ),
            generation_time=generation_time
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Conta tokens aproximados.
        
        Args:
            text: Texto para contar
            
        Returns:
            Número aproximado de tokens
        """
        # Gemini tem método count_tokens, mas vamos usar aproximação simples
        return len(text.split())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cliente.
        
        Returns:
            Dict com configurações
        """
        return {
            'model': self.model_name,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            'top_p': self.config.top_p,
            'top_k': self.config.top_k
        }


def create_llm_client(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> LLMClient:
    """
    Factory function para criar LLM client.
    
    Args:
        model_name: Nome do modelo (usa .env LLM_MODEL se None)
        temperature: Temperatura (usa .env TEMPERATURE se None)
        max_tokens: Max tokens (usa .env MAX_TOKENS se None)
        
    Returns:
        LLMClient configurado
    """
    config = GenerationConfig(
        temperature=temperature or float(os.getenv('TEMPERATURE', '0.2')),
        max_tokens=max_tokens or int(os.getenv('MAX_TOKENS', '800'))
    )
    
    return LLMClient(model_name=model_name, config=config)


# Exemplo de uso
if __name__ == "__main__":
    # Criar client
    client = create_llm_client()
    
    print("📊 LLM Client Stats:")
    stats = client.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Teste simples
    print("\n🤖 Teste de geração:")
    query = "O que são deduções no IRPF?"
    
    result = client.generate(
        prompt=query,
        system_instruction="Você é um assistente especializado em Imposto de Renda."
    )
    
    print(f"\n   Query: {query}")
    print(f"\n   Resposta ({result.tokens_used} tokens, {result.generation_time:.2f}s):")
    print(f"   {result.text[:200]}...")
    print(f"\n   Finish reason: {result.finish_reason}")
