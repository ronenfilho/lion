# 🛠️ LION - Guia Prático de Implementação

## 📋 Roadmap de Implementação Detalhado

Este guia fornece um passo a passo prático para implementar a arquitetura RAG do projeto LION.

**📊 Status Atual:** 94% Completo (33/35 tarefas)
- ✅ **Fase 4 (Ingestão):** 100% completa - Pipeline unificado funcionando
- ✅ **Fase 10.1 e 10.2:** Dataset criado (30 Q&A) + Lei 15.270 ingerida (36 chunks)
- 🎯 **Próximo:** Fase 10.3 - Executar Experimentos Comparativos

---

## 🎯 Fase 1: Setup Inicial (Semana 1)

### 1.1 Preparação do Ambiente

```bash
# Criar estrutura de diretórios
mkdir -p lion/{data/{raw,processed,embeddings},src/{ingestion,retrieval,generation,evaluation,guardrails,monitoring,utils},experiments/{configs,results/{raw,metrics},notebooks},tests/{unit,integration,fixtures},app/{api,ui},config,logs,docs,scripts}

# Inicializar git
cd lion
git init
git add .
git commit -m "Initial project structure"

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependências base
pip install --upgrade pip
```

### 1.2 Arquivo `requirements.txt`

```txt
# Core RAG
langchain==0.1.0
langchain-community==0.0.10
langchain-openai==0.0.5
llama-index==0.9.0

# Embeddings & Vector Stores
chromadb==0.4.22
sentence-transformers==2.3.1
faiss-cpu==1.7.4

# LLM Providers
openai==1.10.0
anthropic==0.18.0
google-generativeai==0.3.2

# Document Processing
pymupdf==1.23.8
pymupdf4llm==0.0.5
beautifulsoup4==4.12.3
unstructured==0.12.0
python-docx==1.1.0

# Evaluation
ragas==0.1.0
bert-score==0.3.13
rouge-score==0.1.2

# API & Web
fastapi==0.109.0
uvicorn==0.27.0
streamlit==1.30.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Monitoring & Logging
prometheus-client==0.19.0
python-json-logger==2.0.7

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
tqdm==4.66.1
numpy==1.26.3
pandas==2.2.0
```

### 1.3 Configuração `.env.example`

```bash
# LLM API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Vector Store
CHROMA_PERSIST_DIR=./data/embeddings/chroma_db

# Embeddings
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072

# Retrieval
TOP_K=5
SIMILARITY_THRESHOLD=0.7
USE_RERANKING=true
HYBRID_ALPHA=0.7

# Generation
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.2
MAX_TOKENS=800

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true

# Cache
ENABLE_CACHE=true
CACHE_TTL=3600
```

---

## 🔧 Fase 2: Implementação Core (Semanas 2-4)

### 2.1 Módulo de Ingestão

#### `src/ingestion/pdf_extractor.py`

```python
import pymupdf4llm

class PDFExtractor:
    """Extração de PDF mantendo estrutura"""
    
    def extract(self, pdf_path: str) -> dict:
        """
        Extrai texto preservando hierarquia
        
        Returns:
            {
                'text': str,
                'metadata': dict,
                'structure': list  # Artigos, parágrafos, etc
            }
        """
        # Usar pymupdf4llm para manter estrutura markdown
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        return {
            'text': md_text,
            'metadata': self._extract_metadata(pdf_path),
            'structure': self._parse_structure(md_text)
        }
    
    def _parse_structure(self, md_text: str) -> list:
        """Parse estrutura hierárquica do documento legal"""
        # Implementar parser específico para estrutura normativa
        pass
```

#### `src/ingestion/chunking/structural_chunker.py`

```python
from typing import List, Dict
import re

class StructuralChunker:
    """Chunking respeitando estrutura legal"""
    
    def __init__(self, max_chunk_size: int = 800):
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, document: dict) -> List[Dict]:
        """
        Segmenta documento por unidades normativas
        
        Hierarquia: Lei > Capítulo > Artigo > Parágrafo > Inciso
        """
        chunks = []
        structure = document['structure']
        
        for artigo in structure:
            # Criar chunk por artigo
            chunk = self._create_chunk(artigo, document['metadata'])
            
            # Se muito grande, subdivide
            if len(chunk['content']) > self.max_chunk_size:
                chunks.extend(self._split_large_article(artigo))
            else:
                chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, artigo: dict, doc_metadata: dict) -> dict:
        """Cria chunk com conteúdo e metadados ricos"""
        return {
            'content': artigo['full_text'],
            'metadata': {
                **doc_metadata,
                'tipo': 'artigo',
                'numero_artigo': artigo['numero'],
                'tem_paragrafos': len(artigo.get('paragrafos', [])) > 0,
                'tem_incisos': len(artigo.get('incisos', [])) > 0,
            },
            'embedding': None  # Será preenchido depois
        }
```

### 2.2 Módulo de Retrieval

#### `src/retrieval/hybrid_retriever.py`

```python
from typing import List
import numpy as np
from rank_bm25 import BM25Okapi

class HybridRetriever:
    """Retrieval híbrido: Dense (embeddings) + Sparse (BM25)"""
    
    def __init__(
        self,
        vector_store,
        documents: List[str],
        alpha: float = 0.7,  # Peso para dense search
        top_k: int = 5
    ):
        self.vector_store = vector_store
        self.alpha = alpha
        self.top_k = top_k
        
        # Inicializar BM25
        tokenized_docs = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        self.documents = documents
    
    def retrieve(self, query: str, filters: dict = None) -> List[dict]:
        """
        Busca híbrida com RRF (Reciprocal Rank Fusion)
        """
        # 1. Dense retrieval (embeddings)
        dense_results = self.vector_store.similarity_search(
            query,
            k=self.top_k * 2,
            filter=filters
        )
        
        # 2. Sparse retrieval (BM25)
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        sparse_results = self._get_top_bm25(bm25_scores, k=self.top_k * 2)
        
        # 3. Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(
            dense_results,
            sparse_results
        )
        
        return fused_results[:self.top_k]
    
    def _reciprocal_rank_fusion(
        self,
        dense_results: List,
        sparse_results: List,
        k: int = 60
    ) -> List:
        """
        RRF: score(d) = sum(1 / (k + rank(d)))
        """
        scores = {}
        
        # Score from dense
        for rank, result in enumerate(dense_results):
            doc_id = result['id']
            scores[doc_id] = scores.get(doc_id, 0) + self.alpha / (k + rank + 1)
        
        # Score from sparse
        for rank, result in enumerate(sparse_results):
            doc_id = result['id']
            scores[doc_id] = scores.get(doc_id, 0) + (1 - self.alpha) / (k + rank + 1)
        
        # Sort by score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return [{'id': doc_id, 'score': score} for doc_id, score in sorted_docs]
```

### 2.3 Módulo de Generation

#### `src/generation/prompt_templates.py`

```python
from string import Template

SYSTEM_PROMPT = """Você é um assistente especializado em IRPF (Imposto de Renda Pessoa Física).

REGRAS OBRIGATÓRIAS:
1. BASE suas respostas EXCLUSIVAMENTE nos documentos fornecidos abaixo
2. NUNCA invente informações ou cite artigos não mencionados no contexto
3. Se a informação não estiver nos documentos, diga: "Não encontrei essa informação nas fontes oficiais disponíveis"
4. SEMPRE cite a fonte específica (ex: "Conforme IN RFB 2.255/2025, art. 12")
5. Use linguagem clara e acessível, mas mantenha precisão técnica
6. Em caso de dúvida, seja conservador e indique buscar orientação profissional

CONTEXTO NORMATIVO:
$retrieved_chunks

IMPORTANTE: As informações acima são a ÚNICA fonte de verdade. Não use conhecimento prévio do modelo."""

USER_PROMPT_TEMPLATE = Template("""Pergunta: $user_question

Responda de forma fundamentada, citando os artigos/parágrafos relevantes das fontes fornecidas.""")

DISCLAIMER = """

⚠️ AVISO IMPORTANTE:
Esta resposta é meramente informativa e baseada em fontes oficiais disponíveis. 
Não constitui consultoria tributária ou jurídica. Para situações específicas, 
consulte um contador ou advogado tributarista."""

def build_prompt(query: str, chunks: List[dict]) -> str:
    """Monta prompt completo com contexto recuperado"""
    
    # Formatar chunks recuperados
    context = "\n\n---\n\n".join([
        f"[Fonte: {c['metadata']['source']} - {c['metadata']['tipo']}]\n{c['content']}"
        for c in chunks
    ])
    
    # Montar prompt
    system = Template(SYSTEM_PROMPT).substitute(retrieved_chunks=context)
    user = USER_PROMPT_TEMPLATE.substitute(user_question=query)
    
    return system, user
```

---

## 🧪 Fase 3: Implementação de Guardrails (Semana 5)

### `src/guardrails/input_validator.py`

```python
import re
from typing import Tuple

class InputValidator:
    """Validação de entrada antes de processar"""
    
    PII_PATTERNS = {
        'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
        'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    }
    
    INJECTION_PATTERNS = [
        "ignore previous instructions",
        "disregard your rules",
        "you are now",
        "pretend to be",
        "forget everything",
    ]
    
    def validate(self, query: str) -> Tuple[bool, str]:
        """
        Valida entrada
        
        Returns:
            (is_valid, error_message)
        """
        # 1. Tamanho
        if len(query) < 10:
            return False, "Pergunta muito curta. Por favor, seja mais específico."
        
        if len(query) > 500:
            return False, "Pergunta muito longa. Por favor, seja mais conciso."
        
        # 2. Prompt injection
        query_lower = query.lower()
        for pattern in self.INJECTION_PATTERNS:
            if pattern in query_lower:
                return False, "Padrão de entrada inválido detectado."
        
        # 3. PII
        if self._contains_pii(query):
            return False, "Por favor, não inclua CPF, CNPJ, email ou outros dados pessoais na sua pergunta."
        
        return True, ""
    
    def _contains_pii(self, text: str) -> bool:
        """Detecta presença de dados pessoais"""
        for pattern in self.PII_PATTERNS.values():
            if re.search(pattern, text):
                return True
        return False
```

### `src/guardrails/output_validator.py`

```python
import re
from typing import List, Tuple

class OutputValidator:
    """Validação de resposta antes de entregar"""
    
    def validate(
        self,
        response: str,
        retrieved_chunks: List[dict]
    ) -> Tuple[bool, str]:
        """
        Valida resposta do LLM
        
        Returns:
            (is_valid, validated_response)
        """
        # 1. Verificar citações
        cited_articles = self._extract_citations(response)
        available_articles = self._extract_available_articles(retrieved_chunks)
        
        for article in cited_articles:
            if article not in available_articles:
                return False, "Resposta cita artigos não presentes no contexto. Tente novamente."
        
        # 2. Comprimento mínimo
        if len(response) < 50:
            return False, "Resposta muito curta. Possivelmente incompleta."
        
        # 3. Adicionar disclaimer
        if "⚠️" not in response:
            from .prompt_templates import DISCLAIMER
            response += DISCLAIMER
        
        return True, response
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extrai citações de artigos da resposta"""
        # Regex para capturar: art. 12, artigo 12, Art 12, etc
        pattern = r'(?:art\.?|artigo)\s*(\d+)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [f"art_{m}" for m in matches]
    
    def _extract_available_articles(self, chunks: List[dict]) -> List[str]:
        """Extrai artigos disponíveis nos chunks"""
        articles = set()
        for chunk in chunks:
            if 'numero_artigo' in chunk['metadata']:
                articles.add(f"art_{chunk['metadata']['numero_artigo']}")
        return list(articles)
```

---

## 📊 Fase 4: Implementação de Evaluation (Semana 6)

### `src/evaluation/metrics/bertscore.py`

```python
from bert_score import score as bert_score

class BERTScoreEvaluator:
    """Avaliação de similaridade semântica"""
    
    def __init__(self, model_type: str = "microsoft/deberta-xlarge-mnli"):
        self.model_type = model_type
    
    def evaluate(
        self,
        predictions: List[str],
        references: List[str]
    ) -> dict:
        """
        Calcula BERTScore
        
        Returns:
            {
                'precision': float,
                'recall': float,
                'f1': float
            }
        """
        P, R, F1 = bert_score(
            predictions,
            references,
            model_type=self.model_type,
            lang="pt",
            verbose=False
        )
        
        return {
            'precision': P.mean().item(),
            'recall': R.mean().item(),
            'f1': F1.mean().item()
        }
```

### `src/evaluation/experiments/experiment_runner.py`

```python
import json
from typing import List, Dict
from datetime import datetime
import numpy as np

class ExperimentRunner:
    """Executa experimentos comparativos"""
    
    def __init__(self, config: dict):
        self.config = config
        self.results = []
    
    def run_experiment(
        self,
        queries: List[str],
        ground_truth: List[str],
        rag_pipeline,
        runs_per_query: int = 5
    ):
        """
        Executa experimento com múltiplas repetições
        """
        for i, (query, truth) in enumerate(zip(queries, ground_truth)):
            print(f"Processing query {i+1}/{len(queries)}: {query[:50]}...")
            
            query_results = []
            
            for run in range(runs_per_query):
                # Executar RAG
                response = rag_pipeline.query(query)
                
                # Calcular métricas
                metrics = self._calculate_metrics(response, truth)
                
                # Salvar resultado
                result = {
                    'query_id': i,
                    'query': query,
                    'run_id': run,
                    'response': response['answer'],
                    'chunks_retrieved': response['chunks'],
                    'metrics': metrics,
                    'timestamp': datetime.now().isoformat(),
                    'config': self.config
                }
                
                query_results.append(result)
                self.results.append(result)
            
            # Calcular estatísticas agregadas
            self._save_query_statistics(i, query_results)
        
        return self.results
    
    def _calculate_metrics(self, response: dict, ground_truth: str) -> dict:
        """Calcula todas as métricas configuradas"""
        metrics = {}
        
        # BERTScore
        if 'bertscore' in self.config['metrics']:
            from ..metrics.bertscore import BERTScoreEvaluator
            evaluator = BERTScoreEvaluator()
            bertscore = evaluator.evaluate(
                [response['answer']],
                [ground_truth]
            )
            metrics['bertscore_f1'] = bertscore['f1']
        
        # RAGAS
        if 'faithfulness' in self.config['metrics']:
            # Implementar RAGAS metrics
            pass
        
        return metrics
    
    def _save_query_statistics(self, query_id: int, query_results: List[dict]):
        """Calcula média e desvio padrão das métricas"""
        scores = [r['metrics']['bertscore_f1'] for r in query_results]
        
        stats = {
            'query_id': query_id,
            'mean_score': np.mean(scores),
            'std_score': np.std(scores),
            'min_score': np.min(scores),
            'max_score': np.max(scores)
        }
        
        # Salvar
        with open(f'experiments/results/metrics/query_{query_id}_stats.json', 'w') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
```

---

## 🚀 Fase 5: Pipeline Completo (Semana 7)

### `src/rag_pipeline.py`

```python
class RAGPipeline:
    """Pipeline RAG completo"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # Inicializar componentes
        self.query_processor = QueryProcessor()
        self.retriever = HybridRetriever(...)
        self.reranker = Reranker() if config['use_reranking'] else None
        self.generator = LLMGenerator(...)
        self.input_validator = InputValidator()
        self.output_validator = OutputValidator()
        self.cache = SemanticCache() if config['enable_cache'] else None
        self.logger = RAGLogger()
    
    def query(self, user_query: str) -> dict:
        """
        Processa query completa
        
        Returns:
            {
                'answer': str,
                'chunks': List[dict],
                'metadata': dict
            }
        """
        start_time = time.time()
        
        # 1. Validar entrada
        is_valid, error = self.input_validator.validate(user_query)
        if not is_valid:
            return {'error': error}
        
        # 2. Verificar cache
        if self.cache:
            cached = self.cache.get(user_query)
            if cached:
                self.logger.log_cache_hit(user_query)
                return cached
        
        # 3. Processar query
        processed_query = self.query_processor.process(user_query)
        
        # 4. Retrieval
        chunks = self.retriever.retrieve(
            processed_query['query'],
            filters=processed_query.get('filters')
        )
        
        # 5. Re-ranking (opcional)
        if self.reranker:
            chunks = self.reranker.rerank(user_query, chunks)
        
        # 6. Gerar resposta
        answer = self.generator.generate(user_query, chunks)
        
        # 7. Validar saída
        is_valid, validated_answer = self.output_validator.validate(answer, chunks)
        if not is_valid:
            return {'error': 'Falha na validação da resposta'}
        
        # 8. Preparar resultado
        result = {
            'answer': validated_answer,
            'chunks': chunks,
            'metadata': {
                'latency_ms': (time.time() - start_time) * 1000,
                'num_chunks': len(chunks),
                'cache_hit': False
            }
        }
        
        # 9. Salvar em cache
        if self.cache:
            self.cache.set(user_query, result)
        
        # 10. Log
        self.logger.log_query(user_query, result)
        
        return result
```

---

## ✅ Checklist de Implementação - Status Atualizado

### 📊 Progresso Geral: 94% Completo (33/35 tarefas)

**Fases Completas:**
- ✅ Fase 1: Setup Inicial (6/6)
- ✅ Fase 2: Configuração (6/6)
- ✅ Fase 3: Ambiente Python (2/2)
- ✅ Fase 4: Ingestão (10/10) - **100%**
- 🔄 Fase 5: Retrieval (3/5) - 60%
- ✅ Fase 6: Geração (3/3)
- ✅ Fase 7: Guardrails (3/3)
- ✅ Fase 8: Avaliação (5/5)
- 🔄 Fase 9: Pipeline Completo (0/3)
- 🔄 Fase 10: Experimentos (2/5) - **40%**

```markdown
## ✅ Fase 1: Setup Inicial (100% - 6/6)
- [x] Estrutura de diretórios criada (30+ pastas)
- [x] requirements.txt criado (40+ dependências)
- [x] .env.example configurado
- [x] .gitignore criado
- [x] Git inicializado
- [x] Arquitetura e documentação completa (8 docs, ~3800 linhas)
📝 Commit: 9d6f6c6 - "docs: expandir arquitetura e criar estrutura inicial"

## ✅ Fase 2: Configuração do Sistema (100% - 6/6)
- [x] Sistema de configuração YAML implementado
- [x] Validação Pydantic (config.py com 8 classes)
- [x] config/default.yaml (configuração base)
- [x] config/development.yaml (ambiente dev)
- [x] config/production.yaml (ambiente prod)
- [x] Modelos trocados para Google (Gemini 2.0 Flash + text-embedding-004)
📝 Commit: ede83f1 - "feat: implementar sistema de configuração e estrutura base"

## ✅ Fase 3: Ambiente Python (100% - 2/2)
- [x] Ambiente virtual criado (venv)
- [x] Dependências instaladas compatíveis com Python 3.12
- [x] Integração .env → YAML implementada (prioridade: .env > {env}.yaml > default.yaml)
- [x] Sistema de configuração testado e validado ✓
📝 Commit: ede83f1 - "feat: implementar sistema de configuração e estrutura base"

## ✅ Fase 4: Ingestão de Dados (100% - 10/10)
- [x] src/ingestion/extractors/pdf_extractor.py (PyMuPDF + detecção estrutural)
- [x] src/ingestion/extractors/html_extractor.py (BeautifulSoup4 + encoding automático, tables + line breaks)
- [x] src/ingestion/extractors/text_cleaner.py (normalização + limpeza legal)
- [x] src/ingestion/chunking/structural_chunker.py (unified chunker com chunk_markdown() + chunk_pdf())
- [x] src/ingestion/embeddings_pipeline.py (gemini-embedding-001, 3072d)
- [x] src/ingestion/vector_store.py (ChromaDB com persistência, busca e filtros)
- [x] scripts/2_ingest_processed_documents.py (pipeline completo: load → chunk → embed → store)
- [x] scripts/2.1_show_chunk_stats.py + 2.2_show_chunks.py (visualização de chunks)
- [x] scripts/1_create_test_dataset.py (extração Q&A do Manual RFB)
- [x] experiments/datasets/manual_rfb_test.json (30 pares pergunta-resposta estruturados)
📝 Commit: 7da3c3e - "feat: implementa módulo de ingestão com extractors e chunkers"
📝 Commit: aac8d85 - "feat: adiciona embeddings pipeline com Google Gemini"
📝 Commit: 55abc1b - "feat: adiciona vector store com ChromaDB"
📝 Commit: a1e1023 - "feat(ingestion): unifica chunkers e implementa pipeline completo de ingestão"
✅ **Pipeline Testado**: 36 chunks criados de L15270_processed.md, embeddings 3072d, ChromaDB persistente

## ✅ Fase 5: Sistema de Retrieval (60% - 3/5)
- [x] src/retrieval/dense_retriever.py (busca vetorial com ChromaDB)
- [x] src/retrieval/bm25_retriever.py (busca por termos com tokenização legal)
- [x] src/retrieval/hybrid_retriever.py (RRF + weighted fusion, 70% dense / 30% BM25)
- [ ] src/retrieval/reranker.py (cross-encoder para reordenar resultados)
- [ ] Testar e comparar performance dos retrievers
📝 Commit: db17679 - "feat: implementa sistema de retrieval (dense, BM25, hybrid)"

## ✅ Fase 6: Geração de Respostas (100% - 3/3)
- [x] src/generation/llm_client.py (Google Gemini) - Commit: 549cabf
- [x] src/generation/prompts.py (templates especializados) - Commit: 549cabf
- [x] src/generation/output_parser.py (estruturação) - Commit: 549cabf

## ✅ Fase 7: Guardrails (100% - 3/3)
- [x] src/guardrails/pii_detector.py (regex patterns) - Commit: d199133
- [x] src/guardrails/input_validator.py (PII, prompt injection) - Commit: d199133
- [x] src/guardrails/output_validator.py (citações, relevância) - Commit: d199133

## ✅ Fase 8: Avaliação (100% - 5/5)
- [x] src/evaluation/metrics/rag_metrics.py (precision, recall, MRR, faithfulness, hallucination) - Commit: 01c505c
- [x] src/evaluation/metrics/comparative_metrics.py (ComparativeEvaluator, A/B testing) - Commit: 01c505c
- [x] src/evaluation/experiments/runner.py (automated experiment execution) - Commit: 01c505c
- [x] src/evaluation/metrics/bertscore.py (similaridade semântica BERT-based, bert-base-multilingual-cased)
- [x] src/evaluation/metrics/ragas_metrics.py (7 métricas RAG, integração Gemini 2.5 Flash, validado com score 1.000)
- [x] tests/evaluation/test_bertscore.py (4/4 testes passando)
- [x] Configuração .env para RAGAS (RAGAS_LLM_PROVIDER=gemini, embeddings configurados)
📝 Fase completa em: 15/02/2026

## ✅ Fase 9: Pipeline RAG Completo (100% - 3/3)
- [x] src/pipeline/rag_pipeline.py (integração completa - ingestion → retrieval → generation → evaluation)
- [x] tests/unit/test_rag_pipeline.py (18 testes unitários cobrindo todos os métodos)
- [x] tests/integration/test_rag_pipeline_integration.py (testes end-to-end do pipeline completo)
📝 Fase completa em: 15/02/2026

## 🔄 Fase 10: Experimentos (30% - 2/5)
- [x] **Etapa 10.1**: Criar dataset de teste ✅ (manual_rfb_test.json com 30 Q&A)
- [x] **Etapa 10.2**: Ingerir documentos processados ✅ (L15270_processed.md → 36 chunks no ChromaDB)
- [ ] **Etapa 10.3**: Executar experimentos comparativos (4 experimentos: dense vs BM25 vs hybrid)
- [ ] **Etapa 10.4**: Analisar resultados e calcular métricas (RAGAS, BERTScore)
- [ ] **Etapa 10.5**: Gerar relatórios e visualizações
```

---

## 🎯 PRÓXIMO PASSO RECOMENDADO

### ➡️ Fase 10.3: Executar Experimentos Comparativos

**✅ Status Atual:** 
- Dataset de teste criado: `experiments/datasets/manual_rfb_test.json` (30 Q&A estruturados)
- Lei 15.270 ingerida: 36 chunks no ChromaDB (coleção "irpf_2025")
- Pipeline de ingestão completo: `scripts/2_ingest_processed_documents.py`
- Ferramentas de visualização: `2.1_show_chunk_stats.py`, `2.2_show_chunks.py`

**🎯 Objetivo:** Executar experimentos comparativos para validar as hipóteses da pesquisa e medir o impacto de diferentes configurações do RAG.

#### **Tarefa Imediata: Implementar e Executar Experimentos**

**Experimentos Planejados:**

1. **Experimento 1: RAG vs Sem RAG**
   - **Config A**: Gemini sem RAG (baseline)
   - **Config B**: Gemini 2.5 Flash + RAG (dense retrieval)
   - **Objetivo**: Medir ganho de acurácia e redução de alucinações
   - **Métricas**: Faithfulness, Answer Relevancy, BERTScore F1

2. **Experimento 2: LLM Grande vs Pequeno+RAG**
   - **Config A**: Gemini 2.0 Flash (maior contexto, sem RAG)
   - **Config B**: Gemini 2.5 Flash + RAG
   - **Objetivo**: Validar se arquitetura RAG supera tamanho do modelo
   - **Métricas**: Fidelidade normativa, Custo-benefício (tokens)

3. **Experimento 3: Estratégias de Retrieval**
   - **Config A**: Dense retrieval (embeddings apenas)
   - **Config B**: BM25 retrieval (termos apenas)
   - **Config C**: Hybrid retrieval (70% dense + 30% BM25)
   - **Objetivo**: Melhor estratégia de busca para termos normativos
   - **Métricas**: Context Precision, Context Recall, MRR

4. **Experimento 4: Número de Chunks Retrieved**
   - **Config A**: k=3 chunks
   - **Config B**: k=5 chunks
   - **Config C**: k=10 chunks
   - **Objetivo**: Balancear contexto vs ruído
   - **Métricas**: Answer Relevancy, Context Utilization, Latência

**Pipeline de Execução:**

```bash
# 1. Criar script de experimentos
scripts/3_run_experiments.py

# 2. Executar cada configuração
python scripts/3_run_experiments.py --experiment rag_vs_no_rag
python scripts/3_run_experiments.py --experiment llm_size
python scripts/3_run_experiments.py --experiment retrieval_strategy
python scripts/3_run_experiments.py --experiment chunk_count

# 3. Analisar resultados
python scripts/3.1_analyze_results.py

# 4. Gerar relatórios
python scripts/3.2_generate_report.py
```

**Estrutura do Script de Experimentos:**

```python
# scripts/3_run_experiments.py
"""
Executa experimentos comparativos com diferentes configurações RAG
"""
import json
from pathlib import Path
from typing import Dict, List
import time

from src.pipeline.rag_pipeline import RAGPipeline
from src.evaluation.metrics.ragas_metrics import RAGASEvaluator
from src.evaluation.metrics.bertscore import BERTScoreEvaluator

class ExperimentRunner:
    def __init__(self, dataset_path: str):
        self.dataset = self._load_dataset(dataset_path)
        self.results_dir = Path('experiments/results/')
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_dataset(self, path: str) -> Dict:
        """Carrega dataset de teste"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def run_experiment(
        self, 
        experiment_name: str, 
        config: Dict
    ) -> Dict:
        """
        Executa experimento com configuração específica
        
        Args:
            experiment_name: Nome do experimento
            config: Configuração do RAG (retrieval_method, k, etc)
        
        Returns:
            Resultados agregados com métricas
        """
        print(f"\n{'='*60}")
        print(f"🧪 Experimento: {experiment_name}")
        print(f"{'='*60}\n")
        
        # Inicializar pipeline com configuração
        pipeline = RAGPipeline(config)
        
        # Inicializar avaliadores
        ragas_eval = RAGASEvaluator()
        bert_eval = BERTScoreEvaluator()
        
        results = []
        
        # Processar cada pergunta do dataset
        for i, qa in enumerate(self.dataset['questions'], 1):
            print(f"[{i}/{len(self.dataset['questions'])}] {qa['question'][:60]}...")
            
            start_time = time.time()
            
            # Query RAG
            response = pipeline.query(qa['question'])
            
            latency = (time.time() - start_time) * 1000
            
            # Calcular métricas
            metrics = {
                'latency_ms': latency,
                'num_chunks': len(response.get('chunks', [])),
            }
            
            # RAGAS metrics
            if config.get('use_rag', True):
                ragas_scores = ragas_eval.evaluate(
                    question=qa['question'],
                    answer=response['answer'],
                    contexts=[c['content'] for c in response['chunks']],
                    ground_truth=qa['ground_truth']
                )
                metrics.update(ragas_scores)
            
            # BERTScore
            bert_scores = bert_eval.evaluate(
                predictions=[response['answer']],
                references=[qa['ground_truth']]
            )
            metrics['bertscore_f1'] = bert_scores['f1']
            
            # Salvar resultado individual
            result = {
                'question_id': qa['id'],
                'question': qa['question'],
                'answer': response['answer'],
                'ground_truth': qa['ground_truth'],
                'metrics': metrics,
                'config': config
            }
            
            results.append(result)
        
        # Agregar métricas
        aggregated = self._aggregate_metrics(results)
        
        # Salvar resultados
        output_path = self.results_dir / f'{experiment_name}_results.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'experiment_name': experiment_name,
                'config': config,
                'aggregated_metrics': aggregated,
                'individual_results': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Resultados salvos: {output_path}")
        print(f"\n📊 Métricas Agregadas:")
        for metric, value in aggregated.items():
            print(f"   {metric}: {value:.4f}")
        
        return aggregated
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict:
        """Calcula média e desvio padrão das métricas"""
        import numpy as np
        
        metrics_dict = {}
        
        for result in results:
            for metric, value in result['metrics'].items():
                if metric not in metrics_dict:
                    metrics_dict[metric] = []
                metrics_dict[metric].append(value)
        
        aggregated = {}
        for metric, values in metrics_dict.items():
            aggregated[f'{metric}_mean'] = np.mean(values)
            aggregated[f'{metric}_std'] = np.std(values)
        
        return aggregated

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment', required=True, 
                       choices=['rag_vs_no_rag', 'llm_size', 
                               'retrieval_strategy', 'chunk_count'])
    parser.add_argument('--dataset', default='experiments/datasets/manual_rfb_test.json')
    
    args = parser.parse_args()
    
    runner = ExperimentRunner(args.dataset)
    
    # Definir configurações para cada experimento
    experiments = {
        'rag_vs_no_rag': [
            {
                'name': 'no_rag_baseline',
                'config': {'use_rag': False, 'llm': 'gemini-2.5-flash'}
            },
            {
                'name': 'rag_enabled',
                'config': {
                    'use_rag': True, 
                    'retrieval_method': 'dense',
                    'k': 5,
                    'llm': 'gemini-2.5-flash'
                }
            }
        ],
        'llm_size': [
            {
                'name': 'large_llm_no_rag',
                'config': {'use_rag': False, 'llm': 'gemini-2.0-flash'}
            },
            {
                'name': 'small_llm_with_rag',
                'config': {
                    'use_rag': True,
                    'retrieval_method': 'dense',
                    'k': 5,
                    'llm': 'gemini-2.5-flash'
                }
            }
        ],
        'retrieval_strategy': [
            {
                'name': 'dense_only',
                'config': {
                    'use_rag': True,
                    'retrieval_method': 'dense',
                    'k': 5
                }
            },
            {
                'name': 'bm25_only',
                'config': {
                    'use_rag': True,
                    'retrieval_method': 'bm25',
                    'k': 5
                }
            },
            {
                'name': 'hybrid',
                'config': {
                    'use_rag': True,
                    'retrieval_method': 'hybrid',
                    'dense_weight': 0.7,
                    'bm25_weight': 0.3,
                    'k': 5
                }
            }
        ],
        'chunk_count': [
            {
                'name': 'k3',
                'config': {'use_rag': True, 'retrieval_method': 'hybrid', 'k': 3}
            },
            {
                'name': 'k5',
                'config': {'use_rag': True, 'retrieval_method': 'hybrid', 'k': 5}
            },
            {
                'name': 'k10',
                'config': {'use_rag': True, 'retrieval_method': 'hybrid', 'k': 10}
            }
        ]
    }
    
    # Executar experimentos
    for exp_config in experiments[args.experiment]:
        runner.run_experiment(
            experiment_name=f"{args.experiment}_{exp_config['name']}",
            config=exp_config['config']
        )

if __name__ == '__main__':
    main()
```

**Tempo estimado:** 2-3 dias (implementação + execução + análise inicial)

**Após execução:** Fase 10.4 (análise de resultados) e Fase 10.5 (relatórios/visualizações)

---
```json
{
  "dataset_name": "lei_15270_qa_test",
  "version": "1.0",
  "created_at": "2026-02-15",
  "total_questions": 30,
  "questions": [
    {
      "id": "q001",
      "question": "Quem é obrigado a declarar o Imposto de Renda?",
      "ground_truth": "É obrigado a apresentar a Declaração de Ajuste Anual quem recebeu...",
      "category": "obrigatoriedade",
      "difficulty": "facil",
      "source": "Lei 15.270/2025, Art. 3º",
      "metadata": {
        "article": "3",
        "section": "obrigatoriedade"
      }
    }
  ]
}
```

**Pipeline de Criação:**

1. **Extração do PDF:**
   ```python
   from src.ingestion.extractors.pdf_extractor import PDFExtractor
   
   extractor = PDFExtractor()
   doc_data = extractor.extract('data/raw/lei_15270_2025.pdf')
   ```

2. **Script de Extração:** `scripts/create_test_dataset.py`
   ```python
   """
   Script para extrair perguntas e respostas da Lei 15.270
   e criar dataset de teste estruturado
   """
   import json
   from pathlib import Path
   from typing import List, Dict
   import re
   
   def extract_qa_pairs(text: str) -> List[Dict]:
       """
       Extrai pares de perguntas e respostas do texto.
       
       Estratégia:
       - Identificar padrões de perguntas (ex: linhas terminando com '?')
       - Capturar resposta até próxima pergunta ou seção
       - Extrair metadados (artigo, parágrafo, etc)
       """
       qa_pairs = []
       
       # Regex para identificar perguntas
       question_pattern = r'^(.+?\?)\s*$'
       
       # Processar texto linha por linha
       lines = text.split('\n')
       current_question = None
       current_answer = []
       
       for i, line in enumerate(lines):
           line = line.strip()
           if not line:
               continue
           
           # Detectar pergunta
           match = re.match(question_pattern, line, re.MULTILINE)
           if match:
               # Salvar Q&A anterior
               if current_question:
                   qa_pairs.append({
                       'question': current_question,
                       'answer': ' '.join(current_answer).strip()
                   })
               
               # Iniciar nova pergunta
               current_question = match.group(1)
               current_answer = []
           elif current_question:
               # Acumular resposta
               current_answer.append(line)
       
       # Adicionar última Q&A
       if current_question:
           qa_pairs.append({
               'question': current_question,
               'answer': ' '.join(current_answer).strip()
           })
       
       return qa_pairs
   
   def enrich_qa_metadata(qa_pairs: List[Dict]) -> List[Dict]:
       """
       Enriquece Q&A com metadados adicionais.
       """
       enriched = []
       
       for i, qa in enumerate(qa_pairs, 1):
           enriched.append({
               'id': f'q{i:03d}',
               'question': qa['question'],
               'ground_truth': qa['answer'],
               'category': classify_category(qa['question']),
               'difficulty': 'medio',  # Ajustar manualmente
               'source': 'Lei 15.270/2025',
               'metadata': extract_source_metadata(qa['answer'])
           })
       
       return enriched
   
   def classify_category(question: str) -> str:
       """Classifica pergunta em categoria"""
       keywords = {
           'obrigatoriedade': ['obrigado', 'obrigada', 'obrigatório'],
           'deducoes': ['dedução', 'deduzir', 'abater'],
           'dependentes': ['dependente', 'filho', 'cônjuge'],
           'rendimentos': ['rendimento', 'renda', 'salário'],
           'prazo': ['prazo', 'data', 'quando'],
           'penalidades': ['multa', 'penalidade', 'sanção']
       }
       
       question_lower = question.lower()
       for category, words in keywords.items():
           if any(word in question_lower for word in words):
               return category
       
       return 'outros'
   
   def extract_source_metadata(text: str) -> Dict:
       """Extrai metadados de fonte (artigos, parágrafos)"""
       metadata = {}
       
       # Buscar artigos
       art_match = re.search(r'art(?:igo)?\.?\s*(\d+)', text, re.IGNORECASE)
       if art_match:
           metadata['article'] = art_match.group(1)
       
       return metadata
   
   def main():
       # 1. Extrair PDF
       from src.ingestion.extractors.pdf_extractor import PDFExtractor
       
       pdf_path = 'data/raw/lei_15270_2025.pdf'
       extractor = PDFExtractor()
       
       print(f"📄 Extraindo {pdf_path}...")
       doc_data = extractor.extract(pdf_path)
       
       # 2. Extrair Q&A
       print("🔍 Extraindo pares de perguntas e respostas...")
       qa_pairs = extract_qa_pairs(doc_data['text'])
       print(f"   Encontrados: {len(qa_pairs)} pares Q&A")
       
       # 3. Enriquecer com metadados
       print("📊 Enriquecendo com metadados...")
       enriched_qa = enrich_qa_metadata(qa_pairs)
       
       # 4. Criar dataset estruturado
       dataset = {
           'dataset_name': 'lei_15270_qa_test',
           'version': '1.0',
           'created_at': '2026-02-15',
           'total_questions': len(enriched_qa),
           'source_document': 'Lei 15.270/2025',
           'questions': enriched_qa
       }
       
       # 5. Salvar JSON
       output_path = Path('experiments/datasets/lei_15270_test.json')
       output_path.parent.mkdir(parents=True, exist_ok=True)
       
       with open(output_path, 'w', encoding='utf-8') as f:
           json.dump(dataset, f, ensure_ascii=False, indent=2)
       
       print(f"\n✅ Dataset criado: {output_path}")
       print(f"   Total de perguntas: {len(enriched_qa)}")
       
       # 6. Estatísticas
       categories = {}
       for qa in enriched_qa:
           cat = qa['category']
           categories[cat] = categories.get(cat, 0) + 1
       
       print("\n📊 Distribuição por categoria:")
       for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
           print(f"   {cat}: {count}")
   
   if __name__ == '__main__':
       main()
   ```

3. **Validação Manual:**
   - Revisar 10-20% das Q&A extraídas
   - Ajustar dificuldades e categorias
   - Corrigir respostas truncadas ou incompletas

4. **Ingestão da Lei 15.270:**
   ```python
   # scripts/ingest_lei_15270.py
   from src.pipeline.rag_pipeline import create_rag_pipeline
   
   pipeline = create_rag_pipeline(verbose=True)
   
   result = pipeline.ingest_documents([
       'data/raw/lei_15270_2025.pdf'
   ])
   
   print(f"✅ Documentos processados: {result.documents_processed}")
   print(f"✅ Chunks indexados: {result.chunks_indexed}")
   ```

**Próximos Passos (após criação do dataset):**

**Fase 10.2 - Experimentos Comparativos:**

1. **Experimento 1: RAG vs Sem RAG** (Gemini)
   - Configuração A: Gemini sem RAG (baseline)
   - Configuração B: Gemini com RAG
   - Objetivo: Medir ganho de acurácia e redução de alucinações
   - Métricas: Faithfulness, Answer Relevancy, BERTScore F1

2. **Experimento 2: LLM Grande vs Pequeno+RAG**
   - Configuração A: Gemini Pro sem RAG
   - Configuração B: Gemini Flash + RAG
   - Objetivo: Validar se arquitetura supera tamanho do modelo
   - Métricas: Fidelidade normativa, Custo-benefício

3. **Experimento 3: Estratégias de Chunking**
   - Configuração A: Chunking fixo (800 tokens)
   - Configuração B: Chunking estrutural (artigos/parágrafos)
   - Objetivo: Melhor estratégia de segmentação
   - Métricas: Context Precision, Context Recall

4. **Experimento 4: Retrieval Dense vs Híbrido**
   - Configuração A: Dense retrieval (embeddings apenas)
   - Configuração B: Hybrid retrieval (70% dense + 30% BM25)
   - Objetivo: Impacto de BM25 em termos normativos
   - Métricas: Precision@5, Recall@5, MRR

**Tempo estimado:** 
- Dataset: 1-2 dias (extração + validação)
- Experimentos: 3-5 dias (execução + análise)

---

## 📌 Notas Importantes

- ✅ **Fase 9 Completa:** Pipeline RAG totalmente integrado e testado
  - RAGPipeline: 676 linhas integrando 11 componentes
  - Métodos: ingest_documents(), query(), batch_query()
  - Cache semântico, error handling, logging estruturado
  - 18 testes unitários + testes de integração end-to-end
  - Correções de compatibilidade API (PromptManager, RAGEvaluator, LLMClient)
- ✅ **Fase 10.1 Preparada:** Scripts de criação de dataset
  - `scripts/create_test_dataset.py`: Extração automática de Q&A de PDFs
  - `scripts/ingest_lei_15270.py`: Ingestão da Lei 15.270 no vector store
  - `scripts/README.md`: Documentação completa do fluxo
  - Estudo de caso: Lei 15.270 (Linguagem Simples IRPF)
- ✅ **Fase 8 Completa:** Todas as métricas de avaliação implementadas e validadas
  - BERTScore: 4/4 testes passando (P/R/F1: 0.717-1.000)
  - RAGAS: Integração com Gemini 2.5 Flash, score perfeito (1.000 faithfulness)
  - Factory functions para todos os evaluators
- ✅ **Arquitetura:** Completa e validada (v2.0 com 10 melhorias)
- ✅ **Configuração:** Sistema robusto com validação Pydantic
- ✅ **Modelos:** 100% gratuitos (Google Gemini 2.5 Flash + text-embedding-004)
- ⚠️ **API Key necessária:** Obtenha gratuitamente em https://aistudio.google.com/
- ⚠️ **Quota Gemini Free Tier:** 5 req/min, 20 req/dia por modelo - considerar cache e batching
- 🎯 **Foco atual:** Criação de dataset de teste para experimentos (Lei 15.270)

---

## 🎓 Recursos de Aprendizado

### Tutoriais Recomendados
1. LangChain RAG Tutorial
2. ChromaDB Quickstart
3. RAGAS Evaluation Guide

### Repositórios de Referência
- langchain-ai/langchain
- run-llama/llama_index
- explodinggradients/ragas

### Scripts Disponíveis
- `scripts/create_test_dataset.py` - Extração de Q&A de documentos
- `scripts/ingest_lei_15270.py` - Ingestão no vector store
- `scripts/README.md` - Documentação detalhada

---

**Data:** 15/02/2026  
**Versão:** 1.2  
**Última Atualização:** Fase 9 completa + Scripts Fase 10.1 criados  
**Autor:** Equipe LION
cd /home/decode/workspace/lion
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt