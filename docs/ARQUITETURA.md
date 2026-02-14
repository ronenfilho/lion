# 🦁 LION

## Arquitetura Proposta — Assistente IRPF com RAG

### Documento Técnico de Arquitetura (README)

---

## 📌 1. Visão Arquitetural

O **LION (Legal Interpretation and Official Norms)** é um sistema de Perguntas & Respostas (Q&A) para o domínio do **IRPF 2026**, baseado em arquitetura **RAG (Retrieval-Augmented Generation)**.

O objetivo é:

* 🔒 Garantir **acurácia normativa**
* 📚 Fundamentar respostas em **fontes oficiais**
* 🧠 Reduzir **alucinações**
* 📊 Validar ganhos quantitativos frente a LLMs sem RAG

O sistema foi desenhado para ser:

* Escalável
* Modular
* Reprodutível experimentalmente
* Auditável

---

# 🏗️ 2. Arquitetura Geral

## 2.1 Visão em Alto Nível

```
                ┌────────────────────┐
                │    Usuário         │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │  Query Processor   │
                └─────────┬──────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │ Retrieval (Vector DB)  │
              └─────────┬──────────────┘
                        │
                        ▼
              ┌────────────────────────┐
              │ Context Builder        │
              └─────────┬──────────────┘
                        │
                        ▼
              ┌────────────────────────┐
              │ LLM (Generation Layer) │
              └─────────┬──────────────┘
                        │
                        ▼
                ┌────────────────────┐
                │   Resposta Final   │
                └────────────────────┘
```

---

# 🧠 3. Camadas do Sistema

---

## 🆕 3.0 Camada 0 — Query Understanding & Preprocessing (NOVO)

Antes de entrar no pipeline RAG, implementar:

### Intent Classification

Classificar a pergunta em categorias:

```python
intents = [
    "deducoes",           # Sobre deduções permitidas
    "dependentes",        # Regras de dependentes
    "rendimentos",        # Tipos de rendimentos
    "obrigatoriedade",    # Quem deve declarar
    "prazo",              # Datas e prazos
    "retificacao",        # Como retificar
    "fora_escopo"         # Não é sobre IRPF
]
```

**Benefícios:**
- Filtrar perguntas fora do escopo
- Adicionar metadata filtering no retrieval
- Melhorar experiência do usuário

### Query Normalization

```python
def normalize_query(query: str) -> str:
    """
    - Corrigir erros ortográficos comuns
    - Expandir siglas (IRPF → Imposto de Renda Pessoa Física)
    - Normalizar valores monetários
    - Remover stop words irrelevantes
    """
    pass
```

### Entity Extraction

Extrair entidades-chave:
- **Anos:** 2024, 2025, 2026
- **Valores monetários:** R$ 28.559,70
- **Códigos normativos:** IN 2.255/2025
- **Tipos de rendimento:** aluguel, aposentadoria, trabalho

**Uso:** Adicionar como filtros no vector store

---

## 3.1 Camada 1 — Ingestão de Dados

### Entrada:

* **Perguntão IRPF 2025** (Perguntas e Respostas oficiais)
* **IN RFB nº 2.255/2025** (Instrução Normativa)
* **Lei nº 15.263/2025** (Lei de Linguagem Simples)
* **Manuais e Guias** da Receita Federal

### Pipeline de Ingestão Detalhado:

#### 1. Extração (PDF/HTML)

**Ferramentas recomendadas:**

```python
# Para PDFs estruturados
import pymupdf4llm  # Mantém estrutura e formatação
# ou
from langchain_community.document_loaders import PyPDFLoader

# Para PDFs complexos com tabelas
import camelot  # Extração de tabelas
# ou
from unstructured.partition.pdf import partition_pdf

# Para HTML
from bs4 import BeautifulSoup
from langchain_community.document_loaders import UnstructuredHTMLLoader
```

#### 2. Limpeza e Normalização

```python
def clean_document(text: str) -> str:
    """
    - Remover headers/footers repetitivos
    - Normalizar espaçamentos e quebras de linha
    - Corrigir hifenização entre linhas
    - Manter numeração de artigos/parágrafos
    - Preservar estrutura hierárquica
    """
    # Regex patterns para limpeza
    text = re.sub(r'\n{3,}', '\n\n', text)  # Excesso de quebras
    text = re.sub(r'(?<=\w)-\s+(?=\w)', '', text)  # Hifenização
    return text
```

#### 3. Segmentação Estrutural (Detalhado)

**Estratégia Structure-Aware MELHORADA:**

```python
class LegalDocumentChunker:
    """
    Respeita a hierarquia normativa:
    Lei > Capítulo > Seção > Artigo > Parágrafo > Inciso > Alínea
    """
    
    def chunk_by_structure(self, document):
        chunks = []
        
        # 1. Detectar estrutura hierárquica
        hierarchy = self.parse_legal_structure(document)
        
        # 2. Criar chunks por unidade normativa
        for artigo in hierarchy:
            chunk = {
                "content": artigo.full_text,
                "metadata": {
                    "artigo": artigo.numero,
                    "paragrafos": artigo.paragrafos,
                    "incisos": artigo.incisos,
                    "source": document.source,
                    "tipo": "artigo_completo"
                }
            }
            
            # 3. Se artigo > max_tokens, subdivide por parágrafo
            if len(chunk["content"]) > MAX_CHUNK_SIZE:
                chunks.extend(self.split_large_article(artigo))
            else:
                chunks.append(chunk)
        
        return chunks
    
    def add_context_window(self, chunks):
        """
        Adiciona contexto dos chunks adjacentes
        (artigo anterior/posterior)
        """
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk["context_before"] = chunks[i-1]["summary"]
            if i < len(chunks) - 1:
                chunk["context_after"] = chunks[i+1]["summary"]
        
        return chunks
```

**Para Perguntão (Q&A format):**

```python
class QAChunker:
    """
    Cada par Pergunta-Resposta é uma unidade atômica
    """
    
    def chunk_perguntao(self, document):
        qa_pairs = self.extract_qa_pairs(document)
        
        chunks = []
        for qa in qa_pairs:
            chunk = {
                "content": f"Pergunta: {qa.question}\n\nResposta: {qa.answer}",
                "metadata": {
                    "tipo": "pergunta_resposta",
                    "numero_pergunta": qa.id,
                    "categoria": self.classify_question(qa.question),
                    "keywords": self.extract_keywords(qa.question)
                }
            }
            chunks.append(chunk)
        
        return chunks
```

#### 4. Geração de Embeddings

```python
# Batch processing para eficiência
BATCH_SIZE = 100

def generate_embeddings(chunks, model="text-embedding-3-large"):
    embeddings = []
    
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_texts = [c["content"] for c in batch]
        
        # Gerar embeddings em lote
        batch_embeddings = embedding_model.encode(
            batch_texts,
            normalize_embeddings=True,  # Para cosine similarity
            show_progress_bar=True
        )
        
        embeddings.extend(batch_embeddings)
    
    return embeddings
```

#### 5. Indexação Vetorial com Metadados

```python
# ChromaDB example
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.create_collection(
    name="irpf_2025",
    metadata={"description": "IRPF 2025 - Base Normativa"},
    embedding_function=embedding_function
)

# Adicionar documentos com metadados ricos
collection.add(
    documents=[chunk["content"] for chunk in chunks],
    embeddings=embeddings,
    metadatas=[chunk["metadata"] for chunk in chunks],
    ids=[f"chunk_{i}" for i in range(len(chunks))]
)
```

---

## 3.2 Camada 2 — Estratégias de Chunking

Serão testadas duas abordagens:

### A) Sliding Window

* Tamanho fixo (ex: 800 tokens)
* Overlap: 20–30%
* Simples e eficiente

### B) Structure-Aware (Recomendado)

* Respeita:

  * Artigos
  * Incisos
  * Parágrafos
  * Pergunta-Resposta como unidade

➡ Espera-se melhor preservação normativa.

---

## 3.3 Camada 3 — Representação Vetorial

### Embeddings

Modelos possíveis (ordenados por recomendação):

1. **text-embedding-3-large** (OpenAI) → 3072 dimensões, melhor performance
2. **BGE-m3** (BAAI) → 1024 dimensões, multilingual, open-source
3. **nomic-embed-text-v1.5** → 768 dimensões, local, eficiente
4. **intfloat/multilingual-e5-large** → Excelente para português jurídico

### Vector Store

**Recomendações por cenário:**

* **Desenvolvimento/Experimentos:** ChromaDB (simples, local, persistente)
* **Produção pequena/média:** Qdrant (eficiente, suporta filtros)
* **Produção em larga escala:** Pinecone ou Weaviate (managed, escalável)
* **Self-hosted produção:** Milvus ou pgvector (PostgreSQL)

### Estratégias de Busca

#### 1. Dense Retrieval (Vetorial)
* Métrica: **Cosine similarity**
* Top-k: 5-10 chunks

#### 2. Hybrid Search (RECOMENDADO)
* **70% dense** (embeddings) + **30% sparse** (BM25/TF-IDF)
* Captura tanto similaridade semântica quanto keywords exatas
* Essencial para termos técnicos/normativos específicos

#### 3. Metadata Filtering
Estrutura de metadados:

```python
{
    "chunk_id": "IN2255_art12_inc2",
    "source": "IN_RFB_2255_2025",
    "tipo": "artigo|paragrafo|pergunta_resposta",
    "artigo": 12,
    "inciso": 2,
    "ano_vigencia": 2025,
    "topico": "deducoes|dependentes|rendimentos"
}
```

Permite filtros contextuais: "apenas IN 2255" ou "vigência 2025"

---

## 3.4 Camada 4 — Retrieval

### Pipeline de Retrieval Avançado

#### Fase 1: Query Processing
1. **Limpeza e normalização** da pergunta
2. **Query expansion** (opcional):
   - Extração de entidades (anos, valores, tipos de renda)
   - Geração de variações semânticas
3. **Embedding da pergunta**

#### Fase 2: Busca Multi-Estratégia (NOVO)

```python
# Hybrid Retrieval Pipeline
dense_results = vector_db.similarity_search(query_embedding, k=10)
sparse_results = bm25_index.search(query_text, k=10)

# Reciprocal Rank Fusion
combined_results = rrf_fusion(dense_results, sparse_results)
top_candidates = combined_results[:15]
```

#### Fase 3: Re-ranking (CRÍTICO)

**Por que re-ranking?**
- Embeddings capturam similaridade geral
- Re-ranker avalia relevância contextual específica

**Modelos recomendados:**
- **Cross-encoder:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Cohere Rerank** (API)
- **BGE-reranker-base**

**Pipeline:**
1. Retrieval inicial: top-15 chunks
2. Re-ranking: ordena por relevância real
3. Seleção final: top-5 para contexto

#### Fase 4: Context Window Management

**Estratégias de montagem do contexto:**

1. **Ordenação por relevância** (padrão)
2. **Ordenação estrutural** (manter ordem normativa)
3. **Diversificação de fontes** (evitar redundância)

**Controle de tokens:**
```python
MAX_CONTEXT_TOKENS = 4000  # Deixar espaço para prompt e resposta
```

#### Fase 5: Fallback Strategy

Se `max(similarity_scores) < 0.7`:
- Responder: "Não encontrei fundamentação normativa suficiente"
- Sugerir reformulação da pergunta
- **NÃO ALUCINAR**

---

## 3.5 Camada 5 — Geração

### Modelos LLM Avaliados

#### Tier 1: LLMs Grandes (Baseline e RAG)

1. **GPT-4 Turbo** / **GPT-4o**
   - Melhor raciocínio complexo
   - Custo alto
   
2. **Claude 3 Opus** / **Claude 3.5 Sonnet**
   - Excelente seguimento de instruções
   - Ótimo para contextos longos (200k tokens)
   
3. **Gemini 1.5 Pro**
   - Janela de contexto massiva (1M tokens)
   - Ótima relação custo-benefício

#### Tier 2: LLMs Médios/Pequenos Quantizados

1. **Llama 3.1 8B (Q4_K_M)**
   - Ótimo custo-benefício
   - Roda localmente
   
2. **Mistral 7B Instruct v0.3**
   - Eficiente e rápido
   - Bom em português
   
3. **Qwen2.5 7B Instruct**
   - Multilingual forte
   - Raciocínio jurídico adequado

### Prompt Engineering (CRÍTICO)

#### Template de Prompt RAG

```python
SYSTEM_PROMPT = """Você é um assistente especializado em IRPF (Imposto de Renda Pessoa Física).

REGRAS OBRIGATÓRIAS:
1. BASE suas respostas EXCLUSIVAMENTE nos documentos fornecidos abaixo
2. NUNCA invente informações ou cite artigos não mencionados no contexto
3. Se a informação não estiver nos documentos, diga: "Não encontrei essa informação nas fontes oficiais disponíveis"
4. SEMPRE cite a fonte específica (ex: "Conforme IN RFB 2.255/2025, art. 12")
5. Use linguagem clara e acessível, mas mantenha precisão técnica
6. Em caso de dúvida, seja conservador e indique buscar orientação profissional

CONTEXTO NORMATIVO:
{retrieved_chunks}

IMPORTANTE: As informações acima são a ÚNICA fonte de verdade. Não use conhecimento prévio do modelo."""

USER_PROMPT = """Pergunta: {user_question}

Responda de forma fundamentada, citando os artigos/parágrafos relevantes."""
```

#### Parâmetros de Geração

```python
generation_config = {
    "temperature": 0.2,        # Baixa criatividade, alta precisão
    "top_p": 0.9,              # Nucleus sampling
    "max_tokens": 800,         # Respostas concisas
    "presence_penalty": 0.1,   # Evita repetição
    "frequency_penalty": 0.1,
    "stop_sequences": ["###", "Contexto:"]  # Evita gerar chunks extras
}
```

### Chain-of-Thought para Casos Complexos (OPCIONAL)

Para perguntas que envolvem cálculos ou múltiplas etapas:

```python
COT_PROMPT = """Antes de responder, analise passo a passo:

1. Qual é exatamente a dúvida do contribuinte?
2. Quais normas se aplicam?
3. Existem exceções ou regras especiais?
4. Qual é a resposta final fundamentada?

Agora responda de forma estruturada."""
```

### Self-Consistency e Verificação (AVANÇADO)

Para aumentar confiabilidade:

1. Gerar 3 respostas independentes (temperatura 0.3)
2. Comparar consistência entre elas
3. Se divergirem significativamente → sinalizar incerteza
4. Se convergirem → maior confiança na resposta

---

# 🧪 4. Protocolo Experimental (Definido em Reunião 12/02)

Base: Reunião com Otávio

---

## 🎯 Experimento 1

### LLM Grande (ex: Gemini)

### Comparar:

| Modelo | RAG |
| ------ | --- |
| Gemini | ❌   |
| Gemini | ✅   |

Objetivo:

* Medir ganho percentual de acurácia
* Medir redução de alucinação

---

## 🎯 Experimento 2

### LLM Grande sem RAG vs LLM Pequeno + RAG

| Modelo                    | RAG |
| ------------------------- | --- |
| Gemini                    | ❌   |
| Modelo pequeno quantizado | ✅   |

Objetivo:

* Verificar se arquitetura supera tamanho do modelo
* Avaliar custo-benefício

Hipótese esperada:

> Um modelo menor + RAG supera modelo grande sem RAG em fidelidade normativa.

---

## 🎯 Experimento 3 — Repetição Estatística

Cada pergunta será executada:

* 🔁 5 execuções por configuração
* Calcular média de similaridade

### Métricas:

* BERTScore (F1)
* Faithfulness (RAGAS)
* Similaridade média
* Desvio padrão

---

## 🎯 Experimento 4 — Few-shot

Avaliar impacto de:

* Zero-shot
* Few-shot (3 exemplos do Perguntão)

Pergunta-chave:

> Few-shot melhora modelo sem RAG o suficiente para competir com RAG?

Expectativa:

* Melhora fluência
* Não resolve problema de atualização normativa

---

# 📊 5. Métricas de Avaliação

## 5.1 Retrieval

* Precision@k
* Recall@k

## 5.2 Generation

* BERTScore (F1)
* Faithfulness
* Answer Relevancy

## 5.3 Métrica Final

Score médio em 5 execuções:

```
Final Score = Média(BERTScore_F1)
```

---

# 🧮 6. Estrutura Reprodutível do Experimento

```
experiments/
│
├── config_1_llm_sem_rag/
├── config_2_llm_com_rag/
├── config_3_small_quant_rag/
│
├── results_raw/
├── results_metrics/
└── analysis.ipynb
```

Cada execução salva:

```json
{
  "question_id": 12,
  "model": "gemini",
  "rag": true,
  "run_id": 3,
  "response": "...",
  "bertscore": 0.89,
  "faithfulness": 0.94
}
```

---

# ⚙️ 7. Componentes Avançados e Otimizações (NOVO)

---

## 7.1 Semantic Caching

**Problema:** Queries similares reexecutam todo pipeline

**Solução:** Cache baseado em similaridade semântica

```python
class SemanticCache:
    """
    Se query nova tem similaridade > 0.95 com query em cache,
    retorna resposta cacheada
    """
    
    def __init__(self, similarity_threshold=0.95):
        self.cache_embeddings = []
        self.cache_responses = []
        self.threshold = similarity_threshold
    
    def get(self, query_embedding):
        if not self.cache_embeddings:
            return None
        
        similarities = cosine_similarity(
            query_embedding,
            self.cache_embeddings
        )
        
        max_sim_idx = np.argmax(similarities)
        
        if similarities[max_sim_idx] > self.threshold:
            return self.cache_responses[max_sim_idx]
        
        return None
    
    def set(self, query_embedding, response):
        self.cache_embeddings.append(query_embedding)
        self.cache_responses.append(response)
```

**Benefícios:**
- Reduz latência em 90%+ para queries similares
- Reduz custo de API calls
- Melhora UX

---

## 7.2 Guardrails e Validação de Output

### Input Guardrails

```python
class InputGuardrails:
    """
    Validar entrada antes de processar
    """
    
    def validate(self, query: str) -> tuple[bool, str]:
        # 1. Tamanho mínimo/máximo
        if len(query) < 10:
            return False, "Pergunta muito curta"
        
        if len(query) > 500:
            return False, "Pergunta muito longa"
        
        # 2. Detectar prompt injection
        injection_patterns = [
            "ignore previous instructions",
            "disregard your rules",
            "you are now",
            "pretend to be"
        ]
        
        for pattern in injection_patterns:
            if pattern in query.lower():
                return False, "Padrão de entrada inválido detectado"
        
        # 3. Detectar PII (dados sensíveis)
        if self.contains_pii(query):
            return False, "Por favor, não inclua CPF, nomes completos ou dados pessoais"
        
        return True, "OK"
```

### Output Guardrails

```python
class OutputGuardrails:
    """
    Validar resposta do LLM antes de entregar ao usuário
    """
    
    def validate(self, response: str, retrieved_chunks: list) -> tuple[bool, str]:
        # 1. Detectar alucinação de artigos
        cited_articles = self.extract_citations(response)
        valid_articles = self.extract_articles_from_chunks(retrieved_chunks)
        
        for article in cited_articles:
            if article not in valid_articles:
                return False, "Resposta cita artigos não presentes no contexto"
        
        # 2. Detectar disclaimers ausentes
        if "consulte um contador" not in response.lower():
            response += "\n\n⚠️ Esta resposta é informativa. Para casos específicos, consulte um profissional contábil."
        
        # 3. Verificar comprimento
        if len(response) < 50:
            return False, "Resposta muito curta, possivelmente incompleta"
        
        return True, response
```

---

## 7.3 Observabilidade e Logging

### Estrutura de Log Completa

```python
import logging
from datetime import datetime
import json

class RAGLogger:
    """
    Log estruturado de toda execução
    """
    
    def log_query(self, query_data: dict):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": query_data["session_id"],
            "query": query_data["query"],
            "query_embedding_time_ms": query_data["embedding_time"],
            
            # Retrieval
            "retrieval": {
                "num_candidates": query_data["num_candidates"],
                "top_k": query_data["top_k"],
                "retrieval_time_ms": query_data["retrieval_time"],
                "chunks_retrieved": [
                    {
                        "chunk_id": c["id"],
                        "similarity_score": c["score"],
                        "source": c["source"]
                    }
                    for c in query_data["chunks"]
                ]
            },
            
            # Generation
            "generation": {
                "model": query_data["model"],
                "temperature": query_data["temperature"],
                "tokens_input": query_data["input_tokens"],
                "tokens_output": query_data["output_tokens"],
                "generation_time_ms": query_data["generation_time"],
                "cost_usd": query_data["cost"]
            },
            
            # Response
            "response": query_data["response"],
            "response_length": len(query_data["response"]),
            
            # Quality metrics
            "quality": {
                "num_citations": query_data.get("num_citations", 0),
                "avg_chunk_similarity": query_data.get("avg_similarity", 0),
                "cache_hit": query_data.get("cache_hit", False)
            }
        }
        
        # Salvar em arquivo JSON Lines
        with open("logs/queries.jsonl", "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
```

### Dashboarding com Prometheus + Grafana (Produção)

```python
from prometheus_client import Counter, Histogram, Gauge

# Métricas
query_counter = Counter('rag_queries_total', 'Total queries')
retrieval_latency = Histogram('rag_retrieval_latency_seconds', 'Retrieval latency')
generation_latency = Histogram('rag_generation_latency_seconds', 'Generation latency')
cache_hit_rate = Gauge('rag_cache_hit_rate', 'Cache hit rate')
avg_similarity = Gauge('rag_avg_similarity_score', 'Average chunk similarity')
```

---

## 7.4 A/B Testing Framework

Para experimentos em produção:

```python
class ABTestManager:
    """
    Distribuir usuários entre configurações
    """
    
    def __init__(self):
        self.experiments = {
            "chunking_strategy": {
                "variants": ["fixed", "structural"],
                "traffic_split": [0.5, 0.5]
            },
            "reranking": {
                "variants": ["with_rerank", "without_rerank"],
                "traffic_split": [0.7, 0.3]
            }
        }
    
    def assign_variant(self, user_id: str, experiment: str):
        # Consistent hashing para mesmo usuário ter mesma experiência
        hash_value = hash(f"{user_id}_{experiment}") % 100
        
        cumulative = 0
        for variant, traffic in zip(
            self.experiments[experiment]["variants"],
            self.experiments[experiment]["traffic_split"]
        ):
            cumulative += traffic * 100
            if hash_value < cumulative:
                return variant
        
        return self.experiments[experiment]["variants"][0]
```

---

## 7.5 Feedback Loop e Continuous Learning

```python
class FeedbackCollector:
    """
    Coletar feedback dos usuários para melhoria contínua
    """
    
    def collect_feedback(self, query_id: str, feedback: dict):
        """
        feedback = {
            "helpful": bool,
            "accurate": bool (1-5),
            "sources_cited": bool,
            "comments": str (opcional)
        }
        """
        
        # Salvar em banco
        self.db.insert({
            "query_id": query_id,
            "timestamp": datetime.now(),
            **feedback
        })
        
        # Se feedback negativo, adicionar a fila de revisão
        if not feedback["helpful"] or feedback["accurate"] < 3:
            self.add_to_review_queue(query_id)
    
    def analyze_feedback(self):
        """
        Identificar padrões:
        - Queries com baixa satisfação
        - Gaps de conhecimento
        - Chunks que nunca são recuperados
        - Chunks sempre recuperados mas irrelevantes
        """
        pass
```

---

# ⚙️ 8. Boas Práticas Arquiteturais (ATUALIZADO)

### 🔹 Modularização

Separar responsabilidades em módulos independentes:

```
src/
├── ingestion/
│   ├── extractors/      # PDF, HTML, etc
│   ├── cleaners/        # Normalização
│   ├── chunkers/        # Estratégias de chunking
│   └── embedders/       # Geração de embeddings
│
├── retrieval/
│   ├── vector_store.py
│   ├── hybrid_search.py
│   ├── reranker.py
│   └── query_processor.py
│
├── generation/
│   ├── llm_client.py
│   ├── prompt_templates.py
│   └── output_parser.py
│
├── evaluation/
│   ├── metrics/
│   ├── evaluators/
│   └── experiments/
│
├── guardrails/
│   ├── input_validation.py
│   └── output_validation.py
│
├── monitoring/
│   ├── logger.py
│   ├── metrics.py
│   └── tracer.py
│
└── utils/
    ├── cache.py
    ├── config.py
    └── helpers.py
```

### 🔹 Reprodutibilidade

```python
# config/experiment.yaml
experiment:
  name: "exp_001_gemini_rag_structural"
  seed: 42
  
model:
  name: "gemini-1.5-pro"
  temperature: 0.2
  top_p: 0.9
  max_tokens: 800
  
retrieval:
  strategy: "hybrid"
  top_k: 5
  rerank: true
  similarity_threshold: 0.7
  
chunking:
  strategy: "structural"
  max_chunk_size: 800
  overlap: 0

evaluation:
  runs_per_query: 5
  metrics: ["bertscore", "faithfulness", "answer_relevancy"]
```

### 🔹 Controle de Versão de Componentes

```python
# Versionamento de componentes
class ComponentVersion:
    EMBEDDING_MODEL = "text-embedding-3-large"
    EMBEDDING_VERSION = "v1.0"
    CHUNKING_STRATEGY = "structural_v2"
    PROMPT_TEMPLATE = "v3.1"
    
    @classmethod
    def to_dict(cls):
        return {
            "embedding_model": cls.EMBEDDING_MODEL,
            "embedding_version": cls.EMBEDDING_VERSION,
            "chunking_strategy": cls.CHUNKING_STRATEGY,
            "prompt_template": cls.PROMPT_TEMPLATE
        }
```

### 🔹 Gestão de Configuração com Validação

```python
# Usar Pydantic para validação
from pydantic import BaseModel, Field

class RetrievalConfig(BaseModel):
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    use_reranker: bool = True
    hybrid_alpha: float = Field(default=0.7, ge=0.0, le=1.0)

class GenerationConfig(BaseModel):
    model_name: str
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=800, ge=100, le=4000)
```

### 🔹 Controle de Temperatura

* **0.2** para experimentos comparativos (máxima consistência)
* **0.3-0.5** para produção (leve variação aceitável)
* **0.7+** apenas para casos criativos (não recomendado para domínio legal)

### 🔹 Observabilidade Completa

Logar em cada execução:

* ✅ Query original e normalizada
* ✅ Chunks recuperados (IDs, scores, sources)
* ✅ Tempo de retrieval
* ✅ Tempo de geração
* ✅ Tokens consumidos
* ✅ Custo estimado
* ✅ Cache hit/miss
* ✅ Resposta final
* ✅ Citações extraídas

---

# 🔐 9. Segurança e IA Responsável (EXPANDIDO)

### 9.1 Princípios

* ✅ Base exclusivamente oficial (sem dados sintéticos ou scraped)
* ✅ Resposta fundamentada com rastreabilidade
* ✅ Transparência de fontes e limitações
* ✅ Não aconselhamento jurídico vinculante
* ✅ Indicação explícita da base normativa

### 9.2 Proteção de Dados

```python
class PIIDetector:
    """
    Detectar e anonimizar dados pessoais
    """
    
    patterns = {
        "cpf": r'\d{3}\.\d{3}\.\d{3}-\d{2}',
        "cnpj": r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "telefone": r'\(\d{2}\)\s?\d{4,5}-?\d{4}'
    }
    
    def detect_and_mask(self, text: str) -> str:
        for pii_type, pattern in self.patterns.items():
            text = re.sub(pattern, f"[{pii_type.upper()}_REMOVIDO]", text)
        return text
```

### 9.3 Rate Limiting e Abuse Prevention

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/query")
@limiter.limit("10/minute")  # Max 10 queries por minuto por IP
async def query_endpoint(request: QueryRequest):
    pass
```

### 9.4 Disclaimers Obrigatórios

Toda resposta deve incluir:

```
⚠️ AVISO IMPORTANTE:
Esta resposta é meramente informativa e baseada em fontes oficiais disponíveis 
até [DATA]. Não constitui consultoria tributária ou jurídica. Para situações 
específicas, consulte um contador ou advogado tributarista.
```

---

# 🚀 10. Escalabilidade e Produção

### 10.1 Roadmap de Escala

Projeto preparado para:

#### Fase 1: MVP Experimental (Atual)
* 50 queries de teste
* Execução local
* Modelos via API

#### Fase 2: Beta Privado
* 500-1000 usuários
* Deploy em Cloud (AWS/GCP)
* Monitoramento básico

#### Fase 3: Produção
* Escala horizontal
* CDN para assets
* Cache distribuído (Redis)
* Load balancing

#### Fase 4: Multi-domínio
* IRPF + IRPJ
* ISS, ICMS
* Multi-ano (2024-2027)

### 10.2 Arquitetura de Deploy

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ┌──────▼──────┐          ┌──────▼──────┐
         │  API Server │          │  API Server │
         │   (FastAPI) │          │   (FastAPI) │
         └──────┬──────┘          └──────┬──────┘
                │                         │
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │   Vector DB Cluster     │
                │   (Qdrant/Weaviate)     │
                └─────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │    Redis Cache          │
                └─────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │  PostgreSQL (Logs/Meta) │
                └─────────────────────────┘
```

### 10.3 Otimizações de Performance

#### Cache Estratégico
* **L1:** Semantic cache (in-memory)
* **L2:** Redis (respostas completas)
* **L3:** CDN (assets estáticos)

#### Batch Processing
* Processar múltiplas queries em paralelo
* Batch embedding generation

#### Async Processing
```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.post("/query")
async def async_query(request: QueryRequest):
    # Paralelizar retrieval e preparação de prompt
    chunks_task = asyncio.create_task(retriever.retrieve(request.query))
    embedding_task = asyncio.create_task(embedder.embed(request.query))
    
    chunks, query_embedding = await asyncio.gather(chunks_task, embedding_task)
    
    # Generation
    response = await llm.generate(chunks, request.query)
    return response
```

### 10.4 Custos e Estimativas

| Componente | Custo Mensal (1000 queries/dia) |
|-----------|----------------------------------|
| Embedding API | ~$20-30 |
| LLM API (GPT-4) | ~$300-500 |
| Vector DB (Managed) | ~$50-100 |
| Cloud Hosting | ~$100-200 |
| **Total** | **~$500-850** |

**Otimizações:**
- Usar modelos locais quantizados: **-70% custo LLM**
- Self-host vector DB: **-100% custo Vector DB**
- Cache hit rate 40%: **-40% custo total**

---

# 📌 11. Estrutura de Diretórios Completa (ATUALIZADO)

```
📁 LION/
│
├── 📂 data/
│   ├── raw/                    # Fontes originais
│   │   ├── perguntao_2025.pdf
│   │   ├── IN_2255_2025.pdf
│   │   └── lei_15263_2025.pdf
│   ├── processed/              # Texto limpo e normalizado
│   │   ├── perguntao_cleaned.json
│   │   └── instrucoes_normativas.json
│   └── embeddings/             # Bases vetoriais
│       ├── chroma_db/
│       └── metadata_index.json
│
├── 📂 src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py
│   │   ├── html_extractor.py
│   │   ├── text_cleaner.py
│   │   ├── chunking/
│   │   │   ├── fixed_chunker.py
│   │   │   ├── structural_chunker.py
│   │   │   └── qa_chunker.py
│   │   └── embedding_pipeline.py
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vector_store.py      # Abstração para ChromaDB/Qdrant
│   │   ├── hybrid_retriever.py  # Dense + Sparse
│   │   ├── reranker.py
│   │   ├── query_processor.py
│   │   └── semantic_cache.py
│   │
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── llm_client.py        # Abstração para múltiplos LLMs
│   │   ├── prompt_templates.py
│   │   ├── output_parser.py
│   │   └── citation_extractor.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics/
│   │   │   ├── bertscore.py
│   │   │   ├── ragas_metrics.py
│   │   │   └── retrieval_metrics.py
│   │   ├── evaluators/
│   │   │   ├── rag_evaluator.py
│   │   │   └── baseline_evaluator.py
│   │   └── experiments/
│   │       ├── experiment_runner.py
│   │       └── results_analyzer.py
│   │
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── input_validator.py
│   │   ├── output_validator.py
│   │   └── pii_detector.py
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── metrics_collector.py
│   │   └── tracer.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── helpers.py
│
├── 📂 experiments/
│   ├── configs/                 # YAMLs de configuração
│   │   ├── exp_001_gemini_no_rag.yaml
│   │   ├── exp_002_gemini_rag_fixed.yaml
│   │   ├── exp_003_gemini_rag_structural.yaml
│   │   └── exp_004_llama_rag_structural.yaml
│   ├── results/
│   │   ├── raw/                # JSONs de cada execução
│   │   └── metrics/            # Métricas agregadas
│   └── notebooks/              # Análise de resultados
│       └── analysis.ipynb
│
├── 📂 tests/
│   ├── unit/
│   │   ├── test_chunking.py
│   │   ├── test_retrieval.py
│   │   └── test_generation.py
│   ├── integration/
│   │   └── test_rag_pipeline.py
│   └── fixtures/
│       └── sample_queries.json
│
├── 📂 app/
│   ├── main.py                 # FastAPI app
│   ├── api/
│   │   ├── routes.py
│   │   └── models.py
│   └── ui/                     # Interface (opcional)
│       └── streamlit_app.py
│
├── 📂 config/
│   ├── default.yaml
│   ├── development.yaml
│   └── production.yaml
│
├── 📂 logs/
│   ├── queries.jsonl
│   └── errors.log
│
├── 📂 docs/
│   ├── PROJETO_LION.md
│   ├── ARQUITETURA.md          # Este documento
│   ├── API_DOCS.md
│   └── DEPLOYMENT.md
│
├── 📂 scripts/
│   ├── setup_database.py
│   ├── run_experiments.py
│   └── generate_report.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# 📊 12. Hipóteses Consolidadas e Experimentos

1. RAG melhora significativamente fidelidade normativa.
2. Modelo pequeno + RAG pode superar modelo grande sem RAG.
3. Few-shot não substitui recuperação externa.
4. A média de 5 execuções reduz viés estocástico.

---

# 🏁 11. Status do Projeto

Fase Atual:
**Planejamento → Início do Desenvolvimento Experimental**

**Última atualização da arquitetura:** 14/02/2026

---

# 📚 Referências Técnicas

## Papers Fundamentais
- RAG: Lewis et al. (2020)
- RAGAS: Es et al. (2023)
- Transformers: Vaswani et al. (2017)

## Frameworks Utilizados
- LangChain / LlamaIndex
- ChromaDB / Qdrant
- FastAPI
- RAGAS

---

**Versão do Documento:** 2.0 (Arquitetura Expandida e Melhorada)
**Autor:** Ronen Rodrigues Silva Filho
**Contribuições:** Otimizações arquiteturais por especialista em RAG
