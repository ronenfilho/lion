# 🛠️ LION - Guia Prático de Implementação

## 📋 Roadmap de Implementação Detalhado

Este guia fornece um passo a passo prático para implementar a arquitetura RAG do projeto LION.

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

### 📊 Progresso Geral: 41% Completo (14/34 tarefas)

```markdown
## ✅ Fase 1: Setup Inicial (100% - 6/6)
- [x] Estrutura de diretórios criada (30+ pastas)
- [x] requirements.txt criado (40+ dependências)
- [x] .env.example configurado
- [x] .gitignore criado
- [x] Git inicializado
- [x] Arquitetura e documentação completa (8 docs, ~3800 linhas)

## ✅ Fase 2: Configuração do Sistema (100% - 6/6)
- [x] Sistema de configuração YAML implementado
- [x] Validação Pydantic (config.py com 8 classes)
- [x] config/default.yaml (configuração base)
- [x] config/development.yaml (ambiente dev)
- [x] config/production.yaml (ambiente prod)
- [x] Modelos trocados para Google (Gemini 2.0 Flash + text-embedding-004)

## ✅ Fase 3: Ambiente Python (100% - 2/2) ✨ NOVO
- [x] Ambiente virtual criado (venv)
- [x] Dependências instaladas compatíveis com Python 3.12
- [x] Integração .env → YAML implementada (prioridade: .env > {env}.yaml > default.yaml)
- [x] Sistema de configuração testado e validado ✓

## 🔄 Fase 4: Ingestão de Dados (0% - 0/6)
- [ ] src/ingestion/extractors/pdf_extractor.py
- [ ] src/ingestion/extractors/text_cleaner.py
- [ ] src/ingestion/chunking/structural_chunker.py
- [ ] src/ingestion/chunking/qa_chunker.py
- [ ] src/ingestion/embeddings_pipeline.py
- [ ] Configurar ChromaDB local

## 🔄 Fase 5: Sistema de Retrieval (0% - 0/5)
- [ ] src/retrieval/vector_store.py (abstração)
- [ ] src/retrieval/dense_retriever.py
- [ ] src/retrieval/bm25_retriever.py
- [ ] src/retrieval/hybrid_retriever.py (70% dense + 30% BM25)
- [ ] src/retrieval/reranker.py (cross-encoder)

## 🔄 Fase 6: Geração de Respostas (0% - 0/3)
- [ ] src/generation/llm_client.py (Google Gemini)
- [ ] src/generation/prompts.py (templates especializados)
- [ ] src/generation/output_parser.py (estruturação)

## 🔄 Fase 7: Guardrails (0% - 0/3)
- [ ] src/guardrails/input_validator.py (PII, prompt injection)
- [ ] src/guardrails/output_validator.py (citações, relevância)
- [ ] src/guardrails/pii_detector.py (regex + NER)

## 🔄 Fase 8: Avaliação (0% - 0/3)
- [ ] src/evaluation/metrics/bertscore.py
- [ ] src/evaluation/metrics/ragas_metrics.py
- [ ] src/evaluation/experiments/runner.py

## 🔄 Fase 9: Pipeline RAG Completo (0% - 0/3)
- [ ] src/pipeline/rag_pipeline.py (integração completa)
- [ ] tests/unit/ (testes unitários)
- [ ] tests/integration/ (testes de integração)

## 🔄 Fase 10: Experimentos (0% - 0/3)
- [ ] Preparar dataset de teste (perguntas IRPF)
- [ ] Executar experimentos comparativos
- [ ] Analisar resultados e métricas
```

---

## 🎯 PRÓXIMO PASSO RECOMENDADO

### ➡️ Fase 4: Implementar Módulo de Ingestão

**Começar com: PDF Extractor** 

O primeiro componente funcional será `src/ingestion/extractors/pdf_extractor.py` para processar documentos IRPF.

**O que implementar:**
```bash
cd /home/decode/workspace/lion
python3 -m venv venv
source venv/bin/activate
```

2. **Instalar dependências:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Configurar variáveis de ambiente:**
```bash
cp .env.example .env
# Editar .env e adicionar sua GOOGLE_API_KEY
# Obter chave em: https://aistudio.google.com/app/apikey
```

4. **Verificar instalação:**
```bash
python -c "import langchain; import chromadb; import google.generativeai; print('✅ Dependências OK')"
```

**Tempo estimado:** 5-10 minutos

**Após conclusão:** Começar implementação do módulo de ingestão (Fase 4) - PDF extractor será o primeiro componente funcional.

---

## 📌 Notas Importantes

- ✅ **Arquitetura:** Completa e validada (v2.0 com 10 melhorias)
- ✅ **Configuração:** Sistema robusto com validação Pydantic
- ✅ **Modelos:** 100% gratuitos (Google Gemini + text-embedding-004)
- ⚠️ **API Key necessária:** Obtenha gratuitamente em https://aistudio.google.com/
- 🎯 **Foco atual:** Setup do ambiente Python antes de implementar código

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

---

**Data:** 14/02/2026  
**Versão:** 1.0  
**Autor:** Equipe LION
cd /home/decode/workspace/lion
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt