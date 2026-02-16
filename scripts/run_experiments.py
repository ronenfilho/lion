"""
Experiment Runner - LION
Sistema para execução de experimentos comparativos do RAG
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import time
from tqdm import tqdm
import numpy as np

from src.ingestion.vector_store import VectorStore, create_vector_store
from src.ingestion.embeddings_pipeline import create_embeddings_pipeline
from src.retrieval.dense_retriever import DenseRetriever, create_dense_retriever
from src.retrieval.bm25_retriever import BM25Retriever, create_bm25_retriever
from src.retrieval.hybrid_retriever import HybridRetriever, create_hybrid_retriever
from src.generation.llm_client import LLMClient, GenerationConfig
from src.generation.local_llm_client import LocalLLMClient
from src.generation.groq_client import GroqLLMClient
from src.generation.prompts import PromptManager
from src.evaluation.metrics.ragas_metrics import RAGASEvaluator, create_ragas_evaluator
from src.evaluation.metrics.bertscore import BERTScoreEvaluator


class ExperimentRunner:
    """
    Executa experimentos comparativos com diferentes configurações RAG
    """
    
    def __init__(
        self,
        dataset_path: str,
        results_dir: str = "experiments/results"
    ):
        """
        Inicializa runner de experimentos.
        
        Args:
            dataset_path: Caminho para dataset de teste (JSON)
            results_dir: Diretório para salvar resultados
        """
        self.dataset = self._load_dataset(dataset_path)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar subdiretórios para organização
        self.raw_dir = self.results_dir / "raw"
        self.analysis_dir = self.results_dir / "analysis"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar componentes base
        self.vector_store = create_vector_store()
        self.embeddings = create_embeddings_pipeline()
        self.prompt_manager = PromptManager()
        
        # Avaliadores
        self.ragas_evaluator = create_ragas_evaluator()
        self.bert_evaluator = BERTScoreEvaluator()
        
        print(f"✅ ExperimentRunner inicializado")
        print(f"   Dataset: {len(self.dataset['questions'])} perguntas")
        print(f"   Resultados raw: {self.raw_dir}")
        print(f"   Análises: {self.analysis_dir}")
    
    def _load_dataset(self, path: str) -> Dict:
        """Carrega dataset de teste"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_few_shot_examples(self) -> List[Dict[str, str]]:
        """
        Retorna exemplos para few-shot learning.
        
        Usa as últimas 2 perguntas (29 e 30) do dataset como exemplos.
        
        Returns:
            Lista de dicts com 'question' e 'answer'
        """
        examples = []
        # Perguntas 29 e 30 (índices 28 e 29)
        for i in [28, 29]:
            if i < len(self.dataset['questions']):
                qa = self.dataset['questions'][i]
                examples.append({
                    'question': qa['question'],
                    'answer': qa['ground_truth']
                })
        return examples
    
    def run_experiment(
        self,
        experiment_name: str,
        config: Dict[str, Any],
        max_questions: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executa experimento com configuração específica.
        
        Args:
            experiment_name: Nome do experimento
            config: Configuração do RAG
                - use_rag: bool
                - retrieval_method: 'dense', 'bm25', 'hybrid'
                - k: int (número de chunks)
                - llm: str (modelo)
                - dense_weight: float (para hybrid)
                - bm25_weight: float (para hybrid)
            max_questions: Limite de perguntas (None = todas)
        
        Returns:
            Resultados agregados com métricas
        """
        print(f"\n{'='*70}")
        print(f"🧪 Experimento: {experiment_name}")
        print(f"{'='*70}")
        print(f"Configuração:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print()
        
        # Inicializar componentes baseado na config
        llm_name = config.get('llm', 'gemini-2.5-flash')
        
        # Verificar se é modelo local
        if llm_name.startswith('local:'):
            model_name = llm_name.replace('local:', '')
            llm_client = LocalLLMClient(model_name=model_name, quantize=True)
        # Verificar se é Groq
        elif llm_name.startswith('groq:'):
            model_name = llm_name.replace('groq:', '')
            llm_client = GroqLLMClient(model_name=model_name)
        else:
            llm_client = LLMClient(
                model_name=llm_name,
                config=GenerationConfig(
                    temperature=config.get('temperature', 0.2),
                    max_tokens=config.get('max_tokens', 2048)  # Aumentado para 2048
                )
            )
        
        # Configurar retriever se usar RAG
        retriever = None
        if config.get('use_rag', True):
            retrieval_method = config.get('retrieval_method', 'hybrid')
            k = config.get('k', 5)
            
            if retrieval_method == 'dense':
                retriever = create_dense_retriever(top_k=k)
            elif retrieval_method == 'bm25':
                retriever = create_bm25_retriever(
                    vector_store=self.vector_store,
                    top_k=k
                )
            elif retrieval_method == 'hybrid':
                retriever = create_hybrid_retriever(
                    alpha=config.get('dense_weight', 0.7),
                    top_k=k
                )
        
        # Processar perguntas
        questions = self.dataset['questions']
        
        # Se usar few-shot, excluir as últimas 2 perguntas (29 e 30) do processamento
        if config.get('use_few_shot', False):
            # Processar apenas as primeiras 28 perguntas
            questions = questions[:28]
        
        if max_questions:
            questions = questions[:max_questions]
        
        results = []
        
        for i, qa in enumerate(tqdm(questions, desc="Processando queries"), 1):
            try:
                result = self._process_single_query(
                    qa=qa,
                    llm_client=llm_client,
                    retriever=retriever,
                    config=config
                )
                results.append(result)
            
            except Exception as e:
                print(f"❌ Erro na query {qa['id']}: {e}")
                results.append({
                    'question_id': qa['id'],
                    'question': qa['question'],
                    'error': str(e),
                    'config': config
                })
        
        # Agregar métricas
        aggregated = self._aggregate_metrics(results)
        
        # Salvar resultados
        output_data = {
            'experiment_name': experiment_name,
            'config': config,
            'timestamp': datetime.now().isoformat(),
            'total_questions': len(questions),
            'successful_queries': len([r for r in results if 'error' not in r]),
            'failed_queries': len([r for r in results if 'error' in r]),
            'aggregated_metrics': aggregated,
            'individual_results': results
        }
        
        # Salvar no diretório raw/
        output_path = self.raw_dir / f'{experiment_name}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Experimento concluído!")
        print(f"   Resultados: {output_path}")
        print(f"   Sucesso: {output_data['successful_queries']}/{len(questions)}")
        print(f"\n📊 Métricas Agregadas:")
        for metric, value in sorted(aggregated.items()):
            if isinstance(value, (int, float)):
                print(f"   {metric}: {value:.4f}")
        
        return output_data
    
    def _extract_core_answer(self, full_answer: str) -> str:
        """
        Extrai o conteúdo principal da resposta, removendo saudações e cortesias.
        
        Remove padrões como:
        - "Prezado(a) usuário(a)," + próxima linha
        - "Como assistente especializado..." + próxima linha  
        - Disclaimers no final
        
        Args:
            full_answer: Resposta completa do LLM
        
        Returns:
            Apenas o conteúdo técnico da resposta
        """
        import re
        
        answer = full_answer
        
        # Remover saudações no início (várias variações)
        greetings = [
            r'^Prezado\(a\)\s+usuário\(a\),?\s*\n+',
            r'^Prezado\(a\)\s+contribuinte,?\s*\n+',
            r'^Caro\(a\)\s+usuário\(a\),?\s*\n+',
            r'^Olá,?\s*\n+'
        ]
        
        for pattern in greetings:
            answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
        
        # Remover frases de agradecimento
        answer = re.sub(
            r'^Agradeço\s+sua\s+pergunta[^\n]*\n+',
            '',
            answer,
            flags=re.IGNORECASE
        )
        
        # Remover frase de apresentação do assistente (várias variações)
        answer = re.sub(
            r'^Como assistente especializado[^:,]+[,:]\s+',
            '',
            answer,
            flags=re.IGNORECASE | re.DOTALL
        )
        
        answer = re.sub(
            r'^Como especialista[^:,]+[,:]\s+',
            '',
            answer,
            flags=re.IGNORECASE | re.DOTALL
        )
        
        # Remover disclaimers do final
        answer = re.sub(
            r'\n+⚠️.*$',
            '',
            answer,
            flags=re.MULTILINE | re.DOTALL
        )
        
        answer = re.sub(
            r'\n+Importante:.*$',
            '',
            answer,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        answer = re.sub(
            r'\n+Observação:.*$',
            '',
            answer,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        # Limpar espaços extras
        answer = answer.strip()
        
        return answer
    
    def _process_single_query(
        self,
        qa: Dict,
        llm_client: LLMClient,
        retriever: Optional[Any],
        config: Dict
    ) -> Dict[str, Any]:
        """
        Processa uma única query.
        
        Returns:
            Resultado individual com métricas
        """
        start_time = time.time()
        
        question = qa['question']
        ground_truth = qa['ground_truth']
        
        # Recuperar contexto se usar RAG
        chunks = []
        contexts = []
        
        if retriever:
            retrieval_results = retriever.retrieve(question)
            chunks = [
                {
                    'id': r.id,
                    'content': r.content,
                    'score': r.score,
                    'metadata': r.metadata
                }
                for r in retrieval_results
            ]
            contexts = [r.content for r in retrieval_results]
        
        # Gerar resposta
        if config.get('use_rag', True) and contexts:
            # Verificar se usa few-shot
            if config.get('use_few_shot', False):
                # Carregar exemplos do dataset (perguntas 2-4)
                examples = self._get_few_shot_examples()
                prompt = self.prompt_manager.generate_few_shot_prompt(
                    question=question,
                    context_chunks=contexts,
                    examples=examples
                )
            else:
                # RAG: usar contexto normal
                prompt = self.prompt_manager.generate_rag_prompt(
                    question=question,
                    context_chunks=contexts
                )
        else:
            # Sem RAG: apenas pergunta
            prompt = self.prompt_manager.generate_no_rag_prompt(question)
        
        generation_result = llm_client.generate(prompt)
        full_answer = generation_result.text
        
        # Extrair resposta "pura" para avaliação (sem cortesias)
        core_answer = self._extract_core_answer(full_answer)
        
        latency = (time.time() - start_time) * 1000  # ms
        
        # Calcular métricas
        metrics = {
            'latency_ms': latency,
            'num_chunks': len(chunks),
            'tokens_used': generation_result.tokens_used
        }
        
        # BERTScore - usar core_answer (sem cortesias)
        try:
            bert_result = self.bert_evaluator.evaluate(
                candidates=[core_answer],
                references=[ground_truth]
            )
            metrics['bertscore_precision'] = bert_result.precision
            metrics['bertscore_recall'] = bert_result.recall
            metrics['bertscore_f1'] = bert_result.f1
        except Exception as e:
            print(f"  ⚠️  BERTScore falhou: {e}")
        
        # RAGAS (apenas se usar RAG) - usar core_answer
        if config.get('use_rag', True) and contexts:
            try:
                ragas_scores = self.ragas_evaluator.evaluate(
                    questions=[question],
                    answers=[core_answer],
                    contexts=[contexts],
                    ground_truths=[ground_truth]
                )
                # RAGAS retorna objeto, converter para dict
                ragas_dict = {
                    'answer_relevancy': ragas_scores.answer_relevancy,
                    'faithfulness': ragas_scores.faithfulness
                }
                if ragas_scores.answer_correctness is not None:
                    ragas_dict['answer_correctness'] = ragas_scores.answer_correctness
                if ragas_scores.context_precision is not None:
                    ragas_dict['context_precision'] = ragas_scores.context_precision
                if ragas_scores.context_recall is not None:
                    ragas_dict['context_recall'] = ragas_scores.context_recall
                
                metrics.update(ragas_dict)
            except Exception as e:
                print(f"  ⚠️  RAGAS falhou: {e}")
        
        return {
            'question_id': qa['id'],
            'question': question,
            'answer_full': full_answer,  # Resposta completa com cortesias
            'answer_core': core_answer,  # Resposta pura para comparação
            'ground_truth': ground_truth,
            'chunks': chunks,
            'metrics': metrics,
            'config': config,
            'category': qa.get('category', 'unknown'),
            'difficulty': qa.get('difficulty', 'unknown')
        }
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict[str, float]:
        """
        Calcula média e desvio padrão das métricas.
        
        Args:
            results: Lista de resultados individuais
        
        Returns:
            Métricas agregadas (mean e std para cada métrica)
        """
        # Filtrar resultados com erro
        valid_results = [r for r in results if 'error' not in r]
        
        if not valid_results:
            return {}
        
        # Coletar valores de cada métrica
        metrics_dict = {}
        
        for result in valid_results:
            for metric, value in result['metrics'].items():
                if isinstance(value, (int, float)):
                    if metric not in metrics_dict:
                        metrics_dict[metric] = []
                    metrics_dict[metric].append(value)
        
        # Calcular agregações
        aggregated = {}
        
        for metric, values in metrics_dict.items():
            aggregated[f'{metric}_mean'] = float(np.mean(values))
            aggregated[f'{metric}_std'] = float(np.std(values))
            aggregated[f'{metric}_min'] = float(np.min(values))
            aggregated[f'{metric}_max'] = float(np.max(values))
            aggregated[f'{metric}_median'] = float(np.median(values))
        
        return aggregated
    
    def run_all_experiments(
        self,
        experiment_type: str,
        max_questions: Optional[int] = None
    ):
        """
        Executa todos os experimentos de um tipo.
        
        Args:
            experiment_type: 'rag_vs_no_rag', 'llm_size', 
                           'retrieval_strategy', 'chunk_count'
            max_questions: Limite de perguntas por experimento
        """
        experiments = self._get_experiments_config(experiment_type)
        
        print(f"\n{'#'*70}")
        print(f"🚀 Executando {len(experiments)} experimentos: {experiment_type}")
        print(f"{'#'*70}\n")
        
        all_results = []
        
        for exp_config in experiments:
            result = self.run_experiment(
                experiment_name=f"{experiment_type}_{exp_config['name']}",
                config=exp_config['config'],
                max_questions=max_questions
            )
            all_results.append(result)
            
            # Pausa entre experimentos
            time.sleep(2)
        
        # Salvar sumário
        summary = {
            'experiment_type': experiment_type,
            'timestamp': datetime.now().isoformat(),
            'total_experiments': len(experiments),
            'experiments': [
                {
                    'name': r['experiment_name'],
                    'config': r['config'],
                    'metrics': r['aggregated_metrics']
                }
                for r in all_results
            ]
        }
        
        # Salvar sumário no diretório raw/
        summary_path = self.raw_dir / f'{experiment_type}_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"✅ Todos os experimentos concluídos!")
        print(f"   Sumário: {summary_path}")
        print(f"{'='*70}\n")
    
    def _get_experiments_config(self, experiment_type: str) -> List[Dict]:
        """Define configurações para cada tipo de experimento"""
        
        if experiment_type == 'rag_vs_no_rag':
            return [
                {
                    'name': 'no_rag_baseline',
                    'config': {
                        'use_rag': False,
                        'llm': 'gemini-2.5-flash'
                    }
                },
                {
                    'name': 'rag_dense',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'dense',
                        'k': 5,
                        'llm': 'gemini-2.5-flash'
                    }
                },
                {
                    'name': 'rag_hybrid',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 5,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'gemini-2.5-flash'
                    }
                }
            ]
        
        elif experiment_type == 'retrieval_strategy':
            return [
                {
                    'name': 'dense_only',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'dense',
                        'k': 5,
                        'llm': 'gemini-2.5-flash'
                    }
                },
                {
                    'name': 'bm25_only',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'bm25',
                        'k': 5,
                        'llm': 'gemini-2.5-flash'
                    }
                },
                {
                    'name': 'hybrid_70_30',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 5,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'gemini-2.5-flash'
                    }
                },
                {
                    'name': 'hybrid_50_50',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 5,
                        'dense_weight': 0.5,
                        'bm25_weight': 0.5,
                        'llm': 'gemini-2.5-flash'
                    }
                }
            ]
        
        elif experiment_type == 'chunk_count':
            return [
                {
                    'name': 'k3',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 3,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'gemini-2.5-flash'
                    }
                },
                {
                    'name': 'k5',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 5,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'gemini-2.5-flash'
                    }
                },
                {
                    'name': 'k10',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 10,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'gemini-2.5-flash'
                    }
                }
            ]
        
        elif experiment_type == 'llm_size':
            return [
                {
                    'name': 'flash_with_rag',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 5,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'gemini-2.0-flash'
                    }
                },
                {
                    'name': 'flash_no_rag',
                    'config': {
                        'use_rag': False,
                        'llm': 'gemini-2.5-flash'
                    }
                }
            ]

        elif experiment_type == 'local_model_comparison':
            return [
                {
                    'name': 'tinyllama_with_rag',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'dense',
                        'k': 3,
                        'llm': 'local:tinyllama'
                    }
                },
                {
                    'name': 'tinyllama_few_shot_with_rag',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'dense',
                        'k': 3,
                        'llm': 'local:tinyllama',
                        'use_few_shot': True
                    }
                }
            ]

        elif experiment_type == 'model_comparison':
            return [
                # === BASELINE (Sem RAG) ===
                {
                    'name': 'groq_llama_3.1_8b_baseline',
                    'config': {
                        'use_rag': False,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': False
                    }
                },
                
                # === VARIAÇÕES k=3 ===
                {
                    'name': 'groq_k3_dense_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'dense',
                        'k': 3,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k3_bm25_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'bm25',
                        'k': 3,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k3_hybrid_70_30_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 3,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k3_hybrid_50_50_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 3,
                        'dense_weight': 0.5,
                        'bm25_weight': 0.5,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                
                # === VARIAÇÕES k=5 ===
                {
                    'name': 'groq_k5_dense_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'dense',
                        'k': 5,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k5_bm25_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'bm25',
                        'k': 5,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k5_hybrid_70_30_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 5,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k5_hybrid_50_50_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 5,
                        'dense_weight': 0.5,
                        'bm25_weight': 0.5,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                
                # === VARIAÇÕES k=10 ===
                {
                    'name': 'groq_k10_dense_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'dense',
                        'k': 10,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k10_bm25_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'bm25',
                        'k': 10,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k10_hybrid_70_30_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 10,
                        'dense_weight': 0.7,
                        'bm25_weight': 0.3,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                },
                {
                    'name': 'groq_k10_hybrid_50_50_few_shot',
                    'config': {
                        'use_rag': True,
                        'retrieval_method': 'hybrid',
                        'k': 10,
                        'dense_weight': 0.5,
                        'bm25_weight': 0.5,
                        'llm': 'groq:llama-3.1-8b-instant',
                        'use_few_shot': True
                    }
                }
            ]
                    
        else:
            raise ValueError(f"Tipo de experimento desconhecido: {experiment_type}")


def main():
    parser = argparse.ArgumentParser(
        description='Executa experimentos comparativos do RAG'
    )
    
    parser.add_argument(
        '--experiment',
        required=True,
        choices=['rag_vs_no_rag', 'retrieval_strategy', 'chunk_count', 'llm_size', 'model_comparison'],
        help='Tipo de experimento a executar'
    )
    
    parser.add_argument(
        '--dataset',
        default='experiments/datasets/manual_rfb_test.json',
        help='Caminho para dataset de teste'
    )
    
    parser.add_argument(
        '--max-questions',
        type=int,
        default=None,
        help='Número máximo de perguntas (None = todas)'
    )
    
    parser.add_argument(
        '--results-dir',
        default='experiments/results',
        help='Diretório para salvar resultados'
    )
    
    args = parser.parse_args()
    
    # Criar runner
    runner = ExperimentRunner(
        dataset_path=args.dataset,
        results_dir=args.results_dir
    )
    
    # Executar experimentos
    runner.run_all_experiments(
        experiment_type=args.experiment,
        max_questions=args.max_questions
    )


if __name__ == '__main__':
    main()
