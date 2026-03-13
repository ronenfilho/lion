"""
Avaliação Consolidada do Componente de Retrieval (R) em RAG
=========================================================================
Para: Artigo Científico - LION RAG: Legal Interpretation in RAG Systems

Objetivo:
- Avaliar múltiplas estratégias de retrieval com rigor científico
- Coletar métricas de performance e qualidade
- Gerar dados reproduzíveis para análise e publicação
- Sem dependência de ground truth ou LLM generation

Estratégias Testadas:
1. Dense Retrieval (Embeddings Semânticos)
2. BM25 (Retrieval Baseado em Termos)
3. Hybrid Retrieval (Fusão RRF com Normalização)

Configurações:
- k ∈ {3, 5, 10} para cada método
- Dense Weight (α) ∈ {0.5, 0.7} para Hybrid
- 30 perguntas de teste (IRPF 2025)
- Total: ~50-70 avaliações com variações

Dataset: manual_rfb_test.json (30 perguntas IRPF)
Vector Store: ChromaDB "irpf_2025" (1,292 chunks)
Embedding Model: gemini-embedding-001 (3072-dim)

Output para Artigo:
- retrieval_results_TIMESTAMP.json (dados brutos estruturados)
- retrieval_metrics_TIMESTAMP.csv (métricas para tabelas)
- retrieval_analysis_TIMESTAMP.md (resumo e insights)
- figures_data/ (dados para gráficos)
"""

import sys
from pathlib import Path
import json
import hashlib
import csv
import argparse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import time
from tqdm import tqdm
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.vector_store import VectorStore
from src.retrieval.dense_retriever import DenseRetriever
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.hybrid_retriever import HybridRetriever
from src.ingestion.embeddings_pipeline import EmbeddingsPipeline

from dotenv import load_dotenv
import os

load_dotenv()


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
TEST_DATASET_PATH = "data/datasets/test/manual_rfb_test.json"
EMBEDDINGS_CACHE_PATH = "data/datasets/test/manual_rfb_test_embeddings.json"
RESULTS_DIR = Path("data/experiments/results/retrieval")

# Configurações de retrieval para o artigo
# Balanceado entre coverage (k variado) e métodos (3 abordagens)
RETRIEVAL_CONFIGS = [
    # Dense Retrieval - Semântica Pura
    {"method": "dense", "k": 3, "description": "Dense k=3"},
    {"method": "dense", "k": 5, "description": "Dense k=5"},
    {"method": "dense", "k": 10, "description": "Dense k=10"},
    
    # BM25 - Retrieval por Termos
    {"method": "bm25", "k": 3, "description": "BM25 k=3"},
    {"method": "bm25", "k": 5, "description": "BM25 k=5"},
    {"method": "bm25", "k": 10, "description": "BM25 k=10"},
    
    # Hybrid - Fusão RRF com Normalização
    {"method": "hybrid", "k": 3, "alpha": 0.7, "description": "Hybrid(α=0.7) k=3"},
    {"method": "hybrid", "k": 5, "alpha": 0.7, "description": "Hybrid(α=0.7) k=5"},
    {"method": "hybrid", "k": 10, "alpha": 0.7, "description": "Hybrid(α=0.7) k=10"},
    {"method": "hybrid", "k": 5, "alpha": 0.5, "description": "Hybrid(α=0.5) k=5"},
]


@dataclass
class RetrievalMetrics:
    """Métricas de uma retrieval para análise científica"""
    question_id: str
    method: str
    k: int
    alpha: Optional[float]
    latency_ms: float
    num_chunks: int
    top_score: float
    avg_score: float
    median_score: float
    std_score: float
    min_score: float
    max_score: float
    score_range: float
    total_chars: int
    total_words: int
    chunks: List[Dict[str, Any]]
    
    # ✅ Normalização para comparação científica (Abordagem A)
    score_normalized: float = 0.0  # Score normalizado em [0,1]
    rank_position: int = 0  # Posição no ranking da pergunta  
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'question_id': self.question_id,
            'method': self.method,
            'k': self.k,
            'alpha': self.alpha,
            'latency_ms': round(self.latency_ms, 2),
            'num_chunks': self.num_chunks,
            'top_score': round(self.top_score, 6),
            'avg_score': round(self.avg_score, 6),
            'median_score': round(self.median_score, 6),
            'std_score': round(self.std_score, 6),
            'min_score': round(self.min_score, 6),
            'max_score': round(self.max_score, 6),
            'score_range': round(self.score_range, 6),
            'total_chars': self.total_chars,
            'total_words': self.total_words,
            'chunks': self.chunks,
            # ✅ Abordagem A: Scores normalizados e ranking
            'score_normalized': round(self.score_normalized, 6),
            'rank_position': self.rank_position,
        }


class ConsolidatedRetrievalEvaluator:
    """
    Avaliador consolidado de retrieval para artigo científico.
    
    Responsabilidades:
    1. Gerenciar cache inteligente de embeddings
    2. Executar avaliações com múltiplas estratégias
    3. Coletar métricas com rigor estatístico
    4. Gerar saídas em múltiplos formatos (JSON, CSV, Markdown)
    5. Validar reprodutibilidade
    """
    
    def __init__(self):
        """Inicializa avaliador com componentes do RAG"""
        self.vector_store = VectorStore(
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME
        )
        self.embeddings_pipeline = EmbeddingsPipeline()
        self.results_dir = RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ ConsolidatedRetrievalEvaluator inicializado")
        print(f"   Vector Store: {self.vector_store.count()} chunks")
        print(f"   Collection: {COLLECTION_NAME}")
        print(f"   Embedding Model: {self.embeddings_pipeline.model_name}")
    
    # ========================================================================
    # Cache de Embeddings
    # ========================================================================
    
    def _compute_dataset_hash(self, dataset: Dict) -> str:
        """Computa hash SHA256 do dataset para validação de cache"""
        content = json.dumps(
            [(q['id'], q['question']) for q in dataset['questions']],
            sort_keys=True,
            ensure_ascii=False
        )
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_or_create_embeddings(self, dataset: Dict) -> Dict[str, List[float]]:
        """
        Gerencia cache inteligente de embeddings com validação.
        
        Estratégia:
        1. Se cache existe e é válido (hash match), reutiliza
        2. Se cache inválido ou não existe, regenera
        3. Valida integridade antes de usar
        
        Returns:
            Dict: {question_id: embedding_vector}
        """
        cache_path = Path(EMBEDDINGS_CACHE_PATH)
        current_hash = self._compute_dataset_hash(dataset)
        
        # Tentar carregar cache existente
        if cache_path.exists():
            print(f"\n📦 Verificando cache: {cache_path.name}")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                
                if cache.get('metadata', {}).get('dataset_hash') == current_hash:
                    print(f"   ✅ Cache válido ({len(cache['embeddings'])} embeddings)")
                    print(f"   ✓ Dataset hash: {current_hash[:8]}...")
                    print(f"   ✓ Criado em: {cache['metadata'].get('created_at', 'N/A')}")
                    return cache['embeddings']
                else:
                    print(f"   ⚠️ Cache inválido (dataset mudou). Regenerando...")
            except Exception as e:
                print(f"   ⚠️ Erro ao carregar cache: {e}. Regenerando...")
        else:
            print(f"\n🔄 Gerando embeddings para {len(dataset['questions'])} perguntas")
        
        # Gerar novos embeddings
        print()
        embeddings = {}
        import google.generativeai as genai
        
        for qa in tqdm(dataset['questions'], desc="   Processando", unit="q"):
            question_id = qa['id']
            question_text = qa['question']
            
            try:
                result = genai.embed_content(
                    model=self.embeddings_pipeline.model_name,
                    content=question_text,
                    task_type="retrieval_query"
                )
                embeddings[question_id] = result['embedding']
            except Exception as e:
                print(f"\n⚠️  Erro em {question_id}: {e}")
                embeddings[question_id] = None
        
        # Salvar cache com metadados
        cache = {
            'metadata': {
                'dataset_path': str(TEST_DATASET_PATH),
                'dataset_hash': current_hash,
                'embedding_model': self.embeddings_pipeline.model_name,
                'created_at': datetime.now().isoformat(),
                'total_questions': len(dataset['questions']),
                'successful': sum(1 for e in embeddings.values() if e is not None)
            },
            'embeddings': embeddings
        }
        
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        
        print(f"\n   ✅ Cache salvo: {cache_path}")
        return embeddings
    
    # ========================================================================
    # Carregamento de Dados
    # ========================================================================
    
    def load_test_dataset(self, max_questions: Optional[int] = None) -> Optional[Dict]:
        """Carrega dataset de teste com validação
        
        Args:
            max_questions: Número máximo de perguntas a carregar (None = todas)
        """
        dataset_path = Path(TEST_DATASET_PATH)
        
        if not dataset_path.exists():
            print(f"❌ Dataset não encontrado: {TEST_DATASET_PATH}")
            return None
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        questions = dataset.get('questions', []) if isinstance(dataset, dict) else dataset
        
        # Limitar quantidade de perguntas se especificado
        if max_questions and max_questions > 0:
            original_count = len(questions)
            questions = questions[:max_questions]
            print(f"✅ Dataset: {len(questions)}/{original_count} perguntas (limitado via CLI)")
        else:
            print(f"✅ Dataset: {len(questions)} perguntas")
        
        print(f"   Primeiras 3: {[q['id'] for q in questions[:3]]}")
        
        return {'questions': questions, 'metadata': dataset if isinstance(dataset, dict) else {}}
    
    # ========================================================================
    # Criação de Retrievers
    # ========================================================================
    
    def create_retriever(self, config: Dict) -> Optional[Any]:
        """Factory para criar retrievers baseado em config"""
        method = config['method']
        k = config['k']
        
        try:
            if method == 'dense':
                return DenseRetriever(vector_store=self.vector_store, top_k=k)
            
            elif method == 'bm25':
                return BM25Retriever.from_vector_store(
                    vector_store=self.vector_store,
                    top_k=k,
                    tokenizer='legal'
                )
            
            elif method == 'hybrid':
                dense_ret = DenseRetriever(vector_store=self.vector_store, top_k=k)
                return HybridRetriever(
                    dense_retriever=dense_ret,
                    top_k=k,
                    alpha=config.get('alpha', 0.7)
                )
        except Exception as e:
            return None
    
    # ========================================================================
    # Avaliação Principal
    # ========================================================================
    
    def evaluate_query(
        self,
        question: str,
        config: Dict,
        retriever: Any
    ) -> Optional[RetrievalMetrics]:
        """
        Avalia uma query com um retriever e coleta métricas detalhadas.
        
        Métricas coletadas:
        - Latência (ms) com breakdown embedding vs search
        - Número de chunks recuperados
        - Scores: top, avg, median, std, min, max, range
        - Percentile rank (posição normalizada na coleção)
        - Estatísticas de conteúdo: caracteres, palavras
        - ✅ CHUNKS DETALHADOS (content, metadata, counts)
        - ✅ Categoria e complexidade da query
        
        NOTA IMPORTANTE: NÃO normalizar scores!
        Cada método tem escala própria:
        - BM25: [0, ∞) - TF-IDF
        - Dense: [0, 1] - Cosine similarity  
        - Hybrid: ~0.0015 - RRF formula (agora com k=corpus_size/2)
        Normalizar prejudicaria análise comparativa (apples-to-oranges).
        """
        start_time = time.perf_counter()
        
        try:
            results = retriever.retrieve(question, top_k=config['k'])
            total_time_ms = (time.perf_counter() - start_time) * 1000
            
            if not results:
                return None
            
            scores = [r.score for r in results]
            
            # Calcular estatísticas
            avg_score = statistics.mean(scores)
            median_score = statistics.median(scores)
            std_score = statistics.stdev(scores) if len(scores) > 1 else 0
            
            # Conteúdo
            total_chars = sum(len(r.content) for r in results)
            total_words = sum(len(r.content.split()) for r in results)
            
            # Chunks detalhados
            chunks = [
                {
                    'id': r.id,
                    'score': r.score,
                    'content': r.content,
                    'character_count': len(r.content),
                    'word_count': len(r.content.split()),
                    'document': r.metadata.get('document'),
                    'section': r.metadata.get('section'),
                    'rank': idx + 1
                }
                for idx, r in enumerate(results)
            ]
            
            return RetrievalMetrics(
                question_id='placeholder',
                method=config['method'],
                k=config['k'],
                alpha=config.get('alpha'),
                latency_ms=total_time_ms,
                num_chunks=len(results),
                top_score=scores[0],
                avg_score=avg_score,
                median_score=median_score,
                std_score=std_score,
                min_score=min(scores),
                max_score=max(scores),
                score_range=max(scores) - min(scores),
                total_chars=total_chars,
                total_words=total_words,
                chunks=chunks,
            )
        
        except Exception as e:
            return None
    
    def run_evaluation(self, max_questions: Optional[int] = None) -> Dict[str, Any]:
        """
        Executa avaliação completa com todas as configurações.
        
        Args:
            max_questions: Número máximo de perguntas a processar (None = todas)
        
        Fluxo:
        1. Carregar dataset
        2. Gerenciar cache de embeddings
        3. Executar avaliações (config × questão)
        4. Agregar métricas
        5. Gerar saídas (JSON, CSV, MD)
        """
        print(f"\n{'='*80}")
        print(f"🧪 AVALIAÇÃO CONSOLIDADA DE RETRIEVAL")
        print(f"{'='*80}\n")
        
        # 1. Carregar dados
        dataset = self.load_test_dataset(max_questions=max_questions)
        if not dataset:
            return None
        
        questions = dataset['questions']
        embeddings_cache = self._load_or_create_embeddings(dataset)
        
        # 2. Executar avaliações
        print(f"\n{'='*80}")
        print(f"📊 EXECUTANDO AVALIAÇÕES")
        print(f"{'='*80}")
        print(f"   Estratégias: {len(RETRIEVAL_CONFIGS)}")
        print(f"   Perguntas: {len(questions)}")
        print(f"   Total: ~{len(RETRIEVAL_CONFIGS) * len(questions)} avaliações\n")
        
        all_metrics = []
        total_evals = len(RETRIEVAL_CONFIGS) * len(questions)
        
        with tqdm(total=total_evals, desc="Progresso geral", unit="eval") as pbar:
            for q_idx, question_obj in enumerate(questions, 1):
                q_id = question_obj['id']
                q_text = question_obj['question']
                q_cat = question_obj.get('category', 'unknown')
                q_complex = question_obj.get('complexity', 'unknown')
                
                print(f"\n[{q_idx}/{len(questions)}] {q_id} [{q_cat}/{q_complex}]: {q_text[:50]}...")
                
                for cfg in RETRIEVAL_CONFIGS:
                    retriever = self.create_retriever(cfg)
                    
                    if not retriever:
                        pbar.update(1)
                        continue
                    
                    metrics = self.evaluate_query(q_text, cfg, retriever)
                    
                    if metrics:
                        metrics.question_id = q_id
                        all_metrics.append(metrics)
                        
                        status = (
                            f"✅ {cfg['description']}: "
                            f"{metrics.num_chunks} chunks | "
                            f"score={metrics.top_score:.4f} | "
                            f"lat={metrics.latency_ms:.0f}ms"
                        )
                    else:
                        status = f"❌ {cfg['description']}: Falha"
                    
                    pbar.set_postfix_str(status)
                    pbar.update(1)
        
        # ✅ ABORDAGEM A: Normalizar scores para comparação científica
        print(f"\n{'='*80}")
        print(f"📊 NORMALIZANDO SCORES (Min-Max [0,1])")
        print(f"{'='*80}\n")
        all_metrics = self._normalize_scores_minmax(all_metrics)
        
        # 3. Agregar e salvar
        print(f"\n{'='*80}")
        print(f"💾 SALVANDO RESULTADOS")
        print(f"{'='*80}\n")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        output = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_questions': len(questions),
                'total_configs': len(RETRIEVAL_CONFIGS),
                'total_evaluations': len(all_metrics),
                'vector_store': {
                    'name': COLLECTION_NAME,
                    'total_chunks': self.vector_store.count(),
                    'embedding_model': self.embeddings_pipeline.model_name
                },
                'dataset': {
                    'path': TEST_DATASET_PATH,
                    'count': len(questions)
                }
            },
            'results': [m.to_dict() for m in all_metrics]
        }
        
        # Salvar JSON
        json_path = self.results_dir / f"retrieval_results_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ {json_path.name} ({len(output['results'])} resultados)")
        
        # Salvar CSV
        csv_path = self._save_csv(all_metrics, timestamp)
        print(f"✅ {csv_path.name}")
        
        # Salvar Markdown
        md_path = self._save_markdown(all_metrics, timestamp)
        print(f"✅ {md_path.name}")
        
        # Salvar dados para gráficos
        figures_dir = self.results_dir / "figures_data"
        figures_dir.mkdir(exist_ok=True)
        self._save_figures_data(all_metrics, timestamp)
        print(f"✅ figures_data/ (4 arquivos)")
        
        print(f"\n{'='*80}")
        print(f"✅ AVALIAÇÃO CONCLUÍDA")
        print(f"{'='*80}")
        print(f"\n📁 Resultados em: {self.results_dir}\n")
        
        return output
    
    # ========================================================================
    # Normalização para Comparação Científica (Abordagem A)
    # ========================================================================
    
    def _normalize_scores_minmax(self, metrics: List[RetrievalMetrics]) -> List[RetrievalMetrics]:
        """
        Normaliza scores usando Min-Max [0,1] por pergunta.
        
        Estratégia:
        1. Para cada pergunta, encontrar min/max scores globalmente
        2. Normalizar cada score: (x - min) / (max - min)
        3. Gerar ranking por score normalizado
        
        Isso permite comparação científica entre métodos com escalas diferentes.
        """
        # Agrupar por pergunta
        by_question = {}
        for m in metrics:
            if m.question_id not in by_question:
                by_question[m.question_id] = []
            by_question[m.question_id].append(m)
        
        # Normalizar por pergunta
        normalized = []
        for q_id, q_metrics in by_question.items():
            # Encontrar min/max global (todos os métodos)
            scores = [m.top_score for m in q_metrics]
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score
            
            # Normalizar e calcular ranking
            if score_range > 0:
                for m in q_metrics:
                    m.score_normalized = (m.top_score - min_score) / score_range
            else:
                # Todos os scores são iguais
                for m in q_metrics:
                    m.score_normalized = 0.5
            
            # Ordenar por score normalizado (descending) para gerar ranking
            sorted_metrics = sorted(q_metrics, key=lambda x: x.score_normalized, reverse=True)
            for rank, m in enumerate(sorted_metrics, 1):
                m.rank_position = rank
            
            normalized.extend(q_metrics)
            
            # Log
            print(f"✅ {q_id}: min={min_score:.6f}, max={max_score:.6f}")
            for m in sorted_metrics[:3]:
                print(f"   #{m.rank_position} {m.method:6s} k={m.k} α={m.alpha}: "
                      f"score_norm={m.score_normalized:.4f}")
        
        return normalized
    
    # ========================================================================
    # Exportação de Dados
    # ========================================================================
    
    def _save_csv(self, metrics: List[RetrievalMetrics], timestamp: str) -> Path:
        """Salva métricas em CSV para análise e tabelas no artigo"""
        csv_path = self.results_dir / f"retrieval_metrics_{timestamp}.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'question_id', 'method', 'k', 'alpha',
                'latency_ms', 'num_chunks',
                'top_score', 'score_normalized', 'rank_position',
                'avg_score', 'median_score', 'std_score',
                'min_score', 'max_score', 'score_range',
                'total_chars', 'total_words'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for m in metrics:
                row = m.to_dict()
                # Remover chunks que não vai para CSV
                row.pop('chunks', None)
                writer.writerow(row)
        
        return csv_path
    
    def _save_markdown(self, metrics: List[RetrievalMetrics], timestamp: str) -> Path:
        """Salva análise em Markdown com insights para artigo"""
        md_path = self.results_dir / f"retrieval_analysis_{timestamp}.md"
        
        # Agregar por método
        by_method = {}
        for m in metrics:
            if m.method not in by_method:
                by_method[m.method] = []
            by_method[m.method].append(m)
        
        content = [
            f"# Análise de Retrieval - {datetime.now().strftime('%d/%m/%Y')}\n",
            f"## Resumo\n",
            f"- **Avaliações**: {len(metrics)}\n",
            f"- **Métodos**: {', '.join(sorted(by_method.keys()))}\n",
            f"- **Total de queries**: {len(set(m.question_id for m in metrics))}\n",
            f"- **Normalização**: Min-Max [0,1] por pergunta (Abordagem A)\n\n",
            
            f"## Resultados por Método (Original)\n\n",
            f"| Método | K | Latência (ms) | Chunks | Top Score | Std Dev |\n",
            f"|--------|---|---------------|--------|-----------|----------|\n",
        ]
        
        for method in sorted(by_method.keys()):
            method_metrics = by_method[method]
            
            for k in sorted(set(m.k for m in method_metrics)):
                k_metrics = [m for m in method_metrics if m.k == k]
                k_lat = statistics.mean(m.latency_ms for m in k_metrics)
                k_chunks = statistics.mean(m.num_chunks for m in k_metrics)
                k_score = statistics.mean(m.top_score for m in k_metrics)
                k_std = statistics.mean(m.std_score for m in k_metrics)
                
                content.append(
                    f"| {method} | {k} | {k_lat:.1f} | {k_chunks:.1f} | "
                    f"{k_score:.4f} | {k_std:.4f} |\n"
                )
        
        # ✅ NOVO: Tabela com scores normalizados
        content.append(f"\n## Resultados Normalizados [0,1] (Comparáveis)\n\n")
        content.append(f"| Método | K | Rank | Score Norm | Latência (ms) |\n")
        content.append(f"|--------|---|------|------------|---------------|\n")
        
        for method in sorted(by_method.keys()):
            method_metrics = by_method[method]
            
            for k in sorted(set(m.k for m in method_metrics)):
                k_metrics = [m for m in method_metrics if m.k == k]
                # Usar primeira métrica do grupo (rank e score_normalized são iguais)
                m = k_metrics[0]
                k_lat = statistics.mean(x.latency_ms for x in k_metrics)
                
                content.append(
                    f"| {method} | {k} | #{m.rank_position} | "
                    f"{m.score_normalized:.4f} | {k_lat:.1f} |\n"
                )
        
        content.append(f"\n## Destaques\n\n")
        
        # Mais rápido
        fastest = min(metrics, key=lambda m: m.latency_ms)
        content.append(
            f"⚡ **Mais rápido**: {fastest.method} (k={fastest.k}) - "
            f"{fastest.latency_ms:.2f}ms\n\n"
        )
        
        # Melhor score normalizado
        best_normalized = max(metrics, key=lambda m: m.score_normalized)
        content.append(
            f"🏆 **Melhor score normalizado**: {best_normalized.method} (k={best_normalized.k}) - "
            f"{best_normalized.score_normalized:.4f} [0,1]\n"
            f"   └─ Ranking: #{best_normalized.rank_position}\n\n"
        )
        
        # Resumo por método (normalizado)
        content.append(f"## Resumo por Método (Normalizado)\n\n")
        for method in sorted(by_method.keys()):
            method_metrics = by_method[method]
            avg_norm = statistics.mean(m.score_normalized for m in method_metrics)
            avg_rank = statistics.mean(m.rank_position for m in method_metrics)
            avg_lat = statistics.mean(m.latency_ms for m in method_metrics)
            
            content.append(
                f"**{method}**: score_norm={avg_norm:.4f} | "
                f"rank_médio={avg_rank:.1f} | latência={avg_lat:.0f}ms\n"
            )
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.writelines(content)
        
        return md_path
    
    def _save_figures_data(self, metrics: List[RetrievalMetrics], timestamp: str):
        """Salva dados agregados para gerar gráficos no artigo"""
        figures_dir = self.results_dir / "figures_data"
        
        # 1. Latência por método
        by_method = {}
        for m in metrics:
            if m.method not in by_method:
                by_method[m.method] = []
            by_method[m.method].append(m.latency_ms)
        
        latency_data = {
            method: {
                'mean': statistics.mean(lats),
                'median': statistics.median(lats),
                'std': statistics.stdev(lats) if len(lats) > 1 else 0,
                'min': min(lats),
                'max': max(lats)
            }
            for method, lats in by_method.items()
        }
        
        with open(figures_dir / f"latency_{timestamp}.json", 'w') as f:
            json.dump(latency_data, f, indent=2, ensure_ascii=False)
        
        # 2. Score por método
        by_method_metrics = {}
        for m in metrics:
            if m.method not in by_method_metrics:
                by_method_metrics[m.method] = []
            by_method_metrics[m.method].append(m)
        
        score_data = {
            method: {
                'mean': statistics.mean(m.top_score for m in by_method_metrics[method]),
                'std': statistics.stdev([m.top_score for m in by_method_metrics[method]]) if len(by_method_metrics[method]) > 1 else 0,
            }
            for method in by_method_metrics.keys()
        }
        
        with open(figures_dir / f"scores_{timestamp}.json", 'w') as f:
            json.dump(score_data, f, indent=2, ensure_ascii=False)
        
        # 3. k-effect (impacto de k em cada método)
        by_method_k = {}
        for m in metrics:
            key = f"{m.method}_k{m.k}"
            if key not in by_method_k:
                by_method_k[key] = []
            by_method_k[key].append(m.top_score)
        
        k_effect = {
            key: statistics.mean(scores)
            for key, scores in by_method_k.items()
        }
        
        with open(figures_dir / f"k_effect_{timestamp}.json", 'w') as f:
            json.dump(k_effect, f, indent=2, ensure_ascii=False)
        
        # 4. Correlação latência vs chunks
        correlation_data = [
            {'method': m.method, 'k': m.k, 'latency': m.latency_ms, 'chunks': m.num_chunks}
            for m in metrics
        ]
        
        with open(figures_dir / f"latency_chunks_{timestamp}.json", 'w') as f:
            json.dump(correlation_data, f, indent=2, ensure_ascii=False)


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="Avaliação Consolidada de Retrieval para Artigo Científico",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python consolidated_retrieval_evaluation.py              # Processa todas as 30 perguntas
  python consolidated_retrieval_evaluation.py --questions 5  # Processa apenas 5 perguntas
  python consolidated_retrieval_evaluation.py -q 10         # Processa apenas 10 perguntas
        """
    )
    
    parser.add_argument(
        '-q', '--questions',
        type=int,
        default=None,
        help='Número máximo de perguntas a processar (padrão: todas)'
    )
    
    args = parser.parse_args()
    
    evaluator = ConsolidatedRetrievalEvaluator()
    evaluator.run_evaluation(max_questions=args.questions)


if __name__ == '__main__':
    main()
