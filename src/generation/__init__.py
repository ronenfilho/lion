"""
Generation Module - LION
Módulo de geração de respostas com LLMs
"""

from .llm_provider import LLMProvider, GenerationConfig, GenerationResult
from .llm_factory import LLMFactory, create_llm_client
from .prompts import PromptManager, create_prompt_manager
from .output_parser import OutputParser, ParsedResponse, create_output_parser

__all__ = [
    # Provider abstrato
    'LLMProvider',
    'GenerationConfig',
    'GenerationResult',
    
    # Factory
    'LLMFactory',
    'create_llm_client',
    
    # Prompts
    'PromptManager',
    'create_prompt_manager',
    
    # Parser
    'OutputParser',
    'ParsedResponse',
    'create_output_parser',
]
