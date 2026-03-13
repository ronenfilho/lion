"""
Script 2.4: Avaliação de Retrieval Otimizado (Simplificado)
- Compara diferentes configurações de BM25 (para preparar para reranking)
- Execução rápida para validação de pipeline
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

from dotenv import load_dotenv
import os

load_dotenv()

# Configurações
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
TEST_DATASET_PATH = "data/datasets/test/manual_rfb_test.json"
RESULTS_DIR = Path("data/experiments/results/retrieval")

# Configurações a testar
BATCHER_CONFIGS = [
    {"name": "bm25_k3", "k": 3},
    {"name": "bm25_k5", "k": 5},
    {"name": "bm25_k10", "k": 10},
    {"name": "bm25_k15", "k": 15},
]


class OptimizedRetrievalEvaluator:
    """Avaliador de retrieval otimizado"""
    
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
            top_k=15,
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
    
    def evaluate_single_query(
        self,
        question: str,
        k: int
    ) -> Dict[str, Any]:
        """
        Avalia um query com BM25.
        
        Args:
            question: Texto da pergunta
            k: Número de chunks a recuperar
            
        Returns:
            Métricas de retrieval
        """
        start_time = time.time()
        
        try:
            # Temporariamente mudar top_k do retriever
            old_k = self.bm25_retriever.top_k
            self.bm25_retriever.top_k = k
            
            results = self.bm25_retriever.retrieve(question)
            latency_ms = (time.time() - start_time) * 1000
            
            # Restaurar top_k
            self.bm25_retriever.top_k = old_k
            
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
            
            # Incluir chunks detalhados
            chunks = [
                {
                    'id': r.id,
                    'content': r.content,
                    'score': r.score,
                    'document': r.metadata.get('document'),
                    'section': r.metadata.get('section'),
                    'character_count': len(r.content),
                    'word_count': len(r.content.split())
                }
                for r in results
            ]
            
            return {
                'latency_ms': latency_ms,
                'num_chunks': len(results),
                'total_characters': total_chars,
                'total_words': total_words,
                'top_score': scores[0] if scores else 0,
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'chunks': chunks
            }
        except Exception as e:
            return {
                'error': str(e),
                'latency_ms': (time.time() - start_time) * 1000
            }
    
    def run_evaluation(self):
        """Executa avaliação completa"""
        dataset = self.load_test_dataset()
        if not dataset:
            return False
        
        questions = dataset['questions']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        all_results = {
            'timestamp': timestamp,
            'dataset': TEST_DATASET_PATH,
            'total_questions': len(questions),
            'configs': BATCHER_CONFIGS,
            'individual_results': []
        }
        
        # Iterar por cada config e cada pergunta
        total_evals = len(BATCHER_CONFIGS) * len(questions)
        
        with tqdm(total=total_evals, desc="Avaliação geral", unit="eval") as pbar_main:
            for cfg_idx, config in enumerate(BATCHER_CONFIGS, 1):
                print(f"\n🔄 Config {cfg_idx}/{len(BATCHER_CONFIGS)}: {config['name']}")
                
                config_results = {
                    'config_name': config['name'],
                    'config_k': config['k'],
                    'query_results': []
                }
                
                config_latencies = []
                config_scores = []
                
                for q_idx, question in enumerate(questions, 1):
                    q_id = question.get('id', f'q{q_idx:03d}')
                    q_text = question.get('text', question.get('question', str(question)))[:100]
                    
                    result = self.evaluate_single_query(q_text, k=config['k'])
                    
                    # Salvar resultado detalhado
                    eval_result = {
                        'config_name': config['name'],
                        'config_k': config['k'],
                        'question_id': q_id,
                        'question_text': q_text,
                    }
                    eval_result.update(result)
                    
                    all_results['individual_results'].append(eval_result)
                    
                    if 'error' not in result:
                        config_results['query_results'].append(result)
                        config_latencies.append(result['latency_ms'])
                        config_scores.append(result['top_score'])
                    
                    # Update progress bar
                    msg = f"✅ {config['name']}: {result['num_chunks']} chunks | score={result.get('top_score', 0):.3f} | lat={result['latency_ms']:.1f}ms"
                    pbar_main.set_postfix_str(msg)
                    pbar_main.update(1)
                
                # Calcular agregados
                if config_latencies:
                    config_results['latency_mean_ms'] = sum(config_latencies) / len(config_latencies)
                    config_results['latency_min_ms'] = min(config_latencies)
                    config_results['latency_max_ms'] = max(config_latencies)
                    config_results['score_mean'] = sum(config_scores) / len(config_scores)
                    config_results['score_min'] = min(config_scores)
                    config_results['score_max'] = max(config_scores)
                
                all_results[config['name']] = config_results
        
        # Salvar resultados
        self._save_results(all_results, timestamp)
        
        return True
    
    def _save_results(self, results: Dict, timestamp: str):
        """Salva resultados em JSON, CSV e Markdown"""
        
        # JSON
        json_path = self.results_dir / f"optimized_retrieval_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ JSON salvo: {json_path}")
        
        # CSV
        csv_path = self.results_dir / f"optimized_retrieval_{timestamp}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = None
            for result in results['individual_results']:
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=result.keys())
                    writer.writeheader()
                writer.writerow(result)
        print(f"✅ CSV salvo: {csv_path}")
        
        # Markdown com resumo
        md_path = self.results_dir / f"optimized_retrieval_{timestamp}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Avaliação de Retrieval Otimizado\n\n")
            f.write(f"**Data**: {results['timestamp']}\n")
            f.write(f"**Total de perguntas**: {results['total_questions']}\n")
            f.write(f"**Configurações**: {len(results['configs'])}\n\n")
            
            f.write("## Resumo por Configuração\n\n")
            f.write("| Config | Latência (ms) | Score Médio | Min | Max |\n")
            f.write("|--------|---------------|-------------|-----|-----|\n")
            
            for config in results['configs']:
                config_name = config['name']
                if config_name in results and 'latency_mean_ms' in results[config_name]:
                    agg = results[config_name]
                    f.write(
                        f"| {config_name} | "
                        f"{agg.get('latency_mean_ms', 0):.1f} | "
                        f"{agg.get('score_mean', 0):.4f} | "
                        f"{agg.get('score_min', 0):.4f} | "
                        f"{agg.get('score_max', 0):.4f} |\n"
                    )
        
        print(f"✅ Markdown salvo: {md_path}")
        
        # Imprimir resumo final
        print(f"\n{'='*80}")
        print(f"📊 RESUMO DOS RESULTADOS")
        print(f"{'='*80}\n")
        print(f"{'Config':<20} {'Latência (ms)':<20} {'Score Médio':<15}")
        print(f"{'-'*55}")
        
        for config in results['configs']:
            config_name = config['name']
            if config_name in results and 'latency_mean_ms' in results[config_name]:
                agg = results[config_name]
                print(
                    f"{config_name:<20} "
                    f"{agg.get('latency_mean_ms', 0):>7.1f}±{agg.get('latency_max_ms', 0)-agg.get('latency_min_ms', 0):>6.1f}ms    "
                    f"{agg.get('score_mean', 0):>12.4f}"
                )


def main():
    """Main entry point"""
    print("="*80)
    print("SCRIPT 2.4: Avaliação de Retrieval Otimizado (Simplificado)")
    print("="*80)
    print()
    
    evaluator = OptimizedRetrievalEvaluator()
    success = evaluator.run_evaluation()
    
    if success:
        print(f"\n✅ Avaliação concluída com sucesso!")
    else:
        print(f"\n❌ Erro durante avaliação")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
