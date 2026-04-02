# LION Q&A Streamlit UI

Interface web interativa para o sistema LION de Pergunta e Resposta baseado em RAG.

## Funcionalidades

### 📝 Interface Principal
- **Q&A Interativo**: Faça perguntas e receba respostas com citações
- **Visualização de Trechos**: Veja os documentos que fundamentaram a resposta
- **Histórico**: Acompanhe todas as suas perguntas e respostas
- **Exportação**: Salve respostas individuais ou todo o histórico em JSON

### ⚙️ Configurações
- **URL da API**: Configure o endpoint da API LION
- **Verificação de Status**: Valide a conexão com a API
- **Modo Avançado**: Ajuste parâmetros como temperatura e comprimento máximo
- **Contexto Adicional**: Forneça contexto extra para perguntas

### 🎨 Interface Rica
- Layout responsivo com múltiplas abas
- Expandable sections para trechos recuperados
- Métricas de confiança com indicadores visuais
- Código formatado para chunk IDs
- CSS customizado para melhor visualização

## Instalação

### Pré-requisitos
1. API LION rodando: `uvicorn app.api.app:app --host 127.0.0.1 --port 8001`
2. Streamlit instalado: `pip install streamlit`

### Setup

```bash
# Navegar para o projeto
cd /home/decode/workspace/lion

# Ativar environment
source venv/bin/activate

# Instalar streamlit (se não estiver instalado)
pip install streamlit

# Rodar a aplicação
streamlit run app/ui/streamlit_app.py
```

## Uso

### Modo Básico

1. **Abra a aplicação**: Streamlit abrirá em `http://localhost:8501`

2. **Faça uma pergunta**:
   - Digite a pergunta na seção "💬 Q&A"
   - Clique em "🔍 Buscar Resposta"

3. **Visualize a resposta**:
   - Resposta formatada
   - Métricas (Confiança, Fonte, Citações)
   - Citações com IDs dos chunks
   - Trechos recuperados (se habilitado)

### Modo Avançado

1. **Ative o Modo Avançado**:
   - Acesse a sidebar
   - Marque "🔧 Modo avançado"

2. **Configure parâmetros**:
   - **Temperatura**: Controla a criatividade da resposta (0.0-2.0)
   - **Máx de tokens**: Comprimento máximo da resposta

### Histórico de Perguntas

1. **Acesse a aba "📊 Histórico"**:
   - Veja tabela com todas as perguntas
   - Selecione uma para ver detalhes
   - Visualize respostas anteriores

2. **Exporte o histórico**:
   - Clique em "📥 Exportar Histórico como JSON"
   - Faça download do arquivo

### Salvando Respostas

1. **Após receber uma resposta**:
   - Clique em "💾 Salvar"
   - Arquivo JSON é criado em `app/ui/response_YYYYMMDD_HHMMSS.json`

## Estrutura de Arquivos

```
app/ui/
├── __init__.py
├── streamlit_app.py          # Aplicação principal
├── README.md                 # Este arquivo
├── response_*.json           # Respostas individuais salvas
└── history_export_*.json     # Históricos exportados
```

## Configuração da API

### URL da API

Por padrão, a aplicação se conecta a:
```
http://127.0.0.1:8001
```

Para usar um servidor remoto:

1. Acesse "⚙️ Configuração da API" na sidebar
2. Altere a URL
3. Clique em "🔍 Verificar Status" para validar

### Parâmetros da API

A API LION usa os seguintes parâmetros (configurados em `.env`):

- `RETRIEVAL_TYPE`: Tipo de retrieval (hybrid, dense, bm25, mock)
- `TOP_K`: Número de chunks recuperados (padrão: 5)
- `HYBRID_ALPHA`: Peso do retrieval denso vs BM25 (padrão: 0.7)
- `TEMPERATURE`: Criatividade do LLM (padrão: 0.2)
- `MAX_TOKENS`: Comprimento máximo da resposta (padrão: 800)

## Formato das Respostas

### Resposta JSON

```json
{
  "answer": "Sim, você deve declarar imposto de renda se...",
  "confidence": 0.0011,
  "source": "RAG (retriever + GroqProvider)",
  "citations": [
    {
      "index": 1,
      "chunk_id": "L9250compilado_processed_preambulo_art_36",
      "score": 0.0011,
      "content": "CAPÍTULO VIII - DISPOSIÇÕES FINAIS... [truncado]"
    },
    ...
  ]
}
```

### Histórico JSON

```json
{
  "timestamp": "2026-04-02T10:30:45",
  "question": "EU DEVO DECLARAR IMPOSTO DE RENDA?",
  "context": null,
  "response": { ... }
}
```

## Performance

- **Primeira consulta**: ~2-3 segundos (inicializa retriever)
- **Consultas subsequentes**: ~0.5-1 segundo
- **Exibição de trechos**: Instantânea (expandable sections)

## Troubleshooting

### "API não está acessível"

1. Verifique se a API está rodando:
```bash
curl http://127.0.0.1:8001/health
```

2. Se rodando em servidor remoto, atualize a URL em "⚙️ Configuração da API"

### "Streamlit não encontrado"

Instale Streamlit:
```bash
pip install streamlit
```

### Interface lenta

1. Verifique a conexão com a API
2. Desabilite "Mostrar trechos recuperados" se houver muitos chunks
3. Reduza MAX_TOKENS em "Modo Avançado"

## Recursos Futuro

- [ ] Histórico persistente em banco de dados
- [ ] Filtros de busca no histórico
- [ ] Gráficos de confiança ao longo do tempo
- [ ] Suporte a upload de documentos para retrieval
- [ ] Comparação de respostas entre diferentes modelos
- [ ] Modo conversacional com múltiplas turnos
- [ ] Integração com Jira/GitHub para criar issues

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│         Streamlit Web UI (streamlit_app.py)     │
│  - Q&A Interface                                 │
│  - History Management                            │
│  - Response Visualization                        │
└──────────────────┬──────────────────────────────┘
                   │ HTTP POST/GET
                   ▼
┌─────────────────────────────────────────────────┐
│      FastAPI LION Q&A API (app.api.app.py)      │
│  /health - Health check                          │
│  /ask - Q&A endpoint                             │
└──────────────────┬──────────────────────────────┘
                   │ Python
                   ▼
┌─────────────────────────────────────────────────┐
│         RAG Pipeline (app.api.qa.py)             │
│  1. Retrieve (HybridRetriever)                   │
│  2. Build Context                                │
│  3. Generate (Groq LLM)                          │
└─────────────────────────────────────────────────┘
```

## Desenvolvimento

### Adicionar nova funcionalidade

1. Edite `streamlit_app.py`
2. Teste localmente: `streamlit run app/ui/streamlit_app.py`
3. Commit: `git add app/ui && git commit -m "feature: ..."`

### Debug

Ative modo debug do Streamlit:
```bash
streamlit run app/ui/streamlit_app.py --logger.level=debug
```

## Licença

Parte do projeto LION - Veja LICENSE na raiz do projeto

## Suporte

Para questões ou bugs:
1. Verifique o status da API
2. Consulte logs: `tail -f /tmp/lion_api.log`
3. Abra uma issue no GitHub
