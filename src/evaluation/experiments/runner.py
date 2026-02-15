"""
Experiment Runner - LION
Sistema para execução automatizada de experimentos RAG
"""

import json
import time
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
import statistics

from ..metrics.rag_metrics import RAGEvaluator, RAGMetrics
from ..metrics.comparative_metrics import (
    ComparativeEvaluator, SystemConfig, RunResult, ComparisonReport
)


@dataclass
class ExperimentConfig:
    """Configuração de experimento"""
    name: str
    description: str
    dataset_path: str
    configs: List[SystemConfig]
    output_dir: str
    max_queries: Optional[int] = None  # Limite de queries para teste rápido


@dataclass
class QueryResult:
    """Resultado de uma query individual"""
    query_id: str
    query: str
    config_name: str
    answer: str
    retrieved_chunks: List[str]
    context: str
    metrics: RAGMetrics
    latency_ms: float
    timestamp: float


@dataclass
class ExperimentReport:
    """Relatório de experimento completo"""
    experiment_name: str
    total_queries: int
    configs_tested: List[str]
    results: List[QueryResult]
    comparison: ComparisonReport
    insights: Dict[str, Any]
    duration_seconds: float


class ExperimentRunner:
    """
    Runner para execução automatizada de experimentos RAG.
    
    Funcionalidades:
    - Carregar datasets de perguntas/respostas
    - Executar múltiplas configurações em paralelo
    - Agregar métricas e gerar relatórios
    - Exportar resultados em múltiplos formatos
    """
    
    def __init__(
        self,
        output_dir: str = "experiments/results",
        verbose: bool = True
    ):
        """
        Inicializa runner de experimentos.
        
        Args:
            output_dir: Diretório para salvar resultados
            verbose: Se True, imprime progresso
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        self.rag_evaluator = RAGEvaluator()
        self.comparative_evaluator = ComparativeEvaluator()
    
    def load_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """
        Carrega dataset de queries.
        
        Formato esperado (JSON):
        [
            {
                "id": "q1",
                "query": "Como declarar aposentadoria?",
                "expected_topics": ["aposentadoria", "rendimentos"],
                "relevant_doc_ids": ["doc_123", "doc_456"]
            },
            ...
        ]
        
        Args:
            dataset_path: Caminho para arquivo JSON
            
        Returns:
            Lista de queries
        """
        dataset_path = Path(dataset_path)
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset não encontrado: {dataset_path}")
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        if self.verbose:
            print(f"✅ Dataset carregado: {len(dataset)} queries")
        
        return dataset
    
    def run_experiment(
        self,
        config: ExperimentConfig,
        query_executor: Callable[[str, SystemConfig], Dict[str, Any]]
    ) -> ExperimentReport:
        """
        Executa experimento completo.
        
        Args:
            config: Configuração do experimento
            query_executor: Função que executa query e retorna resultado
                Assinatura: (query: str, sys_config: SystemConfig) -> Dict
                Retorno esperado: {
                    'answer': str,
                    'retrieved_chunks': List[str],
                    'context': str,
                    'retrieved_ids': List[str],
                    'latency_ms': float,
                    'tokens_used': int
                }
        
        Returns:
            ExperimentReport com resultados completos
        """
        start_time = time.time()
        
        if self.verbose:
            print(f"\n🧪 INICIANDO EXPERIMENTO: {config.name}")
            print("=" * 80)
            print(f"📝 {config.description}")
            print(f"📊 Dataset: {config.dataset_path}")
            print(f"🔧 Configurações: {len(config.configs)}")
        
        # Carregar dataset
        dataset = self.load_dataset(config.dataset_path)
        
        # Limitar queries se necessário
        if config.max_queries:
            dataset = dataset[:config.max_queries]
            if self.verbose:
                print(f"⚠️  Limitando a {config.max_queries} queries para teste")
        
        # Executar queries para cada configuração
        all_results = []
        
        for sys_config in config.configs:
            if self.verbose:
                print(f"\n▶️  Testando configuração: {sys_config.name}")
                print(f"   Retriever: {sys_config.retriever_type}")
                print(f"   LLM: {sys_config.llm_provider}/{sys_config.llm_model}")
                print(f"   Temperature: {sys_config.temperature}, Top-K: {sys_config.top_k}")
            
            config_results = self._run_config(
                sys_config=sys_config,
                queries=dataset,
                query_executor=query_executor
            )
            
            all_results.extend(config_results)
        
        # Análise comparativa
        if self.verbose:
            print("\n📊 Gerando análise comparativa...")
        
        comparison = self.comparative_evaluator.compare()
        insights = self._generate_insights(all_results, comparison)
        
        # Relatório
        duration = time.time() - start_time
        
        report = ExperimentReport(
            experiment_name=config.name,
            total_queries=len(dataset),
            configs_tested=[c.name for c in config.configs],
            results=all_results,
            comparison=comparison,
            insights=insights,
            duration_seconds=duration
        )
        
        # Salvar resultados
        self._save_report(report, config.output_dir)
        
        if self.verbose:
            print(f"\n✅ Experimento concluído em {duration:.1f}s")
            print(f"📁 Resultados salvos em: {config.output_dir}")
        
        return report
    
    def _run_config(
        self,
        sys_config: SystemConfig,
        queries: List[Dict[str, Any]],
        query_executor: Callable
    ) -> List[QueryResult]:
        """
        Executa queries para uma configuração específica.
        
        Args:
            sys_config: Configuração do sistema
            queries: Lista de queries
            query_executor: Função para executar query
            
        Returns:
            Lista de QueryResult
        """
        results = []
        
        for i, query_data in enumerate(queries, 1):
            if self.verbose and i % 10 == 0:
                print(f"   Progresso: {i}/{len(queries)}")
            
            query_text = query_data['query']
            query_id = query_data.get('id', f'q{i}')
            relevant_ids = query_data.get('relevant_doc_ids', [])
            
            try:
                # Executar query
                exec_result = query_executor(query_text, sys_config)
                
                # Avaliar com RAG metrics
                retrieved_ids = exec_result.get('retrieved_ids', [])
                
                metrics = self.rag_evaluator.evaluate_full_rag(
                    question=query_text,
                    answer=exec_result['answer'],
                    context_chunks=exec_result['retrieved_chunks'],
                    retrieved_chunk_ids=retrieved_ids if retrieved_ids else None,
                    relevant_chunk_ids=relevant_ids if relevant_ids else None
                )
                
                # Criar resultado
                result = QueryResult(
                    query_id=query_id,
                    query=query_text,
                    config_name=sys_config.name,
                    answer=exec_result['answer'],
                    retrieved_chunks=exec_result['retrieved_chunks'],
                    context=exec_result['context'],
                    metrics=metrics,
                    latency_ms=exec_result['latency_ms'],
                    timestamp=time.time()
                )
                
                results.append(result)
                
                # Adicionar ao avaliador comparativo
                run_result = RunResult(
                    query=query_text,
                    answer=exec_result['answer'],
                    retrieved_chunks=exec_result['retrieved_chunks'],
                    context_used=exec_result['context'],
                    latency_ms=exec_result['latency_ms'],
                    tokens_used=exec_result.get('tokens_used', 0),
                    faithfulness=metrics.faithfulness,
                    answer_relevance=metrics.answer_relevance,
                    hallucination_score=metrics.hallucination_score,
                    has_citations=metrics.has_citations,
                    timestamp=time.time(),
                    config=sys_config
                )
                
                self.comparative_evaluator.add_result(sys_config.name, run_result)
                
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Erro na query {query_id}: {e}")
                continue
        
        if self.verbose:
            print(f"   ✅ Completado: {len(results)}/{len(queries)} queries")
        
        return results
    
    def _generate_insights(
        self,
        results: List[QueryResult],
        comparison: ComparisonReport
    ) -> Dict[str, Any]:
        """
        Gera insights sobre os resultados.
        
        Args:
            results: Resultados das queries
            comparison: Comparação entre configurações
            
        Returns:
            Dict com insights
        """
        insights = {}
        
        # Trade-offs
        insights['trade_offs'] = self.comparative_evaluator.analyze_trade_offs(comparison)
        
        # Queries problemáticas (baixa qualidade)
        low_quality = [
            r for r in results
            if r.metrics.overall_score < 0.5
        ]
        
        insights['low_quality_count'] = len(low_quality)
        insights['low_quality_queries'] = [
            {'id': r.query_id, 'query': r.query, 'score': r.metrics.overall_score}
            for r in low_quality[:5]  # Top 5 piores
        ]
        
        # Alucinações
        high_hallucination = [
            r for r in results
            if r.metrics.hallucination_score > 0.3
        ]
        
        insights['high_hallucination_count'] = len(high_hallucination)
        
        # Taxa de citações
        with_citations = [r for r in results if r.metrics.has_citations]
        insights['citation_rate'] = len(with_citations) / len(results) if results else 0
        
        return insights
    
    def _save_report(self, report: ExperimentReport, output_dir: str):
        """
        Salva relatório em múltiplos formatos.
        
        Args:
            report: Relatório do experimento
            output_dir: Diretório de saída
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # JSON completo
        json_path = output_path / "report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self._report_to_dict(report), f, indent=2, ensure_ascii=False)
        
        # CSV com métricas agregadas
        csv_path = output_path / "metrics.csv"
        self._export_metrics_csv(report, csv_path)
        
        # Texto legível
        txt_path = output_path / "summary.txt"
        self._export_summary_txt(report, txt_path)
        
        if self.verbose:
            print(f"   📄 JSON: {json_path}")
            print(f"   📊 CSV: {csv_path}")
            print(f"   📝 TXT: {txt_path}")
    
    def _report_to_dict(self, report: ExperimentReport) -> Dict:
        """Converte relatório para dict serializável."""
        return {
            'experiment_name': report.experiment_name,
            'total_queries': report.total_queries,
            'configs_tested': report.configs_tested,
            'duration_seconds': report.duration_seconds,
            'results': [
                {
                    'query_id': r.query_id,
                    'query': r.query,
                    'config_name': r.config_name,
                    'answer': r.answer,
                    'latency_ms': r.latency_ms,
                    'metrics': asdict(r.metrics)
                }
                for r in report.results
            ],
            'comparison': {
                'best_config': report.comparison.best_config,
                'ranking': report.comparison.ranking,
                'avg_latency': report.comparison.avg_latency,
                'avg_faithfulness': report.comparison.avg_faithfulness,
                'avg_relevance': report.comparison.avg_relevance
            },
            'insights': report.insights
        }
    
    def _export_metrics_csv(self, report: ExperimentReport, csv_path: Path):
        """Exporta métricas para CSV."""
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Config', 'Latency_ms', 'Faithfulness', 'Answer_Relevance',
                'Context_Relevance', 'Hallucination', 'Citation_Rate', 'Overall_Score'
            ])
            
            # Dados
            for config_name, score in report.comparison.ranking:
                writer.writerow([
                    config_name,
                    f"{report.comparison.avg_latency[config_name]:.2f}",
                    f"{report.comparison.avg_faithfulness[config_name]:.2f}",
                    f"{report.comparison.avg_relevance[config_name]:.2f}",
                    0,  # Context relevance (não temos no comparison)
                    f"{report.comparison.avg_hallucination[config_name]:.2f}",
                    f"{report.comparison.citation_rate[config_name]:.2f}",
                    f"{score:.2f}"
                ])
    
    def _export_summary_txt(self, report: ExperimentReport, txt_path: Path):
        """Exporta resumo em texto."""
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"EXPERIMENTO: {report.experiment_name}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total de queries: {report.total_queries}\n")
            f.write(f"Configurações testadas: {len(report.configs_tested)}\n")
            f.write(f"Duração: {report.duration_seconds:.1f}s\n\n")
            
            f.write("RANKING:\n")
            f.write("-" * 80 + "\n")
            for i, (config_name, score) in enumerate(report.comparison.ranking, 1):
                marker = "🏆" if i == 1 else f"{i}."
                f.write(f"{marker} {config_name}: {score:.3f}\n")
            
            f.write("\n\nINSIGHTS:\n")
            f.write("-" * 80 + "\n")
            
            insights = report.insights
            f.write(f"Queries com baixa qualidade: {insights['low_quality_count']}\n")
            f.write(f"Queries com alucinação alta: {insights['high_hallucination_count']}\n")
            f.write(f"Taxa de citações: {insights['citation_rate']:.1%}\n")
            
            f.write("\n\nTRADE-OFFS:\n")
            f.write("-" * 80 + "\n")
            for key, value in insights['trade_offs'].items():
                f.write(f"  • {key}: {value}\n")
    
    def print_report(self, report: ExperimentReport):
        """
        Imprime relatório formatado no console.
        
        Args:
            report: Relatório do experimento
        """
        print("\n\n" + "=" * 80)
        print(f"📊 RELATÓRIO DO EXPERIMENTO: {report.experiment_name}")
        print("=" * 80)
        
        print(f"\n📈 Resumo:")
        print(f"   Total de queries: {report.total_queries}")
        print(f"   Configs testadas: {len(report.configs_tested)}")
        print(f"   Duração: {report.duration_seconds:.1f}s")
        
        # Ranking
        print("\n🏆 Ranking:")
        self.comparative_evaluator.print_comparison(report.comparison)
        
        # Insights
        print("\n💡 Insights:")
        print(f"   • Queries com baixa qualidade: {report.insights['low_quality_count']}")
        print(f"   • Queries com alta alucinação: {report.insights['high_hallucination_count']}")
        print(f"   • Taxa de citações: {report.insights['citation_rate']:.1%}")
        
        if report.insights['low_quality_queries']:
            print("\n   Queries problemáticas (top 5):")
            for q in report.insights['low_quality_queries']:
                print(f"      - [{q['id']}] {q['query'][:60]}... (score: {q['score']:.2f})")
        
        print("\n   Trade-offs:")
        for key, value in report.insights['trade_offs'].items():
            print(f"      • {key}: {value}")


def create_experiment_runner(
    output_dir: str = "experiments/results",
    verbose: bool = True
) -> ExperimentRunner:
    """
    Factory function para criar runner de experimentos.
    
    Args:
        output_dir: Diretório para resultados
        verbose: Se True, imprime progresso
        
    Returns:
        ExperimentRunner
    """
    return ExperimentRunner(output_dir=output_dir, verbose=verbose)


# Exemplo de uso
if __name__ == "__main__":
    print("🧪 TESTE DO EXPERIMENT RUNNER")
    print("=" * 80)
    
    # Mock query executor
    def mock_query_executor(query: str, config: SystemConfig) -> Dict[str, Any]:
        """Simula execução de query."""
        time.sleep(0.1)  # Simular latência
        
        return {
            'answer': f"Resposta simulada para: {query}",
            'retrieved_chunks': [
                "Chunk 1 relevante",
                "Chunk 2 relevante"
            ],
            'context': "Contexto simulado...",
            'retrieved_ids': ['doc1', 'doc2'],
            'latency_ms': 120.5,
            'tokens_used': 150
        }
    
    # Criar dataset de exemplo
    dataset = [
        {
            'id': 'q1',
            'query': 'Como declarar aposentadoria?',
            'relevant_doc_ids': ['doc1', 'doc2']
        },
        {
            'id': 'q2',
            'query': 'Posso deduzir plano de saúde?',
            'relevant_doc_ids': ['doc3', 'doc4']
        }
    ]
    
    dataset_path = Path("experiments/test_dataset.json")
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Dataset de teste criado: {dataset_path}")
    
    # Configurar experimento
    exp_config = ExperimentConfig(
        name="Teste Comparativo",
        description="Comparação entre retriever dense e hybrid",
        dataset_path=str(dataset_path),
        configs=[
            SystemConfig(
                name='dense_gemini',
                retriever_type='dense',
                llm_provider='gemini',
                llm_model='gemini-2.0-flash',
                temperature=0.2,
                top_k=5,
                chunk_size=800
            ),
            SystemConfig(
                name='hybrid_gemini',
                retriever_type='hybrid',
                llm_provider='gemini',
                llm_model='gemini-2.0-flash',
                temperature=0.2,
                top_k=5,
                chunk_size=800
            )
        ],
        output_dir="experiments/test_results"
    )
    
    # Executar
    runner = create_experiment_runner(verbose=True)
    
    try:
        report = runner.run_experiment(exp_config, mock_query_executor)
        runner.print_report(report)
    except Exception as e:
        print(f"❌ Erro no experimento: {e}")
