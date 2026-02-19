"""
Cliente para modelos de linguagem locais quantizados.

Suporta:
- Phi-2 (2.7B quantizado para Q4 ~1.5GB)
- TinyLlama (1.1B ~700MB)
- Qwen2-0.5B (500M ~300MB)
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)

logger = logging.getLogger(__name__)


@dataclass
class LocalGenerationResult:
    """Resultado de geração compatível com GenerationResult do LLMClient."""
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    generation_time: float


class LocalLLMClient:
    """Cliente para modelos locais quantizados."""
    
    # Mapeamento de nomes para modelos do Hugging Face
    MODEL_MAP = {
        'phi-2': 'microsoft/phi-2',
        'tinyllama': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
        'qwen2-0.5b': 'Qwen/Qwen2-0.5B-Instruct'
    }
    
    def __init__(self, model_name: str, quantize: bool = True):
        """
        Inicializa cliente de modelo local.
        
        Args:
            model_name: Nome do modelo (phi-2, tinyllama, qwen2-0.5b)
            quantize: Se True, usa quantização 4-bit
        """
        self.model_name = model_name
        self.quantize = quantize
        
        if model_name not in self.MODEL_MAP:
            raise ValueError(
                f"Modelo '{model_name}' não suportado. "
                f"Opções: {list(self.MODEL_MAP.keys())}"
            )
        
        self.hf_model_id = self.MODEL_MAP[model_name]
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._load_model()
    
    def _load_model(self):
        """Carrega modelo e tokenizer."""
        logger.info(f"Carregando modelo {self.hf_model_id}...")
        start_time = time.time()
        
        try:
            # Verificar disponibilidade de CUDA
            has_cuda = torch.cuda.is_available()
            
            if not has_cuda:
                logger.warning("CUDA não disponível. Usando CPU (mais lento).")
                # Desabilitar quantização em CPU
                if self.quantize:
                    logger.warning("Quantização 4-bit requer CUDA. Carregando modelo em FP32.")
                    self.quantize = False
            
            # Configurar device e dtype
            if has_cuda:
                model_kwargs = {
                    "device_map": "auto",
                    "torch_dtype": torch.float16,
                    "trust_remote_code": True
                }
                
                if self.quantize:
                    # Configuração 4-bit (apenas com CUDA)
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    model_kwargs["quantization_config"] = quantization_config
                    logger.info("Usando quantização 4-bit")
            else:
                # CPU: usar FP32 ou FP16 sem quantização
                model_kwargs = {
                    "torch_dtype": torch.float32,
                    "trust_remote_code": True,
                    "low_cpu_mem_usage": True
                }
                logger.info("Usando CPU com FP32")
            
            # Carregar tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.hf_model_id,
                trust_remote_code=True
            )
            
            # Adicionar pad_token se não existir
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Carregar modelo
            self.model = AutoModelForCausalLM.from_pretrained(
                self.hf_model_id,
                **model_kwargs
            )
            
            # Mover para device apropriado se CPU
            if not has_cuda:
                self.model = self.model.to('cpu')
            
            # Criar pipeline para geração
            device = 0 if has_cuda else -1  # 0 = GPU, -1 = CPU
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.1,
                device=device
            )
            
            load_time = time.time() - start_time
            logger.info(f"Modelo carregado em {load_time:.2f}s")
            
            # Log de uso de memória
            if has_cuda:
                mem_allocated = torch.cuda.memory_allocated() / 1024**3
                mem_reserved = torch.cuda.memory_reserved() / 1024**3
                logger.info(
                    f"GPU Memory - Allocated: {mem_allocated:.2f}GB, "
                    f"Reserved: {mem_reserved:.2f}GB"
                )
        
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> LocalGenerationResult:
        """
        Gera resposta para o prompt (compatível com LLMClient).
        
        Args:
            prompt: Prompt de entrada
            max_tokens: Máximo de tokens a gerar
            temperature: Temperatura de amostragem
            **kwargs: Parâmetros adicionais
        
        Returns:
            LocalGenerationResult com:
            - text: Texto gerado
            - model: Nome do modelo
            - tokens_used: Total de tokens (entrada + saída)
            - finish_reason: Razão de término
            - generation_time: Tempo de geração em segundos
        """
        start_time = time.time()
        
        try:
            # Formatar prompt baseado no modelo
            formatted_prompt = self._format_prompt(prompt)
            
            # Gerar resposta
            outputs = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                return_full_text=False,
                pad_token_id=self.tokenizer.pad_token_id,
                **kwargs
            )
            
            generated_text = outputs[0]['generated_text']
            
            # Calcular tokens
            input_tokens = len(self.tokenizer.encode(formatted_prompt))
            output_tokens = len(self.tokenizer.encode(generated_text))
            total_tokens = input_tokens + output_tokens
            
            generation_time = time.time() - start_time
            
            return LocalGenerationResult(
                text=generated_text.strip(),
                model=self.model_name,
                tokens_used=total_tokens,
                finish_reason='COMPLETE',
                generation_time=generation_time
            )
        
        except Exception as e:
            logger.error(f"Erro na geração: {e}")
            raise
    
    def _format_prompt(self, prompt: str) -> str:
        """
        Formata prompt baseado no template do modelo.
        
        Args:
            prompt: Prompt original
        
        Returns:
            Prompt formatado
        """
        if self.model_name == 'phi-2':
            # Phi-2 usa formato instruct simples
            return f"Instruct: {prompt}\nOutput:"
        
        elif self.model_name == 'tinyllama':
            # TinyLlama usa formato ChatML
            return f"<|system|>\nYou are a helpful assistant.</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
        
        elif self.model_name == 'qwen2-0.5b':
            # Qwen2 usa formato próprio
            return f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        else:
            return prompt
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo.
        
        Returns:
            Dicionário com informações do modelo
        """
        info = {
            'name': self.model_name,
            'hf_model_id': self.hf_model_id,
            'quantized': self.quantize,
            'device': str(self.model.device) if self.model else None
        }
        
        if torch.cuda.is_available():
            info['gpu_memory_allocated_gb'] = torch.cuda.memory_allocated() / 1024**3
            info['gpu_memory_reserved_gb'] = torch.cuda.memory_reserved() / 1024**3
        
        return info
    
    def __repr__(self) -> str:
        return f"LocalLLMClient(model={self.model_name}, quantized={self.quantize})"


# Função auxiliar para criar cliente compatível com GenerationClient
def create_local_llm_client(model_name: str, quantize: bool = True) -> LocalLLMClient:
    """
    Cria cliente de modelo local.
    
    Args:
        model_name: Nome do modelo (phi-2, tinyllama, qwen2-0.5b)
        quantize: Se True, usa quantização 4-bit
    
    Returns:
        Instância de LocalLLMClient
    """
    return LocalLLMClient(model_name=model_name, quantize=quantize)
