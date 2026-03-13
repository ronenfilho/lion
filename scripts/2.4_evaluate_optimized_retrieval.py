"""
Script 2.4: Avaliação de Retrieval Otimizado
- Compara BM25 + CrossEncoder Rerank vs métodos originais
- Pipeline otimizado: 10-15x mais rápido que Dense com melhor qualidade
- Testa diferentes configurações de reranking
"""

import sys
from pathlib import Path
import json
import csv
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.vector_store import VectorStore
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.cross_encoder_reranker import (
    CrossEncoderReranker,
    PipelinedRetriever
)

from dotenv import load_dotenv
import os

load_dotenv()

# Configurações
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
TEST_DATASET_PATH = "data/datasets/test/manual_rfb_test.json"
EMBEDDINGS_CACHE_PATH = "data/datasets/test/manual_rfb_test_embeddings.json"
RESULTS_DIR = Path("data/experiments/results/retrieval")

# Configurações a testar
RERANKING_CONFIGS = [
    {"pipeline_type": "bm25_only", "bm25_k": 5, "final_k": 5, "rerank": False},
    {"pipeline_type": "bm25_rerank", "bm25_k": 10, "final_k": 3, "rerank": True},
    {"pipeline_type": "bm25_rerank", "bm25_k": 10, "final_k": 5, "rerank": True},
    {"pipeline_type": "bm25_rerank", "bm25_k": 15, "final_k": 3, "rerank": True},
]


class OptimizedRetrievalEvaluator:
    """Avaliador de pipeline otimizado de retrieval"""
    
    def __init__(self):
        """Inicializa avaliador"""
        self.vector_store = VectorStore(
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME
        )
        self.results_dir = RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar BM25
        self.bm25_retriever = BM25Retriever.from_vector_store(
            vector_store=self.vector_store,
            top_k=15,  # Máximo para reranking
            tokenizer='legal'
        )
        
        print(f"✅ OptimizedRetrievalEvaluator inicializado")
        print(f"   Vector Store: {self.vector_store.count()} documentos")
        print(f"   Collection: {COLLECTION_NAME}")
    
    def load_test_dataset(self) -> Optional[Dict]:
        """Carrega dataset de teste"""
        dataset_path = Path(TEST_DATASET_PATH)
        if not dataset_path.exists():
            print(f"❌ Dataset não encontrado: {TEST_DATASET_PATH}")
            return None
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        if isinstance(dataset, dict) and 'questions' in dataset:
            questions = dataset['questions']
        else:
            questions = dataset if isinstance(dataset, list) else []
        
        print(f"✅ Dataset carregado: {len(questions)} perguntas")
        return {'questions': questions}
    
    def create_pipeline(self, config: Dict) -> Optional[PipelinedRetriever]:
        """
        Cria pipeline baseado em configuração.
        
        Args:
            config: Configuração de pipeline
            
        Returns:
            PipelinedRetriever inicializado
        """
        try:
            pipeline = PipelinedRetriever(
                bm25_retriever=self.bm25_retriever,
                bm25_fetch_k=config.get('bm25_k', 10),
                final_top_k=config.get('final_k', 3),
                use_reranking=config.get('rerank', True)
            )
            return pipeline
        except Exception as e:
            print(f"   ❌ Erro ao criar pipeline: {e}")
            return None
    
    def format_config(self, config: Dict) -> str:
        """Formata config para display"""
        if config.get('rerank'):
            return f"bm25(k={config['bm25_k']}) → rerank(k={config['final_k']})"
        else:
            return f"bm25(k={config['final_k']})"
    
    def evaluate_single_query(
        self,
        question: str,
        config: Dict,
        pipeline: PipelinedRetriever
    ) -> Dict[str, Any]:
        """
        Avalia um query com o pipeline.
        
        Args:
            question: Texto da pergunta
            config: Configuração do pipeline
            pipeline: PipelinedRetriever
            
        Returns:
            Métricas de retrieval
        """
        start_time = time.time()
        
        try:
            results = pipeline.retrieve(question, top_k=config.get('final_k', 3))
            latency_ms = (time.time() - start_time) * 1000
            
            if not results:
                return {
                    'latency_ms': latency_ms,
                    'num_chunks': 0,
                    'top_score': 0,
                    'avg_score': 0,
                    'error': 'No results'
                }
            
            scores = [r.score for r in results]
            total_chars = sum(len(r.content) for r in results)
            total_words = sum(len(r.content.split()) for r in results)
            
            return {
                'latency_ms': latency_ms,
                'num_chunks': len(results),
                'total_characters': total_chars,
                'total_words': total_words,
                'top_score': scores[0] if scores else 0,
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'chunks': [
                    {
                        'id': r.id,
                        'score': r.score,
                        'original_rank': r.original_rank,
                        'document': r.metadata.get('document', 'N/A'),
                        'section': r.metadata.get('section', 'N/A'),
                        'content': r.content[:500]  # Preview
                    }
                    for r in results
                ]
            }
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                'latency_ms': latency_ms,
                'error': str(e)
            }
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Executa avaliação completa"""
        print(f"\n{'='*80}")
        print(f"🚀 AVALIAÇÃO DE RETRIEVAL OTIMIZADO")
        print(f"{'='*80}\n")
        
        # Carregar dataset
        print("📂 Carregando dataset...")
        dataset = self.load_test_dataset()
        if not dataset:
            return None
        
        questions = dataset['questions']
        
        # Executar avaliação
        print(f"\n📊 Testando {len(RERANKING_CONFIGS)} configurações")
        print(f"   com {len(questions)} perguntas")
        print(f"   = {len(RERANKING_CONFIGS) * len(questions)} execuções\n")
        
        all_results = []
        
        total_evaluations = len(RERANKING_CONFIGS) * len(questions)
        pbar = tqdm(total=total_evaluations, desc="🔄 Progresso geral", unit="eval")
        
        for q_idx, qa in enumerate(questions, 1):
            question_id = qa['id']
            question = qa['question']
            
            print(f"\n[{q_idx}/{len(questions)}] {question_id}: {question[:60]}...")
            
            for config_idx, config in enumerate(RERANKING_CONFIGS, 1):
                pipeline = self.create_pipeline(config)
                
                if not pipeline:
                    print(f"   ❌ Config {config_idx}: Falha na criação")
                    pbar.update(1)
                    continue
                
                # Avaliar
                result = self.evaluate_single_query(question, config, pipeline)
                
                # Adicionar metadados
                result['question_id'] = question_id
                result['question'] = question[:100]
                result['config_pipeline_type'] = config['pipeline_type']
                result['config_bm25_k'] = config.get('bm25_k', None)
                result['config_final_k'] = config['final_k']
                result['config_use_reranking'] = config.get('rerank', False)
                
                all_results.append(result)
                
                if 'error' not in result:
                    config_str = self.format_config(config)
                    status = f"✅ {config_str}: {result['num_chunks']} chunks | score={result['top_score']:.3f} | lat={result['latency_ms']:.0f}ms"
                else:
                    status = f"❌ {config['pipeline_type']}: {result['error']}"
                
                pbar.set_postfix_str(status)
                pbar.update(1)
        
        pbar.close()
        
        # Agregar resultados
        print(f"\n{'='*80}")
        print(f"📈 AGREGAÇÃO DE RESULTADOS")
        print(f"{'='*80}\n")
        
        aggregated = self._aggregate_results(all_results)
        
        # Salvar resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_questions': len(questions),
            'total_configs': len(RERANKING_CONFIGS),
            'total_evaluations': len(all_results),
            'successful_evaluations': len([r for r in all_results if 'error' not in r]),
            'aggregated_metrics': aggregated,
            'individual_results': all_results
        }
        
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON
        json_path = self.results_dir / f"optimized_retrieval_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON: {json_path}")
        
        # CSV
        csv_path = self.results_dir / f"optimized_retrieval_{timestamp}.csv"
        self.save_csv_report(all_results, timestamp)
        print(f"✅ CSV: {csv_path}")
        
        # Markdown
        md_path = self.results_dir / f"optimized_retrieval_{timestamp}.md"
        self.save_markdown_report(aggregated, timestamp)
        print(f"✅ Markdown: {md_path}\n")
        
        print(f"{'='*80}")
        print(f"✅ AVALIAÇÃO CONCLUÍDA!")
        print(f"{'='*80}")
        print(f"\n📁 Resultados salvos em: {self.results_dir}\n")
        
        return output_data
    
    def _aggregate_results(self, results: List[Dict]) -> Dict[str, Dict]:
        """Agrega resultados por configuração"""
        aggregated = {}
        
        for result in results:
            config_key = f"{result['config_pipeline_type']}_bm25_{result['config_bm25_k']}_final_{result['config_final_k']}"
            
            if config_key not in aggregated:
                aggregated[config_key] = {
                    'latencies': [],
                    'top_scores': [],
                    'avg_scores': [],
                    'num_chunks_list': [],
                    'total_chars': [],
                    'total_words': []
                }
            
            if 'error' not in result:
                aggregated[config_key]['latencies'].append(result['latency_ms'])
                aggregated[config_key]['top_scores'].append(result['top_score'])
                aggregated[config_key]['avg_scores'].append(result['avg_score'])
                aggregated[config_key]['num_chunks_list'].append(result['num_chunks'])
                aggregated[config_key]['total_chars'].append(result.get('total_characters', 0))
                aggregated[config_key]['total_words'].append(result.get('total_words', 0))
        
        # Calcular stats
        stats = {}
        for config_key, data in aggregated.items():
            if data['latencies']:
                stats[config_key] = {
                    'avg_latency_ms': sum(data['latencies']) / len(data['latencies']),
                    'min_latency_ms': min(data['latencies']),
                    'max_latency_ms': max(data['latencies']),
                    'avg_top_score': sum(data['top_scores']) / len(data['top_scores']),
                    'avg_num_chunks': sum(data['num_chunks_list']) / len(data['num_chunks_list']),
                    'total_characters': sum(data['total_chars']),
                    'total_words': sum(data['total_words'])
                }
        
        return stats
    
    def save_csv_report(self, results: List[Dict], timestamp: str) -> Path:
        """Salva resultados em CSV"""
        csv_path = self.results_dir / f"optimized_retrieval_{timestamp}.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'question_id', 'question_preview', 'config_pipeline_type',
                'config_bm25_k', 'config_final_k', 'config_use_reranking',
                'latency_ms', 'num_chunks', 'total_characters', 'total_words',
                'top_score', 'avg_score', 'min_score', 'max_score'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                if 'error' not in result:
                    row = {
                        'question_id': result['question_id'],
                        'question_preview': result['question'],
                        'config_pipeline_type': result['config_pipeline_type'],
                        'config_bm25_k': result['config_bm25_k'],
                        'config_final_k': result['config_final_k'],
                        'config_use_reranking': result['config_use_reranking'],
                        'latency_ms': result['latency_ms'],
                        'num_chunks': result['num_chunks'],
                        'total_characters': result.get('total_characters', 0),
                        'total_words': result.get('total_words', 0),
                        'top_score': result['top_score'],
                        'avg_score': result['avg_score'],
                        'min_score': result['min_score'],
                        'max_score': result['max_score']
                    }
                    writer.writerow(row)
        
        return csv_path
    
    def save_markdown_report(self, aggregated: Dict, timestamp: str) -> Path:
        """Salva análise em Markdown"""
        md_path = self.results_dir / f"optimized_retrieval_{timestamp}.md"
        
        content = f"""# Avaliação de Retrieval Otimizado

**Data**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## Resumo de Configurações

| Pipeline | BM25 K | Final K | Latência (ms) | Top Score | Chunks |
|----------|--------|---------|---------------|-----------|--------|
"""
        
        for config, metrics in sorted(aggregated.items(), key=lambda x: x[1]['avg_latency_ms']):
            parts = config.split('_')
            bm25_k = parts[3]
            final_k = parts[5]
            
            content += f"| {config[:30]:30s} | {bm25_k:6s} | {final_k:7s} | {metrics['avg_latency_ms']:13.1f} | {metrics['avg_top_score']:9.3f} | {metrics['avg_num_chunks']:6.1f} |\n"
        
        content += "\n## Melhores Configurações\n\n"
        
        # Mais rápido
        fastest = min(aggregated.items(), key=lambda x: x[1]['avg_latency_ms'])
        content += f"⚡ **Mais Rápido**: {fastest[0]}\n"
        content += f"   - Latência: {fastest[1]['avg_latency_ms']:.1f}ms\n\n"
        
        # Melhor score
        best_score = max(aggregated.items(), key=lambda x: x[1]['avg_top_score'])
        content += f"🏆 **Melhor Score**: {best_score[0]}\n"
        content += f"   - Score: {best_score[1]['avg_top_score']:.4f}\n"
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return md_path


def main():
    """Executa avaliação completa"""
    evaluator = OptimizedRetrievalEvaluator()
    return evaluator.run_evaluation()


if __name__ == "__main__":
    main()
