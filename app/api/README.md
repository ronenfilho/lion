# LION API - RAG-based Q&A System

API FastAPI integrada com sistema RAG (Retrieval-Augmented Generation) para responder perguntas.

## Recursos

- **RAG Pipeline**: Retrieval (documentos) + LLM (geração de resposta)
- **Múltiplos Provedores LLM**: Groq, OpenAI, Anthropic
- **Retrieval Inteligente**: Fallback automático para mock se Chroma não estiver disponível
- **Configuração via .env**: Suporte a variáveis de ambiente para chaves de API

## Estrutura

```
app/api/
├── __init__.py           # Package init
├── app.py                # FastAPI application
├── config.py             # Settings from .env
├── llm.py                # LLM providers (Groq, OpenAI, Anthropic)
├── retriever.py          # Retrieval layer (Chroma + mock fallback)
├── qa.py                 # RAG pipeline (retrieve + generate)
└── requirements.txt      # Dependencies
```

## Configuração

1. **Instale dependências**:
```bash
pip install -r app/api/requirements.txt
```

2. **Configure `.env`** com suas chaves de API (exemplo):
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
TOP_K=5
```

## Executar

```bash
uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Servidor estará disponível em `http://localhost:8000`.

## Endpoints

### POST /ask
Faz uma pergunta e retorna uma resposta gerada por RAG.

**Request**:
```json
{
  "question": "O que é LION?",
  "context": "(opcional) contexto adicional"
}
```

**Response**:
```json
{
  "answer": "LION é um sistema de busca...",
  "confidence": 0.85,
  "source": "RAG (retriever + GroqProvider)"
}
```

### GET /health
Verifica se o serviço está rodando.

**Response**:
```json
{
  "status": "ok",
  "service": "LION Q&A API"
}
```

## Teste com cURL

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Qual é a arquitetura do LION?"}'
```

## Integração com Retrieval

Por padrão, o sistema tenta usar **Chroma** para retrieval. Se não estiver disponível, usa um **MockRetriever** que procura por keywords.

Para adicionar seus próprios documentos a Chroma:
```python
from app.api.retriever import get_retriever_instance

retriever = get_retriever_instance()
# Adicionar lógica para popular Chroma com seus documentos
```

## Provedores LLM Suportados

- **Groq** (padrão): Modelo rápido e eficiente
- **OpenAI**: GPT-4o-mini
- **Anthropic**: Claude 3.5 Sonnet

Troque o provider editando `LLM_PROVIDER` no `.env`.
