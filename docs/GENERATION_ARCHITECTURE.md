# Sistema de Geração Multi-Provider

## 🎯 Visão Geral

O sistema de geração do LION foi projetado com **abstração de provedores**, permitindo trocar facilmente entre diferentes LLMs (Google Gemini, OpenAI, Anthropic, etc.) sem alterar o código de aplicação.

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      Camada de Aplicação                     │
│  (RAG Pipeline, Prompts, Output Parser)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLMProvider (Interface)                   │
│  • generate()                                                │
│  • generate_with_context()                                   │
│  • chat()                                                    │
│  • count_tokens()                                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Gemini     │  │   OpenAI     │  │  Anthropic   │
│   Provider   │  │   Provider   │  │   Provider   │
│              │  │  (futuro)    │  │  (futuro)    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Componentes

#### 1. **LLMProvider** (Interface Abstrata)
`src/generation/llm_provider.py`

Define o contrato que todos os provedores devem seguir:

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(prompt, system_instruction, stream) -> GenerationResult
    
    @abstractmethod
    def generate_with_context(query, chunks, ...) -> GenerationResult
    
    @abstractmethod
    def chat(messages, system_instruction) -> GenerationResult
    
    @abstractmethod
    def count_tokens(text) -> int
```

**Benefícios:**
- ✅ Código de aplicação independente do provedor
- ✅ Fácil adicionar novos provedores
- ✅ Testável com mocks

#### 2. **Implementações Concretas**
`src/generation/providers/`

Cada provedor implementa a interface `LLMProvider`:

- **GeminiProvider**: Google Gemini API
- **OpenAIProvider**: (futuro) GPT-4, GPT-3.5
- **AnthropicProvider**: (futuro) Claude 3
- **OllamaProvider**: (futuro) Modelos locais

#### 3. **LLMFactory**
`src/generation/llm_factory.py`

Factory pattern para criar provedores dinamicamente:

```python
# Criar usando .env
llm = create_llm_client()

# Criar específico
llm = create_llm_client(provider='gemini')

# Com configuração
config = GenerationConfig(temperature=0.7)
llm = create_llm_client(config=config)
```

## 🔧 Configuração

### Arquivo `.env`

```bash
# Escolher provedor
LLM_PROVIDER=gemini

# Configurar chave API
GEMINI_API_KEY=sua_chave_aqui

# Escolher modelo
LLM_MODEL=gemini-2.0-flash-exp

# Parâmetros
TEMPERATURE=0.2
MAX_TOKENS=800
```

### Trocar de Provedor

**Opção 1: Via .env**
```bash
# De Gemini para OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo
```

**Opção 2: Via código**
```python
# Gemini
llm = create_llm_client(provider='gemini')

# OpenAI
llm = create_llm_client(provider='openai')
```

**Nenhuma alteração no código de aplicação é necessária!**

## 💻 Uso

### Geração Básica

```python
from generation import create_llm_client

llm = create_llm_client()
result = llm.generate("O que é IRPF?")

print(result.text)
print(f"Tokens: {result.tokens_used}")
print(f"Provedor: {result.provider}")
```

### Geração RAG

```python
chunks = [
    "Art. 68. São permitidas deduções...",
    "§ 1º As deduções devem ser comprovadas..."
]

result = llm.generate_with_context(
    query="Quais deduções são permitidas?",
    context_chunks=chunks,
    system_instruction="Você é um assistente de IRPF."
)
```

### Chat Multi-turno

```python
messages = [
    {'role': 'user', 'content': 'O que é IRPF?'},
    {'role': 'assistant', 'content': 'IRPF é...'},
    {'role': 'user', 'content': 'Quem precisa declarar?'}
]

result = llm.chat(messages)
```

## 🆕 Adicionar Novo Provedor

### 1. Criar classe do provedor

```python
# src/generation/providers/openai_provider.py

from openai import OpenAI
from ..llm_provider import LLMProvider, GenerationResult

class OpenAIProvider(LLMProvider):
    def __init__(self, model_name, config, api_key):
        self.client = OpenAI(api_key=api_key)
        self._model_name = model_name
        self.config = config
    
    def generate(self, prompt, system_instruction, stream):
        messages = []
        if system_instruction:
            messages.append({'role': 'system', 'content': system_instruction})
        messages.append({'role': 'user', 'content': prompt})
        
        response = self.client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return GenerationResult(
            text=response.choices[0].message.content,
            model=self._model_name,
            provider='openai',
            tokens_used=response.usage.total_tokens,
            finish_reason=response.choices[0].finish_reason,
            generation_time=...
        )
    
    # Implementar outros métodos...
```

### 2. Registrar na factory

```python
# src/generation/llm_factory.py

from .providers.openai_provider import OpenAIProvider

class LLMFactory:
    SUPPORTED_PROVIDERS = {
        'gemini': GeminiProvider,
        'openai': OpenAIProvider,  # ✅ Adicionar aqui
    }
```

### 3. Usar!

```python
llm = create_llm_client(provider='openai', model_name='gpt-4-turbo')
```

## 📊 Comparação de Provedores

| Provedor | Modelos | Custo | Velocidade | Contexto |
|----------|---------|-------|------------|----------|
| **Gemini** | 2.0-flash, 1.5-pro | Gratuito | Rápido | 1M tokens |
| OpenAI | GPT-4, GPT-3.5 | Pago | Médio | 128k tokens |
| Anthropic | Claude 3 | Pago | Médio | 200k tokens |
| Ollama | Llama, Mistral | Grátis | Depende | Varia |

## 🎯 Casos de Uso

### 1. Desenvolvimento Local
```bash
LLM_PROVIDER=gemini  # Gratuito para testes
```

### 2. Produção com Alta Qualidade
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
```

### 3. Privacidade/Offline
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3-8b
```

### 4. Experimentos Comparativos
```python
# Testar mesmo prompt em múltiplos provedores
providers = ['gemini', 'openai', 'anthropic']

for provider_name in providers:
    llm = create_llm_client(provider=provider_name)
    result = llm.generate(test_prompt)
    
    print(f"{provider_name}: {result.text}")
    print(f"Tempo: {result.generation_time}s")
```

## 🔍 Dataclasses

### GenerationConfig
```python
@dataclass
class GenerationConfig:
    temperature: float = 0.2      # Criatividade (0-1)
    max_tokens: int = 800          # Tamanho máximo
    top_p: float = 0.95            # Nucleus sampling
    top_k: int = 40                # Top-k sampling
    stop_sequences: List[str] = None
```

### GenerationResult
```python
@dataclass
class GenerationResult:
    text: str                      # Resposta gerada
    model: str                     # Nome do modelo
    provider: str                  # gemini, openai, etc.
    tokens_used: int               # Tokens consumidos
    finish_reason: str             # stop, length, etc.
    generation_time: float         # Tempo em segundos
    metadata: Dict = None          # Dados extras
```

## 🧪 Testes

```python
# Usar mock para testes
class MockLLMProvider(LLMProvider):
    def generate(self, prompt, **kwargs):
        return GenerationResult(
            text="Resposta mockada",
            model="mock-model",
            provider="mock",
            tokens_used=10,
            finish_reason="stop",
            generation_time=0.1
        )

# Injetar no código de teste
def test_rag_pipeline():
    llm = MockLLMProvider()
    pipeline = RAGPipeline(llm_provider=llm)
    result = pipeline.query("test")
    assert result.text == "Resposta mockada"
```

## 📝 Checklist para Adicionar Provedor

- [ ] Criar classe em `src/generation/providers/`
- [ ] Implementar todos os métodos de `LLMProvider`
- [ ] Adicionar em `LLMFactory.SUPPORTED_PROVIDERS`
- [ ] Atualizar `.env.example` com chaves e modelos
- [ ] Criar testes unitários
- [ ] Documentar parâmetros específicos
- [ ] Adicionar exemplo de uso

## 🚀 Roadmap

### Implementados
- ✅ GeminiProvider (Google Gemini)
- ✅ LLMFactory com seleção dinâmica
- ✅ Interface abstrata LLMProvider

### Próximos
- [ ] OpenAIProvider (GPT-4, GPT-3.5)
- [ ] AnthropicProvider (Claude 3)
- [ ] OllamaProvider (modelos locais)
- [ ] AzureOpenAIProvider
- [ ] BedrockProvider (AWS)

## 💡 Benefícios da Arquitetura

1. **Flexibilidade**: Trocar de provedor em 1 linha
2. **Testabilidade**: Usar mocks facilmente
3. **Extensibilidade**: Adicionar novos provedores sem quebrar código existente
4. **Vendor Lock-in**: Zero dependência de um único provedor
5. **Experimentos**: Comparar provedores facilmente
6. **Custo**: Otimizar custos escolhendo provedor mais barato
7. **Performance**: Usar provedor mais rápido quando necessário
8. **Compliance**: Usar provedor local para dados sensíveis

---

**Última atualização:** 14/02/2026  
**Versão:** 2.0 (Arquitetura Multi-Provider)
