# 🦁 LION - Arquitetura Técnica v3.0

> Documentação detalhada da implementação RAG. Para visão geral, ver [README.md](../README.md)

## Estrutura dos Documentos Markdown

### Hierarquia da Legislação Brasileira (LC 95/98)

Os documentos processados seguem 10 níveis hierárquicos:

**Níveis 1-6 (Headings `#` a `######`)**:
1. `#` **Título do Decreto/Lei** - Ex: "DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018"
2. `##` **Preâmbulo** - Artigos antes do corpo principal (Art. 1º-5º) ou ANEXO
3. `###` **Livro** - Ex: "LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS"
4. `####` **Título** - Ex: "TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS"
5. `#####` **Capítulo** - Ex: "CAPÍTULO I - DOS CONTRIBUINTES"
6. `######` **Seção/Artigo** - Ex: "Seção I - Dos menores" ou "Art. 1º"

**Níveis 7-10 (Listas `*` e `-`)**:
7. `*` **Subseção/Artigo RIR** - Ex: "* **Art. 453**" ou "* **Subseção única - Dos alimentos**"
8. `  -` **Parágrafo (§)** - Ex: "  - **§ 1º** São também contribuintes..."
9. `    -` **Inciso** - Ex: "    - I - de qualquer um dos pais"
10. `      -` **Alínea** - Ex: "      - a) rendimentos do trabalho"

### Estrutura do Arquivo Markdown

**1. Metadados** (linhas 1-16):
```markdown
---
arquivo: D9580_processed.md
padrão detectado: planalto
processado em: 2026-03-02 16:52:12
---
```

**2. Esquema Collapsible** (linhas 17-1500+):
```markdown
<details>
<summary>📋 Esquema da Legislação</summary>

# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018
## Art. 1º
## Art. 2º
### LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS
#### TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS
* Art. 1º
* Art. 2º
...
</details>
```
- Mostra **apenas títulos estruturais e artigos**
- **Não inclui**: parágrafos (§), incisos, alíneas
- Permite navegação rápida da estrutura legal

**3. Corpo do Documento** (linhas 1500+):
```markdown
## 📖 Texto Normativo

## Art. 1º
Texto do artigo...

* **§ 1º** Texto do parágrafo...

  - I - Texto do inciso...
  
    - a) Texto da alínea...
```
- Contém **todo o conteúdo** com hierarquia completa
- Parágrafos, incisos e alíneas aparecem dentro dos artigos

### Regras de Renderização

- **Níveis 1-6**: Usam headings markdown (`#` a `######`)
- **Nível 7+**: Usam listas (`*` e `-` com indentação) para compatibilidade com renderizadores
- **Artigos**: Sem links de âncora, apenas número (Ex: "Art. 453" não "Art. 453 {#art-453}")
- **Combinação de títulos**: "LIVRO I" + "DA TRIBUTAÇÃO" → "LIVRO I - DA TRIBUTAÇÃO"

## Componentes Core

### 1. Ingestion Pipeline

**Módulos**: `src/ingestion/`
- **Extrator**: PDF/HTML → texto (PyMuPDF, BeautifulSoup)
- **Chunker**: Segmentação estrutural com detecção de contexto
- **Embedder**: Google Gemini (`models/gemini-embedding-001`, 3072-dim)
- **Indexer**: ChromaDB com metadados (tipo, fonte, artigo)

**Script**: `scripts/2_ingest_processed_documents.py`

### 2. Retrieval Pipeline

**Módulos**: `src/retrieval/`
- **DenseRetriever**: Similarity search (cosine)
- **BM25Retriever**: Sparse retrieval (rank-bm25)
- **HybridRetriever**: RRF fusion (configurable weights)

**Configurações testadas**:
- k ∈ {3, 5, 10}
- dense_weight ∈ {0.5, 0.7}, bm25_weight ∈ {0.3, 0.5}

### 3. Generation Pipeline

**Módulos**: `src/generation/`
- **LLMClient**: Interface unificada (Groq, Gemini, OpenAI, Local(Ollama))
- **PromptBuilder**: Few-shot + RAG context injection
- **Guardrails**: Validação PII, scope, citation

**Prompt Structure**:
```
[SISTEMA] Você é assistente IRPF...
[FEW-SHOT] {exemplo pergunta 30}
[CONTEXTO] {k chunks recuperados}
[PERGUNTA] {user query}
```

### 4. Evaluation Pipeline

**Módulos**: `src/evaluation/`
- **BERTScoreEvaluator**: microsoft/deberta-xlarge-mnli
- **RAGASEvaluator**: answer_relevancy, faithfulness, context_precision, context_recall
- **CustomMetrics**: latency, tokens, num_chunks

**Script**: `scripts/4_analyze_results.py`

## Dependências Críticas

> ⚠️ **Versões oficiais**: Veja `requirements.txt` na raiz do projeto


**Modelos Utilizados**:
- **LLM**: `llama-3.1-8b-instant` via Groq API (experimentos)
- **LLM**: `gemini-2.0-flash-exp` via Google AI (configuração padrão `.env`)
- **Embeddings**: `models/gemini-embedding-001` (Google, 3072-dim) ou `models/text-embedding-004` (768-dim, `.env`)
- **BERTScore**: `microsoft/deberta-xlarge-mnli` (304M params, português)

## Arquitetura de Código

```
src/
├── ingestion/
│   ├── extractors/         # PDFExtractor, HTMLExtractor
│   ├── chunkers/           # StructuralChunker, FixedChunker
│   └── embedders/          # NomicEmbedder
├── retrieval/
│   ├── dense_retriever.py  # ChromaDB similarity
│   ├── bm25_retriever.py   # rank-bm25
│   └── hybrid_retriever.py # RRF fusion
├── generation/
│   ├── llm_client.py       # Factory: Groq, Gemini, OpenAI
│   └── prompts.py          # PromptBuilder com templates
├── evaluation/
│   └── metrics/
│       ├── bertscore.py    # BERTScoreEvaluator
│       └── ragas.py        # RAGASEvaluator
└── pipeline/
    └── rag_pipeline.py     # RAGPipeline (orquestrador)

scripts/
├── 3_run_experiments.py    # ExperimentRunner (13 configs)
└── 4_analyze_results.py    # ResultAnalyzer (markdown reports)
```

## Detalhes de Avaliação

**BERTScore** (implementação real em `src/evaluation/metrics/bertscore.py`):
```python
from bert_score import score as bert_score

# Inicialização
evaluator = BERTScoreEvaluator(
    model_type='microsoft/deberta-xlarge-mnli',
    lang='pt',
    device=None  # auto-detect cuda/cpu
)

# Avaliação
P, R, F1 = bert_score(
    cands=[generated_answer],
    refs=[ground_truth],
    model_type='microsoft/deberta-xlarge-mnli',
    lang='pt',
    batch_size=64
)
```

**RAGAS** (via LangChain):
```python
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,     # 0-1: relevância da resposta
    faithfulness,         # 0-1: fidelidade aos chunks
    context_precision,    # 0-1: ranking dos chunks
    context_recall        # 0-1: cobertura do ground truth
)
```

**Agregação**: mean, median, std, min, max por experimento (arquivo `*_summary_YYYYMMDD_HHMMSS.json`)

## Configurações Experimentais

**Baseline** (sem RAG):
```python
{
    'use_rag': False, 
    'use_few_shot': False,  # baseline puro
    'llm': 'groq:llama-3.1-8b-instant'
}
```

**RAG Variations** (12 configs):
```python
for k in [3, 5, 10]:
    for method in ['dense', 'bm25', 'hybrid']:
        for weights in [(0.7, 0.3), (0.5, 0.5)]:
            config = {
                'use_rag': True,
                'retrieval_method': method,
                'k': k,
                'dense_weight': weights[0],
                'bm25_weight': weights[1],
                'use_few_shot': True
            }
```

**Dataset**: 30 perguntas IRPF (questão 30 = few-shot, questões 1-29 = teste)

**Resultados**: `experiments/results/analysis/RELATORIO_ANALISE_model_comparison_*.md`

## Decisões Arquiteturais

### Por que ChromaDB?
- Embedding local (sem latência de API)
- Metadados ricos (filtros por tipo, fonte, artigo)
- Simplicidade (sem infraestrutura adicional)

### Por que Groq?
- Latência ultra-baixa (~800ms vs ~3s Gemini)
- API compatível OpenAI
- Custo competitivo

### Por que Hybrid Retrieval?
- Dense: captura similaridade semântica
- BM25: captura termos técnicos exatos ("art. 3º", "IN 2.255")
- Fusion: combina vantagens via RRF

### Por que Few-Shot?
- 1 exemplo (questão 30) reduz variância de resposta
- Melhora estrutura (citação de fontes)
- Custo: +500 tokens por query

## Otimizações Implementadas

1. **Cache de embeddings**: Evita recálculo em queries repetidas
2. **Batch processing**: Avaliação paralela (5 métricas simultâneas)
3. **Logging estruturado**: Timestamps + níveis (INFO, ERROR)
4. **Result versioning**: `_YYYYMMDD_HHMMSS.json` evita sobrescrita

## 📚 Referências e Leituras Recomendadas

### Papers
1. **RAG**: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
2. **Lost in the Middle**: Como LLMs usam contextos longos (Liu et al., 2023)
3. **RAGAS**: Framework de avaliação para RAG (Es et al., 2023)


## Limitações Conhecidas

- **Context window**: 8K tokens (Groq) limita k_max
- **BERTScore latency**: ~6s por avaliação (DeBERTa-XL)
- **Context recall baixo**: Ground truths sintéticos não capturam chunks
- **PII detection**: Regex básico (não NER)

---

**Versão**: 3.0 | **Autor**: Ronen Rodrigues Silva Filho | **Data**: 16/02/2026
