````markdown
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

# 📊 6. Camada de Avaliação (Implementada)

Para garantir a qualidade e confiabilidade das respostas, o sistema inclui um módulo de avaliação automatizada implementado.

## 6.1 Métricas Implementadas

### A) Métricas Base RAG

**Módulo:** `src/evaluation/metrics/rag_metrics.py`

* **Tempo de Resposta**: Latência ponta a ponta do pipeline
* **Tamanho do Contexto**: Quantidade de tokens/chunks recuperados
* **Taxa de Recuperação**: Chunks relevantes vs total recuperado

**Uso:**
```python
from evaluation.metrics import create_rag_evaluator

evaluator = create_rag_evaluator()
metrics = evaluator.evaluate(
    query="Como declarar dependentes?",
    answer=resposta_gerada,
    context=chunks_recuperados,
    response_time=0.8
)
# Retorna: response_time, context_size, context_tokens
```

### B) Métricas Semânticas (BERTScore)

**Módulo:** `src/evaluation/metrics/bertscore.py`

Avalia similaridade semântica entre resposta gerada e ground truth usando embeddings BERT.

**Características:**
* Modelo: `bert-base-multilingual-cased` (otimizado para português)
* Métricas: Precision, Recall, F1-score
* Suporta avaliação em lote e comparação A/B

**Uso:**
```python
from evaluation.metrics import create_bertscore_evaluator

evaluator = create_bertscore_evaluator(
    model_type="bert-base-multilingual-cased",
    lang="pt"
)

result = evaluator.evaluate_rag_answer(
    candidate="Dependentes podem ser declarados...",
    reference="Dependentes devem ser declarados...",
    contexts=chunks_recuperados
)
# Retorna: precision, recall, f1, context_alignment
```

### C) Métricas RAG-específicas (RAGAS)

**Módulo:** `src/evaluation/metrics/ragas_metrics.py`

Implementa métricas especializadas para sistemas RAG usando a biblioteca RAGAS.

**Métricas de Geração:**
* **Faithfulness**: Fidelidade ao contexto (evita alucinações)
* **Answer Relevancy**: Relevância da resposta à pergunta
* **Answer Correctness**: Correção factual (requer ground truth)
* **Answer Similarity**: Similaridade semântica com ground truth

**Métricas de Retrieval:**
* **Context Precision**: Documentos relevantes bem ranqueados
* **Context Recall**: Cobertura do conhecimento necessário
* **Context Entity Recall**: Recuperação de entidades-chave

**Configuração via .env:**
```bash
# Suporta Google Gemini e OpenAI
RAGAS_LLM_PROVIDER=gemini
RAGAS_API_KEY=sua_chave_aqui
```

**Uso:**
```python
from evaluation.metrics import create_ragas_evaluator

evaluator = create_ragas_evaluator(verbose=True)

metrics = evaluator.evaluate(
    questions=["Como declarar dependentes?"],
    answers=[resposta_gerada],
    contexts=[chunks_recuperados],
    ground_truths=["Dependentes devem..."]
)
# Retorna: faithfulness, answer_relevancy, context_precision, etc.
```

**Compatibilidade de Modelos (2026):**
* **Gemini**: `gemini-2.5-flash` (LLM), `models/gemini-embedding-001` (embeddings)
* **OpenAI**: `gpt-3.5-turbo` ou `gpt-4`

## 6.2 Métricas Comparativas

**Módulo:** `src/evaluation/metrics/comparative.py`

Para testes A/B entre diferentes configurações:

```python
from evaluation.metrics import ComparativeEvaluator

evaluator = ComparativeEvaluator()

# Comparar dois modelos
comparison = evaluator.compare_models(
    model_a_results=resultados_modelo_a,
    model_b_results=resultados_modelo_b,
    reference=ground_truth
)
# Retorna: win_rate_a, win_rate_b, tie_rate, significance
```

## 6.3 Infraestrutura de Testes

**Módulo:** `src/evaluation/experiments/experiment_runner.py`

### Experiment Runner

Sistema automatizado para execução de experimentos em larga escala:

**Funcionalidades:**
* Execução de múltiplas configurações em paralelo
* Logging detalhado de todas as execuções
* Agregação automática de resultados
* Exportação para JSON/CSV para análise posterior

**Uso:**
```python
from evaluation.experiments import ExperimentRunner

runner = ExperimentRunner(
    output_dir="experiments/results",
    log_level="INFO"
)

# Executar bateria de testes
results = runner.run_experiment(
    name="exp_001_gemini_vs_llama",
    queries=test_queries,
    configurations=[config_gemini, config_llama],
    repetitions=5  # 5 execuções por configuração
)

# Gerar relatório agregado
runner.generate_report(results)
```

### A/B Testing Framework

```python
from evaluation.experiments import ABTestRunner

ab_test = ABTestRunner()

# Teste estatístico entre duas versões
result = ab_test.run_test(
    variant_a=modelo_atual,
    variant_b=modelo_novo,
    test_set=queries_validacao,
    metrics=["bertscore_f1", "faithfulness", "response_time"]
)

# Retorna: statistical_significance, confidence_interval, recommendation
```

## 6.4 Factory Functions

Para facilitar a criação de avaliadores:

```python
from evaluation.metrics import (
    create_rag_evaluator,
    create_bertscore_evaluator,
    create_ragas_evaluator,
    create_comparative_evaluator
)

# Criação simplificada com configurações padrão
rag_eval = create_rag_evaluator()
bert_eval = create_bertscore_evaluator()
ragas_eval = create_ragas_evaluator(verbose=True)
comp_eval = create_comparative_evaluator()
```

## 6.5 Status da Implementação

| Componente | Status | Testes |
|-----------|---------|---------|
| Métricas RAG Base | ✅ Implementado | ✅ Testado |
| BERTScore | ✅ Implementado | ✅ 4 testes passando |
| RAGAS | ✅ Implementado | ✅ Validado com Gemini |
| Comparativas | ✅ Implementado | ✅ Testado |
| Experiment Runner | ✅ Implementado | ✅ Testado |

**Última atualização:** 15/02/2026

---

# 🛠️ 7. Tecnologias Utilizadas

## 7.1 Stack Implementado

### Linguagens e Frameworks
* **Python 3.12+**: Linguagem principal
* **FastAPI**: Framework web (planejado para API)
* **Pydantic**: Validação de dados e modelos

### Ingestão e Processamento
* **PyPDF**: Extração de PDFs
* **BeautifulSoup4**: Parsing HTML
* **python-docx**: Processamento de documentos Word

### Embeddings e Vetorização
* **sentence-transformers**: Geração de embeddings
* **torch**: Backend para modelos de ML

### Armazenamento Vetorial
* **ChromaDB**: Vector database (em uso)
* **Alternativas avaliadas**: Qdrant, Pinecone, Weaviate

### LLMs e Geração
* **Google Gemini**: Via `google-generativeai` e `langchain-google-genai`
* **OpenAI**: Suporte via `langchain-openai` (opcional)
* **LangChain**: Framework para orquestração de LLMs

### Avaliação e Métricas
* **bert-score**: Métricas semânticas com BERT
* **ragas**: Métricas específicas para RAG (v0.2.10+)
* **datasets**: Manipulação de datasets para avaliação
* **nltk**: Processamento de linguagem natural

### Guardrails
* **presidio-analyzer** e **presidio-anonymizer**: Detecção de PII
* **guardrails-ai**: Framework de validação

### Desenvolvimento e Testes
* **pytest**: Framework de testes
* **python-dotenv**: Gerenciamento de variáveis de ambiente
* **Jupyter**: Notebooks para análise

### Monitoramento (Planejado)
* **Prometheus**: Coleta de métricas
* **Grafana**: Visualização
* **Docker/Kubernetes**: Containerização e orquestração (futuro)

## 7.2 Modelos em Uso

### Embeddings
* **Primário**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
* **Alternativa**: `intfloat/multilingual-e5-large`

### LLMs de Avaliação
* **Gemini 2.5 Flash**: Para métricas RAGAS
* **BERT Multilingual**: Para BERTScore

### LLMs de Geração (Pipeline Principal)
* **Em desenvolvimento**: Gemini 1.5 Pro / GPT-4

---

# 🔐 8. Segurança e IA Responsável

### 8.1 Princípios

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
│   ├── 3_run_experiments.py
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

# 🏁 13. Status do Projeto

## Status Atual das Fases

| Fase | Status | Progresso | Último Update |
|------|--------|-----------|---------------|
| **Fase 1**: Setup e Infra | ✅ Concluído | 100% | Jan/2026 |
| **Fase 2**: Módulo de Ingestão | ✅ Concluído | 100% | Jan/2026 |
| **Fase 3**: Processamento e Segmentação | ✅ Concluído | 100% | Jan/2026 |
| **Fase 4**: Vetorização e Indexação | ✅ Concluído | 100% | Jan/2026 |
| **Fase 5**: Interface de Chat/CLI | ✅ Concluído | 100% | Jan/2026 |
| **Fase 6**: Otimização de busca (Híbrida) | ✅ Concluído | 100% | Fev/2026 |
| **Fase 7**: Guardrails e Filtros | ✅ Concluído | 100% | Fev/2026 |
| **Fase 8**: **Métricas e Avaliação** | ✅ **Concluído** | **100%** | **15/02/2026** |
| **Fase 9**: **Pipeline RAG Completo** | ✅ **Concluído** | **100%** | **15/02/2026** |
| **Fase 10**: Experimentos e Dashboards | 🔄 Em Andamento | 0% | - |

## Fase 8 - Métricas e Avaliação ✅

### Componentes Implementados

✅ **Métricas Base RAG** (`rag_metrics.py`)
- Tempo de resposta
- Tamanho do contexto
- Tokens recuperados

✅ **BERTScore** (`bertscore.py`)
- Precision, Recall, F1
- Suporte multilíngue (PT)
- 4 testes unitários passando

✅ **RAGAS** (`ragas_metrics.py`)
- 7 métricas RAG-específicas
- Integração com Gemini 2.5 Flash
- Configuração via .env
- Validado em produção

✅ **Métricas Comparativas** (`comparative.py`)
- Win rate entre modelos
- Testes A/B
- Análise estatística

✅ **Experiment Runner** (`experiment_runner.py`)
- Execução automatizada
- Logging detalhado
- Agregação de resultados

## Fase 9 - Pipeline RAG Completo ✅

### Componentes Implementados

✅ **RAG Pipeline** (`src/pipeline/rag_pipeline.py`)
- Integração completa de todos os módulos
- Métodos: ingest_documents(), query(), batch_query()
- Cache semântico para otimização
- Error handling e logging estruturado
- Suporte a avaliação automática

✅ **Testes Unitários** (`tests/unit/test_rag_pipeline.py`)
- 18 testes cobrindo todos os métodos
- Mocks para componentes externos
- Validação de fluxos de erro

✅ **Testes de Integração** (`tests/integration/test_rag_pipeline_integration.py`)
- Testes end-to-end do pipeline completo
- Validação de ingestão e query
- Testes de cache e batch processing
- Validação de logging e estatísticas

### Funcionalidades Principais

**Pipeline de Ingestão:**
1. Extração (PDF/HTML)
2. Limpeza de texto
3. Chunking estrutural
4. Geração de embeddings
5. Indexação no ChromaDB

**Pipeline de Query:**
1. Validação de entrada (guardrails)
2. Verificação de cache
3. Retrieval híbrido
4. Geração com LLM
5. Validação de saída
6. Avaliação automática (opcional)

### Próximos Passos

**Fase 10 - Experimentos e Dashboards:**
1. Preparar dataset de teste (30-50 perguntas IRPF)
2. Executar Experimento 1: RAG vs Sem RAG
3. Executar Experimento 2: LLM Grande vs Pequeno+RAG
4. Executar Experimento 3: Estratégias de Chunking
5. Executar Experimento 4: Retrieval Dense vs Híbrido
6. Análise estatística e geração de relatórios

**Última atualização:** 15/02/2026

---

# 📚 14. Referências Técnicas

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
````
