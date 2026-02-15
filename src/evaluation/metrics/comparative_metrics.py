"""
Comparative Metrics - LION
Métricas para comparar diferentes configurações do sistema RAG
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time
import statistics


@dataclass
class SystemConfig:
    """Configuração do sistema para experimento"""
    name: str
    retriever_type: str  # 'dense', 'bm25', 'hybrid'
    llm_provider: str  # 'gemini', 'openai', etc.
    llm_model: str
    temperature: float
    top_k: int
    chunk_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    """Resultado de uma execução"""
    query: str
    answer: str
    retrieved_chunks: List[str]
    context_used: str
    latency_ms: float
    tokens_used: int
    
    # Métricas RAG
    faithfulness: float
    answer_relevance: float
    hallucination_score: float
    has_citations: bool
    
    # Metadata
    timestamp: float
    config: SystemConfig


@dataclass
class ComparisonReport:
    """Relatório de comparação entre configurações"""
    configs: List[SystemConfig]
    results_by_config: Dict[str, List[RunResult]]
    
    # Métricas agregadas por config
    avg_latency: Dict[str, float]
    avg_faithfulness: Dict[str, float]
    avg_relevance: Dict[str, float]
    avg_hallucination: Dict[str, float]
    citation_rate: Dict[str, float]
    
    # Ranking
    best_config: str
    ranking: List[tuple]  # (config_name, overall_score)


class ComparativeEvaluator:
    """
    Avaliador comparativo para diferentes configurações RAG.
    
    Permite comparar:
    - Diferentes retrievers (dense vs BM25 vs hybrid)
    - Diferentes LLMs (Gemini vs OpenAI vs Anthropic)
    - Diferentes parâmetros (temperature, top_k, chunk_size)
    """
    
    def __init__(self):
        """Inicializa avaliador comparativo."""
        self.results: Dict[str, List[RunResult]] = {}
    
    def add_result(self, config_name: str, result: RunResult):
        """
        Adiciona resultado de execução.
        
        Args:
            config_name: Nome da configuração
            result: Resultado da execução
        """
        if config_name not in self.results:
            self.results[config_name] = []
        
        self.results[config_name].append(result)
    
    def compare(self, config_names: Optional[List[str]] = None) -> ComparisonReport:
        """
        Compara configurações.
        
        Args:
            config_names: Lista de configs para comparar (None = todas)
            
        Returns:
            ComparisonReport com análise comparativa
        """
        if config_names is None:
            config_names = list(self.results.keys())
        
        # Calcular métricas agregadas
        avg_latency = {}
        avg_faithfulness = {}
        avg_relevance = {}
        avg_hallucination = {}
        citation_rate = {}
        
        for config_name in config_names:
            results = self.results.get(config_name, [])
            
            if not results:
                continue
            
            # Latência
            latencies = [r.latency_ms for r in results]
            avg_latency[config_name] = statistics.mean(latencies)
            
            # Faithfulness
            faithfulness_scores = [r.faithfulness for r in results]
            avg_faithfulness[config_name] = statistics.mean(faithfulness_scores)
            
            # Relevância
            relevance_scores = [r.answer_relevance for r in results]
            avg_relevance[config_name] = statistics.mean(relevance_scores)
            
            # Alucinação
            hallucination_scores = [r.hallucination_score for r in results]
            avg_hallucination[config_name] = statistics.mean(hallucination_scores)
            
            # Taxa de citações
            citations = [1 if r.has_citations else 0 for r in results]
            citation_rate[config_name] = statistics.mean(citations)
        
        # Ranking (score ponderado)
        ranking = []
        for config_name in config_names:
            if config_name not in avg_faithfulness:
                continue
            
            # Score composto
            score = (
                0.25 * avg_faithfulness[config_name] +
                0.25 * avg_relevance[config_name] +
                0.20 * (1 - avg_hallucination[config_name]) +
                0.15 * citation_rate[config_name] +
                0.15 * (1 - min(1.0, avg_latency[config_name] / 5000))  # Normalizar latência
            )
            
            ranking.append((config_name, score))
        
        # Ordenar por score
        ranking.sort(key=lambda x: x[1], reverse=True)
        best_config = ranking[0][0] if ranking else None
        
        # Extrair configurações
        configs = []
        for config_name in config_names:
            results = self.results.get(config_name, [])
            if results:
                configs.append(results[0].config)
        
        return ComparisonReport(
            configs=configs,
            results_by_config={k: v for k, v in self.results.items() if k in config_names},
            avg_latency=avg_latency,
            avg_faithfulness=avg_faithfulness,
            avg_relevance=avg_relevance,
            avg_hallucination=avg_hallucination,
            citation_rate=citation_rate,
            best_config=best_config,
            ranking=ranking
        )
    
    def print_comparison(self, report: ComparisonReport):
        """
        Imprime relatório de comparação formatado.
        
        Args:
            report: Relatório de comparação
        """
        print("\n📊 RELATÓRIO DE COMPARAÇÃO")
        print("=" * 80)
        
        # Cabeçalho
        print(f"\n{'Config':<20} {'Latency':<12} {'Faith':<8} {'Relev':<8} {'Halluc':<8} {'Cites':<8} {'Score':<8}")
        print("-" * 80)
        
        # Dados
        for config_name, overall_score in report.ranking:
            latency = report.avg_latency.get(config_name, 0)
            faith = report.avg_faithfulness.get(config_name, 0)
            relev = report.avg_relevance.get(config_name, 0)
            halluc = report.avg_hallucination.get(config_name, 0)
            cites = report.citation_rate.get(config_name, 0)
            
            # Marcar melhor config
            marker = "🏆" if config_name == report.best_config else "  "
            
            print(f"{marker} {config_name:<18} "
                  f"{latency:>8.0f}ms   "
                  f"{faith:>6.2f}   "
                  f"{relev:>6.2f}   "
                  f"{halluc:>6.2f}   "
                  f"{cites:>6.1%}   "
                  f"{overall_score:>6.2f}")
        
        print("\n" + "=" * 80)
        print(f"🏆 Melhor configuração: {report.best_config}")
    
    def analyze_trade_offs(self, report: ComparisonReport) -> Dict[str, str]:
        """
        Analisa trade-offs entre configurações.
        
        Args:
            report: Relatório de comparação
            
        Returns:
            Dict com insights sobre trade-offs
        """
        insights = {}
        
        # Fastest vs Best Quality
        fastest = min(report.avg_latency.items(), key=lambda x: x[1])
        highest_faith = max(report.avg_faithfulness.items(), key=lambda x: x[1])
        
        insights['fastest'] = f"{fastest[0]} ({fastest[1]:.0f}ms)"
        insights['highest_quality'] = f"{highest_faith[0]} (faithfulness: {highest_faith[1]:.2f})"
        
        # Most citations
        most_cites = max(report.citation_rate.items(), key=lambda x: x[1])
        insights['most_citations'] = f"{most_cites[0]} ({most_cites[1]:.1%})"
        
        # Lowest hallucination
        lowest_halluc = min(report.avg_hallucination.items(), key=lambda x: x[1])
        insights['safest'] = f"{lowest_halluc[0]} (hallucination: {lowest_halluc[1]:.2f})"
        
        return insights
    
    def export_to_csv(self, report: ComparisonReport, filename: str):
        """
        Exporta resultados para CSV.
        
        Args:
            report: Relatório
            filename: Nome do arquivo
        """
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Config', 'Latency_ms', 'Faithfulness', 'Relevance',
                'Hallucination', 'Citation_Rate', 'Overall_Score'
            ])
            
            # Dados
            for config_name, overall_score in report.ranking:
                writer.writerow([
                    config_name,
                    f"{report.avg_latency[config_name]:.2f}",
                    f"{report.avg_faithfulness[config_name]:.2f}",
                    f"{report.avg_relevance[config_name]:.2f}",
                    f"{report.avg_hallucination[config_name]:.2f}",
                    f"{report.citation_rate[config_name]:.2f}",
                    f"{overall_score:.2f}"
                ])
        
        print(f"✅ Resultados exportados para {filename}")


class ABTestRunner:
    """
    Runner para testes A/B entre configurações.
    
    Facilita comparação head-to-head entre duas configurações.
    """
    
    def __init__(self, config_a: SystemConfig, config_b: SystemConfig):
        """
        Inicializa A/B test.
        
        Args:
            config_a: Configuração A
            config_b: Configuração B
        """
        self.config_a = config_a
        self.config_b = config_b
        self.results_a = []
        self.results_b = []
    
    def add_result_a(self, result: RunResult):
        """Adiciona resultado da configuração A."""
        self.results_a.append(result)
    
    def add_result_b(self, result: RunResult):
        """Adiciona resultado da configuração B."""
        self.results_b.append(result)
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analisa resultados do A/B test.
        
        Returns:
            Dict com análise comparativa
        """
        if not self.results_a or not self.results_b:
            return {'error': 'Sem resultados suficientes'}
        
        # Métricas A
        faith_a = statistics.mean([r.faithfulness for r in self.results_a])
        relev_a = statistics.mean([r.answer_relevance for r in self.results_a])
        latency_a = statistics.mean([r.latency_ms for r in self.results_a])
        
        # Métricas B
        faith_b = statistics.mean([r.faithfulness for r in self.results_b])
        relev_b = statistics.mean([r.answer_relevance for r in self.results_b])
        latency_b = statistics.mean([r.latency_ms for r in self.results_b])
        
        # Diferenças
        faith_diff = ((faith_b - faith_a) / faith_a) * 100 if faith_a > 0 else 0
        relev_diff = ((relev_b - relev_a) / relev_a) * 100 if relev_a > 0 else 0
        latency_diff = ((latency_b - latency_a) / latency_a) * 100 if latency_a > 0 else 0
        
        # Vencedor
        score_a = faith_a * 0.5 + relev_a * 0.5
        score_b = faith_b * 0.5 + relev_b * 0.5
        
        winner = 'A' if score_a > score_b else 'B'
        improvement = abs(score_b - score_a) / score_a * 100 if score_a > 0 else 0
        
        return {
            'config_a': self.config_a.name,
            'config_b': self.config_b.name,
            'faithfulness_a': faith_a,
            'faithfulness_b': faith_b,
            'faithfulness_diff_pct': faith_diff,
            'relevance_a': relev_a,
            'relevance_b': relev_b,
            'relevance_diff_pct': relev_diff,
            'latency_a': latency_a,
            'latency_b': latency_b,
            'latency_diff_pct': latency_diff,
            'winner': winner,
            'improvement_pct': improvement
        }
    
    def print_analysis(self):
        """Imprime análise do A/B test."""
        analysis = self.analyze()
        
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
            return
        
        print("\n🔬 A/B TEST ANALYSIS")
        print("=" * 60)
        print(f"\n📌 Config A: {analysis['config_a']}")
        print(f"📌 Config B: {analysis['config_b']}")
        
        print(f"\n📊 Métricas:")
        print(f"   Faithfulness:  A={analysis['faithfulness_a']:.2f}  B={analysis['faithfulness_b']:.2f}  "
              f"({analysis['faithfulness_diff_pct']:+.1f}%)")
        print(f"   Relevance:     A={analysis['relevance_a']:.2f}  B={analysis['relevance_b']:.2f}  "
              f"({analysis['relevance_diff_pct']:+.1f}%)")
        print(f"   Latency:       A={analysis['latency_a']:.0f}ms  B={analysis['latency_b']:.0f}ms  "
              f"({analysis['latency_diff_pct']:+.1f}%)")
        
        print(f"\n🏆 Vencedor: Config {analysis['winner']} "
              f"(+{analysis['improvement_pct']:.1f}% melhor)")


def create_comparative_evaluator() -> ComparativeEvaluator:
    """
    Factory function para criar avaliador comparativo.
    
    Returns:
        ComparativeEvaluator
    """
    return ComparativeEvaluator()


# Exemplo de uso
if __name__ == "__main__":
    print("🧪 TESTE DO COMPARATIVE EVALUATOR")
    print("=" * 60)
    
    # Criar avaliador
    evaluator = create_comparative_evaluator()
    
    # Simular configurações
    config_hybrid = SystemConfig(
        name='hybrid_gemini',
        retriever_type='hybrid',
        llm_provider='gemini',
        llm_model='gemini-2.0-flash',
        temperature=0.2,
        top_k=5,
        chunk_size=800
    )
    
    config_dense = SystemConfig(
        name='dense_gemini',
        retriever_type='dense',
        llm_provider='gemini',
        llm_model='gemini-2.0-flash',
        temperature=0.2,
        top_k=5,
        chunk_size=800
    )
    
    # Simular resultados
    for i in range(5):
        # Hybrid (melhor qualidade, mais lento)
        evaluator.add_result('hybrid_gemini', RunResult(
            query=f"Query {i}",
            answer="Resposta com citações...",
            retrieved_chunks=[],
            context_used="",
            latency_ms=1200 + i * 50,
            tokens_used=150,
            faithfulness=0.85 + i * 0.02,
            answer_relevance=0.90 + i * 0.01,
            hallucination_score=0.10,
            has_citations=True,
            timestamp=time.time(),
            config=config_hybrid
        ))
        
        # Dense (mais rápido, qualidade um pouco menor)
        evaluator.add_result('dense_gemini', RunResult(
            query=f"Query {i}",
            answer="Resposta...",
            retrieved_chunks=[],
            context_used="",
            latency_ms=800 + i * 30,
            tokens_used=150,
            faithfulness=0.75 + i * 0.02,
            answer_relevance=0.80 + i * 0.01,
            hallucination_score=0.15,
            has_citations=True,
            timestamp=time.time(),
            config=config_dense
        ))
    
    # Comparar
    report = evaluator.compare()
    evaluator.print_comparison(report)
    
    # Trade-offs
    print("\n\n💡 ANÁLISE DE TRADE-OFFS")
    print("=" * 60)
    insights = evaluator.analyze_trade_offs(report)
    for key, value in insights.items():
        print(f"   • {key}: {value}")
