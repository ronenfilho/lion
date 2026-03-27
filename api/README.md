# LION - Q&A API

API mínima para fazer perguntas e receber respostas. Implementada com FastAPI.

Endpoints
- `POST /ask` — aceita JSON `{ "question": "...", "context": "..." }` e retorna `{ "answer": "...", "confidence": 0.5, "source": "mock" }`.

Como executar (local)

1. Instale dependências (recomendado dentro do `venv` do projeto):

```bash
pip install -r api/requirements.txt
```

2. Execute o servidor de desenvolvimento:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

3. Teste com curl:

```bash
curl -X POST "http://127.0.0.1:8000/ask" -H "Content-Type: application/json" -d '{"question":"Qual é a soma de 2+2?"}'
```

Substituir a função `answer_question` em `api/qa.py` é o ponto de integração para ligar seu modelo (LLM, RAG, etc.).
