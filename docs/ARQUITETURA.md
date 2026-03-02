# 🦁 LION - Arquitetura Técnica v3.0

> Documentação detalhada da implementação RAG. Para visão geral, ver [README.md](../README.md)

## Estrutura dos Documentos Markdown

### Hierarquia da Legislação Brasileira (LC 95/98)

Os documentos processados seguem **10 níveis hierárquicos** conforme Lei Complementar 95/98:

#### Estrutura de Headings (Níveis 1-6)

| Nível | Markdown | Elemento | Exemplo |
|-------|----------|----------|---------|
| 1 | `#` | **Título do Decreto/Lei** | `# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018` |
| 2 | `##` | **Preâmbulo/ANEXO** | `## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA` |
| 3 | `###` | **LIVRO** | `### LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS` |
| 4 | `####` | **TÍTULO** | `#### TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS` |
| 5 | `#####` | **CAPÍTULO** | `##### CAPÍTULO I - DOS CONTRIBUINTES` |
| 6 | `######` | **SEÇÃO** | `###### Seção I - Da incidência` |

#### Estrutura de Listas (Níveis 7-10)

| Nível | Markdown | Elemento | Exemplo |
|-------|----------|----------|---------|
| 7 | `*` | **Subtítulo/SUBSEÇÃO/ARTIGO** | `* Disposições gerais`<br>`* **Subseção única**`<br>`  * Art. 677.` |
| 8 | `  -` | **Parágrafo (§)** | `  - **§ 1º** São também contribuintes...` |
| 9 | `    -` | **Inciso** | `    - I - de qualquer um dos pais` |
| 10 | `      -` | **Alínea** | `      - a) rendimentos do trabalho` |

**⚠️ Observação importante**: Artigos aparecem no **nível 7** com indentação especial (`  * Art. X.`) para diferenciá-los de subtítulos (`* Subtítulo`). Subseções são renderizadas em negrito: `* **Subseção I**`.

#### Regras de Combinação de Títulos

O extrator combina automaticamente elementos estruturais vazios consecutivos:

```markdown
# Antes (HTML)
<p>LIVRO III</p>
<p>DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS</p>

# Depois (Markdown)
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
```

**Casos especiais de combinação:**
- `LIVRO/TÍTULO/CAPÍTULO X` + `DA/DO/DAS/DOS ...` → Combinados com hífen
- `Seção I` + `Da incidência` → `###### Seção I - Da incidência`
- `Disposições gerais` → Permanece como subtítulo separado (`* Disposições gerais`)

#### Exemplo Hierárquico Completo

```markdown
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE
##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA
###### Seção I - Da incidência
* Disposições gerais
  * Art. 677.

Os rendimentos de que trata este Capítulo ficam sujeitos à incidência...

  - **§ 1º** O imposto de que trata este artigo será calculado...

    - I - para o ano-calendário de 2010...
    
      - a) até R$ 1.499,15: isento
```

### Estrutura do Arquivo Markdown

Cada documento processado contém três seções principais:

#### 1. Metadados do Documento

Informações sobre o processamento (linhas 1-20):

```markdown
# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018

<details>
<summary>📋 Metadados do Documento</summary>

- **Arquivo**: `D9580.html`
- **Padrão detectado**: planalto
- **Processado em**: 02/03/2026 18:30
</details>
```

#### 2. Esquema Navegável (Collapsible)

Estrutura hierárquica completa para navegação rápida (linhas ~20-1500):

```markdown
<details>
<summary>📋 Esquema da Legislação</summary>

# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018
## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA
## Art. 1º
## Art. 2º
### LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS
#### TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS
##### CAPÍTULO I - DOS CONTRIBUINTES
  * Art. 3º
  * Art. 4º
...
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE
##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA
###### Seção I - Da incidência
* Disposições gerais
  * Art. 677
  * Art. 678
...
</details>
```

**Conteúdo do esquema:**
- ✅ Todos os elementos estruturais (LIVRO, TÍTULO, CAPÍTULO, SEÇÃO, SUBSEÇÃO)
- ✅ Todos os artigos (apenas cabeçalho: `Art. 677`)
- ✅ Subtítulos descritivos (`Disposições gerais`, `Adiantamentos de rendimentos`)
- ❌ Parágrafos (§), incisos e alíneas (aparecem apenas no corpo)

**Utilidade:**
- Navegação rápida da estrutura legislativa
- Identificação de artigos relevantes sem scroll
- Visualização da hierarquia completa em formato compacto

#### 3. Corpo do Documento (Texto Normativo)

Conteúdo completo com toda a hierarquia (linhas 1500+):

```markdown
---

## 📖 Texto Normativo

## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA

## Art. 1º

Este Decreto regulamenta a tributação...

## Art. 2º

Para fins do disposto neste Decreto...

### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS


#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE


##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA


###### Seção I - Da incidência


* Disposições gerais


  * Art. 677.

Os rendimentos de que trata este Capítulo ficam sujeitos à incidência do imposto sobre a renda na fonte calculado em reais, de acordo com as seguintes tabelas progressivas mensais (Lei nº 11.482, de 2007, art. 1º caput , incisos IV a VIII) :

      - I - para o ano-calendário de 2010 e para os meses de janeiro a março do ano-calendário de 2011:


      - II - para os meses de abril a dezembro do ano-calendário de 2011:


  - **§ 1º** O imposto de que trata este artigo será calculado sobre os rendimentos efetivamente recebidos em cada mês...

    - I - os rendimentos do trabalho assalariado, inclusive adiantamentos...
    
      - a) pagos por pessoa jurídica a outra pessoa jurídica;
```

**Conteúdo do corpo:**
- ✅ Estrutura hierárquica completa (10 níveis)
- ✅ Todo o texto normativo (artigos, parágrafos, incisos, alíneas)
- ✅ Formatação: parágrafos em negrito, indentação progressiva
- ✅ Referências cruzadas preservadas (ex: "art. 587")

### Regras de Renderização

#### Detecção Automática de Elementos

O extrator HTML (`src/ingestion/extractors/html_extractor.py`) aplica heurísticas para identificar elementos sem classe CSS:

```python
# Elementos com classe MsoNormal ou sem classe
if mapping is None or mapping == (0, "", "body"):
    if re.match(r"^\s*Art\.?\s*\d+", text):
        mapping = (6, "###### ", "article")  # Artigo
    elif re.match(r"^\s*LIVRO\s+", text):
        mapping = (1, "# ", "heading")       # LIVRO
    elif re.match(r"^\s*TÍTULO\s+", text):
        mapping = (2, "## ", "heading")      # TÍTULO
    elif re.match(r"^\s*CAPÍTULO\s+", text):
        mapping = (3, "### ", "heading")     # CAPÍTULO
    elif re.match(r"^\s*SEÇÃO\s+", text):
        mapping = (4, "#### ", "heading")    # SEÇÃO
    elif len(text) < 100 and text[0].isupper():
        mapping = (5, "##### ", "heading")   # Subtítulo descritivo
```

#### Combinação Inteligente de Títulos

Elementos estruturais vazios consecutivos são automaticamente combinados:

| Padrão | Resultado |
|--------|-----------|
| `LIVRO I` + `DA TRIBUTAÇÃO...` | `### LIVRO I - DA TRIBUTAÇÃO...` |
| `Seção I` + `Da incidência` | `###### Seção I - Da incidência` |
| `Seção I - Da incidência` + `Disposições gerais` | **Não combina** (mantém separados) |

**Lógica de combinação:**
1. Se `current.title` já contém " - ", só combina `next.title` se começar com `DA/DO/DAS/DOS`
2. Preserva o nível hierárquico do primeiro elemento (`current.level`)
3. Não combina textos descritivos curtos que devem ser subtítulos separados

### Exemplo Completo de Documento Processado

📄 **Arquivo de referência**: [D9580_processed.md](../data/processed/markdown/legislation/D9580_processed.md)

**Estatísticas:**
- **Tamanho**: 196.736 palavras, 24.530 linhas
- **Estrutura**: Decreto nº 9.580/2018 (Regulamento do Imposto de Renda - RIR)
- **Hierarquia**: 10 níveis completos
- **Elementos**: 
  - 3 Livros (LIVRO I, II, III)
  - 14 Títulos
  - 125+ Capítulos
  - 200+ Seções e Subseções
  - 1.500+ Artigos
  - Milhares de parágrafos, incisos e alíneas

**Navegação no esquema** (linhas 1-1400):
```markdown
<details>
<summary>📋 Esquema da Legislação</summary>

# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018
## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA
## Art. 1º
...
### LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS
#### TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS
##### CAPÍTULO I - DOS CONTRIBUINTES
  * Art. 3º
...
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE
##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA
###### Seção I - Da incidência
* Disposições gerais
  * Art. 677
  * Art. 678
  * Art. 679
  * Art. 680
###### Seção II - Dos rendimentos do trabalho
* **Subseção I - Do trabalho assalariado**
* Pagos por pessoa física ou jurídica
  * Art. 681
...
</details>
```

**Corpo do documento** (linhas 1400+):
- Texto normativo completo com todos os 10 níveis hierárquicos
- Formatação preservada: parágrafos em negrito, indentação progressiva
- Referências cruzadas mantidas (ex: "conforme art. 587")
- Citações de leis e decretos preservadas

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

**Versão**: 3.1 | **Autor**: Ronen Rodrigues Silva Filho | **Última atualização**: 02/03/2026

**Changelog v3.1:**
- Expandida seção de hierarquia com tabelas detalhadas dos 10 níveis
- Adicionadas regras de combinação de títulos e detecção automática
- Melhorada documentação do esquema navegável vs corpo do documento
- Incluídos exemplos práticos de cada nível hierárquico
