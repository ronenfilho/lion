"""
Script para avaliação pura do componente de Retrieval (R) no RAG
- Testa múltiplas estratégias de retrieval (Dense, BM25, Hybrid)
- Varia k (3, 5, 10)
- Coleta métricas de recuperação (latência, scores dos chunks)
- NÃO inclui RAGAS ou evaluation da resposta gerada
- Cache inteligente de embeddings das perguntas
"""

import sys
from pathlib import Path
import json
import hashlib
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.vector_store import VectorStore
from src.retrieval.dense_retriever import DenseRetriever
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.hybrid_retriever import HybridRetriever
from src.ingestion.embeddings_pipeline import EmbeddingsPipeline

from dotenv import load_dotenv
import os

load_dotenv()

# Configurações
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
TEST_DATASET_PATH = "data/datasets/test/manual_rfb_test.json"
EMBEDDINGS_CACHE_PATH = "data/datasets/test/manual_rfb_test_embeddings.json"
RESULTS_DIR = Path("data/experiments/results/retrieval")  # Pasta específica para retrieval

# Configurações de retrieval a testar
RETRIEVAL_CONFIGS = [
    {"method": "dense", "k": 3},
    {"method": "dense", "k": 5},
    {"method": "dense", "k": 10},
    {"method": "bm25", "k": 3},
    {"method": "bm25", "k": 5},
    {"method": "bm25", "k": 10},
    {"method": "hybrid", "k": 3, "dense_weight": 0.7, "bm25_weight": 0.3},
    {"method": "hybrid", "k": 5, "dense_weight": 0.7, "bm25_weight": 0.3},
    {"method": "hybrid", "k": 10, "dense_weight": 0.7, "bm25_weight": 0.3},
    {"method": "hybrid", "k": 5, "dense_weight": 0.5, "bm25_weight": 0.5},
]


class RetrievalEvaluator:
    """Avaliador de estratégias de retrieval"""
    
    def __init__(self):
        """Inicializa o avaliador"""
        self.vector_store = VectorStore(
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME
        )
        self.embeddings_pipeline = EmbeddingsPipeline()
        self.results_dir = RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ RetrievalEvaluator inicializado")
        print(f"   Vector Store: {self.vector_store.count()} documentos")
        print(f"   Collection: {COLLECTION_NAME}")
    
    def _compute_dataset_hash(self, dataset: Dict) -> str:
        """Computa hash do dataset para validação de cache"""
        # Hash baseado nas IDs e perguntas (não inclui embeddings)
        content = json.dumps(
            [(q['id'], q['question']) for q in dataset['questions']],
            sort_keys=True,
            ensure_ascii=False
        )
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_or_create_embeddings_cache(self, dataset: Dict) -> Dict[str, List[float]]:
        """
        Carrega embeddings do cache ou gera novos.
        
        Returns:
            Dict com format: {question_id: [embedding_vector]}
        """
        cache_path = Path(EMBEDDINGS_CACHE_PATH)
        current_hash = self._compute_dataset_hash(dataset)
        
        # Tentar carregar do cache
        if cache_path.exists():
            print(f"\n📦 Verificando cache de embeddings: {cache_path}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            # Validar hash
            if cache.get('metadata', {}).get('dataset_hash') == current_hash:
                print(f"   ✅ Cache válido! ({len(cache['embeddings'])} embeddings)")
                return cache['embeddings']
            else:
                print(f"   ⚠️  Cache inválido (dataset mudou). Regenerando...")
        else:
            print(f"\n🔄 Gerando embeddings para {len(dataset['questions'])} perguntas...")
        
        # Gerar novos embeddings com barra de progresso
        import google.generativeai as genai
        embeddings = {}
        print()
        for qa in tqdm(dataset['questions'], desc="   Processando embeddings", unit="pergunta"):
            question = qa['question']
            question_id = qa['id']
            
            # Gerar embedding usando genai.embed_content
            try:
                result = genai.embed_content(
                    model=self.embeddings_pipeline.model_name,
                    content=question,
                    task_type="retrieval_query"
                )
                embeddings[question_id] = result['embedding']
            except Exception as e:
                print(f"\n⚠️  Erro ao gerar embedding para {question_id}: {e}")
                embeddings[question_id] = None
        
        # Salvar cache
        cache = {
            'metadata': {
                'dataset_path': str(TEST_DATASET_PATH),
                'dataset_hash': current_hash,
                'embedding_model': 'models/gemini-embedding-001',
                'created_at': datetime.now().isoformat(),
                'total_questions': len(dataset['questions'])
            },
            'embeddings': embeddings
        }
        
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        
        print(f"\n   ✅ Cache salvo em: {cache_path}\n")
        return embeddings
    
    def load_test_dataset(self) -> Optional[Dict[str, Any]]:
        """Carrega dataset de teste"""
        dataset_path = Path(TEST_DATASET_PATH)
        
        if not dataset_path.exists():
            print(f"❌ Dataset não encontrado: {TEST_DATASET_PATH}")
            return None
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Extrair perguntas
        if isinstance(dataset, dict) and 'questions' in dataset:
            questions = dataset['questions']
        else:
            questions = dataset if isinstance(dataset, list) else []
        
        print(f"✅ Dataset carregado: {len(questions)} perguntas")
        return {'questions': questions, 'metadata': dataset if isinstance(dataset, dict) else {}}
    
    def create_retrievers(self, config: Dict) -> Optional[Any]:
        """
        Cria retriever baseado na configuração.
        
        Args:
            config: {method, k, dense_weight?, bm25_weight?}
        
        Returns:
            Retriever inicializado
        """
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
                    alpha=config.get('dense_weight', 0.7)
                )
        except Exception as e:
            print(f"   ❌ Erro ao criar retriever: {e}")
            return None
    
    def format_config(self, config: Dict) -> str:
        """Formata configuração para exibição"""
        method = config['method']
        k = config['k']
        
        if method == 'hybrid':
            alpha = config.get('dense_weight', 0.7)
            return f"{method}(k={k}, α={alpha})"
        else:
            return f"{method}(k={k})"
    
    def evaluate_single_query(
        self,
        question: str,
        config: Dict,
        retriever: Any
    ) -> Dict[str, Any]:
        """
        Avalia um retriever com uma pergunta.
        
        Args:
            question: Texto da pergunta
            config: Configuração do retriever
            retriever: Objeto retriever
        
        Returns:
            Métricas de retrieval
        """
        start_time = time.time()
        
        try:
            results = retriever.retrieve(question, top_k=config['k'])
            latency_ms = (time.time() - start_time) * 1000
            
            if not results:
                return {
                    'config': config,
                    'latency_ms': latency_ms,
                    'num_chunks': 0,
                    'top_score': 0,
                    'avg_score': 0,
                    'min_score': 0,
                    'max_score': 0,
                    'error': 'No results'
                }
            
            scores = [r.score for r in results]
            
            # Calcular estatísticas de conteúdo
            total_chars = sum(len(r.content) for r in results)
            total_words = sum(len(r.content.split()) for r in results)
            
            return {
                'config': config,
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
                        'document': r.metadata.get('document', 'N/A'),
                        'section': r.metadata.get('section', 'N/A'),
                        'content': r.content,  # ✅ NOVO: chunk completo
                        'character_count': len(r.content),  # ✅ NOVO
                        'word_count': len(r.content.split())  # ✅ NOVO
                    }
                    for r in results
                ]
            }
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                'config': config,
                'latency_ms': latency_ms,
                'error': str(e)
            }
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Executa avaliação completa"""
        print(f"\n{'='*80}")
        print(f"🧪 AVALIAÇÃO DE RETRIEVAL - Múltiplas Estratégias")
        print(f"{'='*80}\n")
        
        # 1. Carregar dataset
        print("📂 Carregando dataset...")
        dataset = self.load_test_dataset()
        if not dataset:
            return None
        
        questions = dataset['questions']
        
        # 2. Gerenciar cache de embeddings
        embeddings_cache = self._load_or_create_embeddings_cache(dataset)
        
        # 3. Executar avaliação
        print(f"\n📊 Testando {len(RETRIEVAL_CONFIGS)} configurações de retrieval")
        print(f"   com {len(questions)} perguntas")
        print(f"   = {len(RETRIEVAL_CONFIGS) * len(questions)} execuções\n")
        
        all_results = []
        
        # Barra de progresso geral
        total_evaluations = len(RETRIEVAL_CONFIGS) * len(questions)
        pbar = tqdm(total=total_evaluations, desc="🔄 Progresso geral", unit="eval")
        
        for q_idx, qa in enumerate(questions, 1):
            question_id = qa['id']
            question = qa['question']
            
            print(f"\n[{q_idx}/{len(questions)}] {question_id}: {question[:60]}...")
            
            for config_idx, config in enumerate(RETRIEVAL_CONFIGS, 1):
                retriever = self.create_retrievers(config)
                
                if not retriever:
                    print(f"   ❌ Config {config_idx}: Falha na criação do retriever")
                    pbar.update(1)
                    continue
                
                # Avaliar
                result = self.evaluate_single_query(question, config, retriever)
                
                # Adicionar metadados
                result['question_id'] = question_id
                result['question'] = question[:100]  # Preview
                result['config_method'] = config['method']
                result['config_k'] = config['k']
                result['config_dense_weight'] = config.get('dense_weight', None)
                result['config_bm25_weight'] = config.get('bm25_weight', None)
                
                all_results.append(result)
                
                if 'error' not in result:
                    config_str = self.format_config(config)
                    status = f"✅ {config_str}: {result['num_chunks']} chunks | score={result['top_score']:.3f} | lat={result['latency_ms']:.0f}ms"
                else:
                    status = f"❌ {config['method']} k={config['k']}: {result['error']}"
                
                pbar.set_postfix_str(status)
                pbar.update(1)
        
        pbar.close()
        
        # 4. Agregar resultados
        print(f"\n{'='*80}")
        print(f"📈 AGREGAÇÃO DE RESULTADOS")
        print(f"{'='*80}\n")
        
        aggregated = self._aggregate_results(all_results)
        
        # 5. Salvar resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_questions': len(questions),
            'total_configs': len(RETRIEVAL_CONFIGS),
            'total_evaluations': len(all_results),
            'successful_evaluations': len([r for r in all_results if 'error' not in r]),
            'failed_evaluations': len([r for r in all_results if 'error' in r]),
            'aggregated_metrics': aggregated,
            'individual_results': all_results
        }
        
        # Salvar em pasta específica
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar JSON
        json_path = self.results_dir / f"retrieval_evaluation_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON: {json_path}")
        
        # Salvar CSV
        csv_path = self.save_csv_report(all_results, timestamp)
        print(f"✅ CSV: {csv_path}")
        
        # Salvar Markdown
        md_path = self.save_markdown_report(aggregated, timestamp)
        print(f"✅ Markdown: {md_path}\n")
        
        print(f"{'='*80}")
        print(f"✅ AVALIAÇÃO CONCLUÍDA!")
        print(f"{'='*80}")
        print(f"\n📁 Resultados salvos em: {self.results_dir}")
        print(f"   - {json_path.name}")
        print(f"   - {csv_path.name}")
        print(f"   - {md_path.name}\n")
        
        return output_data
    
    def _aggregate_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Agrega resultados por configuração"""
        aggregated = {}
        
        for result in results:
            if 'error' in result:
                continue
            
            method = result['config_method']
            k = result['config_k']
            key = f"{method}_k{k}"
            
            if key not in aggregated:
                aggregated[key] = {
                    'method': method,
                    'k': k,
                    'dense_weight': result['config_dense_weight'],
                    'bm25_weight': result['config_bm25_weight'],
                    'latencies': [],
                    'num_chunks_list': [],
                    'top_scores': [],
                    'avg_scores': [],
                    'count': 0
                }
            
            aggregated[key]['latencies'].append(result['latency_ms'])
            aggregated[key]['num_chunks_list'].append(result['num_chunks'])
            aggregated[key]['top_scores'].append(result['top_score'])
            aggregated[key]['avg_scores'].append(result['avg_score'])
            aggregated[key]['count'] += 1
        
        # Calcular médias
        for key, metrics in aggregated.items():
            if metrics['count'] > 0:
                metrics['avg_latency_ms'] = sum(metrics['latencies']) / metrics['count']
                metrics['avg_num_chunks'] = sum(metrics['num_chunks_list']) / metrics['count']
                metrics['avg_top_score'] = sum(metrics['top_scores']) / metrics['count']
                metrics['avg_avg_score'] = sum(metrics['avg_scores']) / metrics['count']
                metrics['min_latency_ms'] = min(metrics['latencies'])
                metrics['max_latency_ms'] = max(metrics['latencies'])
            
            # Remover listas (não precisam no agregado)
            del metrics['latencies']
            del metrics['num_chunks_list']
            del metrics['top_scores']
            del metrics['avg_scores']
        
        return aggregated
    
    def save_csv_report(self, results: List[Dict], timestamp: str) -> Path:
        """Salva relatório em CSV"""
        csv_path = self.results_dir / f"retrieval_evaluation_{timestamp}.csv"
        
        rows = []
        for result in results:
            if 'error' in result:
                continue
            
            row = {
                'question_id': result['question_id'],
                'question_preview': result['question'],
                'config_method': result['config_method'],
                'config_k': result['config_k'],
                'config_dense_weight': result['config_dense_weight'],
                'config_bm25_weight': result['config_bm25_weight'],
                'latency_ms': f"{result['latency_ms']:.2f}",
                'num_chunks': result['num_chunks'],
                'top_score': f"{result['top_score']:.4f}",
                'avg_score': f"{result['avg_score']:.4f}",
                'min_score': f"{result['min_score']:.4f}",
                'max_score': f"{result['max_score']:.4f}"
            }
            rows.append(row)
        
        if rows:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        return csv_path
    
    def save_markdown_report(self, aggregated: Dict, timestamp: str) -> Path:
        """Salva relatório em Markdown"""
        md_path = self.results_dir / f"retrieval_evaluation_{timestamp}.md"
        
        md_content = []
        md_content.append(f"# Avaliação de Retrieval\n")
        md_content.append(f"**Data**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        md_content.append(f"**Dataset**: {len(aggregated)} configurações testadas\n")
        
        # Tabela de resultados
        md_content.append("\n## Resumo de Configurações\n")
        md_content.append("| Método | K | Latência (ms) | Chunks | Top Score | Avg Score |\n")
        md_content.append("|--------|---|---------------|--------|-----------|----------|\n")
        
        for key in sorted(aggregated.keys()):
            metrics = aggregated[key]
            md_content.append(
                f"| {metrics['method']} | {metrics['k']} | "
                f"{metrics['avg_latency_ms']:.1f}±{metrics['max_latency_ms']-metrics['min_latency_ms']:.1f} | "
                f"{metrics['avg_num_chunks']:.1f} | "
                f"{metrics['avg_top_score']:.4f} | "
                f"{metrics['avg_avg_score']:.4f} |\n"
            )
        
        # Análise por métrica
        md_content.append("\n## Melhores Configurações\n")
        
        # Mais rápido
        fastest = min(aggregated.items(), key=lambda x: x[1]['avg_latency_ms'])
        md_content.append(f"\n⚡ **Mais rápido**: {fastest[0]} ({fastest[1]['avg_latency_ms']:.1f}ms)\n")
        
        # Maior score
        best_top_score = max(aggregated.items(), key=lambda x: x[1]['avg_top_score'])
        md_content.append(f"🏆 **Melhor Top Score**: {best_top_score[0]} ({best_top_score[1]['avg_top_score']:.4f})\n")
        
        # Melhor avg score
        best_avg_score = max(aggregated.items(), key=lambda x: x[1]['avg_avg_score'])
        md_content.append(f"📊 **Melhor Avg Score**: {best_avg_score[0]} ({best_avg_score[1]['avg_avg_score']:.4f})\n")
        
        # Mais chunks
        most_chunks = max(aggregated.items(), key=lambda x: x[1]['avg_num_chunks'])
        md_content.append(f"📦 **Mais chunks**: {most_chunks[0]} ({most_chunks[1]['avg_num_chunks']:.1f})\n")
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        return md_path


def main():
    """Função principal"""
    evaluator = RetrievalEvaluator()
    evaluator.run_evaluation()


if __name__ == '__main__':
    main()
