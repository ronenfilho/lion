"""
Analyze Results - LION
Script para análise estatística e visualização de resultados de experimentos RAG
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
import pandas as pd
from scipy import stats
from collections import defaultdict


class ResultsAnalyzer:
    """
    Analisa resultados de experimentos RAG com estatísticas e comparações
    """
    
    def __init__(self, results_dir: str = "experiments/results"):
        """
        Inicializa analisador de resultados.
        
        Args:
            results_dir: Diretório com arquivos JSON de resultados
        """
        self.results_dir = Path(results_dir)
        self.experiments = {}
        self.summary = None
        
        if not self.results_dir.exists():
            raise ValueError(f"Diretório não encontrado: {results_dir}")
        
        print(f"📊 ResultsAnalyzer inicializado")
        print(f"   Diretório: {self.results_dir}")
    
    def load_experiment(self, experiment_type: str) -> Dict[str, Any]:
        """
        Carrega resultados de um tipo de experimento.
        
        Args:
            experiment_type: 'rag_vs_no_rag', 'retrieval_strategy', etc.
        
        Returns:
            Dicionário com todos os experimentos desse tipo
        """
        pattern = f"{experiment_type}_*.json"
        files = list(self.results_dir.glob(pattern))
        
        if not files:
            raise ValueError(f"Nenhum resultado encontrado para: {experiment_type}")
        
        experiments = {}
        
        for file in files:
            if file.name.endswith('_summary.json'):
                continue
            
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                experiment_name = data['experiment_name']
                experiments[experiment_name] = data
        
        # Carregar summary se existir
        summary_file = self.results_dir / f"{experiment_type}_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                self.summary = json.load(f)
        
        self.experiments = experiments
        
        print(f"✅ {len(experiments)} experimentos carregados: {experiment_type}")
        for name in experiments.keys():
            print(f"   - {name}")
        
        return experiments
    
    def get_metrics_comparison(self, metric_name: str) -> pd.DataFrame:
        """
        Compara uma métrica específica entre todos os experimentos.
        
        Args:
            metric_name: Nome da métrica (ex: 'bertscore_f1', 'latency_ms')
        
        Returns:
            DataFrame com estatísticas da métrica
        """
        data = []
        
        for exp_name, exp_data in self.experiments.items():
            metrics = exp_data['aggregated_metrics']
            
            row = {
                'experiment': exp_name,
                'config': self._format_config(exp_data['config']),
            }
            
            # Adicionar estatísticas da métrica
            for stat in ['mean', 'std', 'min', 'max', 'median']:
                key = f"{metric_name}_{stat}"
                if key in metrics:
                    row[stat] = metrics[key]
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        if 'mean' in df.columns:
            df = df.sort_values('mean', ascending=False)
        
        return df
    
    def compare_experiments(
        self,
        baseline_name: str,
        comparison_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Compara experimentos contra um baseline.
        
        Args:
            baseline_name: Nome do experimento baseline
            comparison_names: Nomes dos experimentos para comparar (None = todos)
        
        Returns:
            DataFrame com métricas e % de melhoria
        """
        if baseline_name not in self.experiments:
            raise ValueError(f"Baseline não encontrado: {baseline_name}")
        
        baseline = self.experiments[baseline_name]
        baseline_metrics = baseline['aggregated_metrics']
        
        if comparison_names is None:
            comparison_names = [
                name for name in self.experiments.keys()
                if name != baseline_name
            ]
        
        comparisons = []
        
        for exp_name in comparison_names:
            if exp_name not in self.experiments:
                continue
            
            exp = self.experiments[exp_name]
            exp_metrics = exp['aggregated_metrics']
            
            comparison = {
                'experiment': exp_name,
                'config': self._format_config(exp['config'])
            }
            
            # Comparar métricas principais
            metrics_to_compare = [
                'bertscore_f1',
                'latency_ms',
                'tokens_used',
                'faithfulness',
                'answer_relevancy',
                'context_precision',
                'context_recall'
            ]
            
            for metric in metrics_to_compare:
                baseline_key = f"{metric}_mean"
                
                if baseline_key in baseline_metrics and baseline_key in exp_metrics:
                    baseline_val = baseline_metrics[baseline_key]
                    exp_val = exp_metrics[baseline_key]
                    
                    comparison[f'{metric}_baseline'] = baseline_val
                    comparison[f'{metric}_experiment'] = exp_val
                    
                    # Calcular % de melhoria
                    if baseline_val != 0:
                        improvement = ((exp_val - baseline_val) / baseline_val) * 100
                        comparison[f'{metric}_improvement_%'] = improvement
            
            comparisons.append(comparison)
        
        df = pd.DataFrame(comparisons)
        
        return df
    
    def statistical_test(
        self,
        exp1_name: str,
        exp2_name: str,
        metric: str = 'bertscore_f1'
    ) -> Dict[str, Any]:
        """
        Realiza teste estatístico (t-test) entre dois experimentos.
        
        Args:
            exp1_name: Nome do primeiro experimento
            exp2_name: Nome do segundo experimento
            metric: Métrica para comparar
        
        Returns:
            Dicionário com resultados do teste
        """
        exp1 = self.experiments[exp1_name]
        exp2 = self.experiments[exp2_name]
        
        # Extrair valores individuais da métrica
        values1 = self._extract_metric_values(exp1, metric)
        values2 = self._extract_metric_values(exp2, metric)
        
        # T-test pareado (duas caudas)
        t_stat, p_value = stats.ttest_ind(values1, values2)
        
        # Tamanho do efeito (Cohen's d)
        cohens_d = self._calculate_cohens_d(values1, values2)
        
        # Teste de normalidade (Shapiro-Wilk)
        _, p_normal1 = stats.shapiro(values1)
        _, p_normal2 = stats.shapiro(values2)
        
        result = {
            'metric': metric,
            'experiment_1': exp1_name,
            'experiment_2': exp2_name,
            'n_samples_1': len(values1),
            'n_samples_2': len(values2),
            'mean_1': np.mean(values1),
            'mean_2': np.mean(values2),
            'std_1': np.std(values1),
            'std_2': np.std(values2),
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'cohens_d': cohens_d,
            'effect_size': self._interpret_cohens_d(cohens_d),
            'normal_distribution_1': p_normal1 > 0.05,
            'normal_distribution_2': p_normal2 > 0.05
        }
        
        return result
    
    def analyze_by_category(self, experiment_name: str) -> pd.DataFrame:
        """
        Analisa métricas agrupadas por categoria de questão.
        
        Args:
            experiment_name: Nome do experimento
        
        Returns:
            DataFrame com métricas por categoria
        """
        exp = self.experiments[experiment_name]
        results = exp['individual_results']
        
        # Agrupar por categoria
        categories = defaultdict(list)
        
        for result in results:
            if 'error' in result:
                continue
            
            category = result.get('category', 'unknown')
            categories[category].append(result)
        
        # Calcular estatísticas por categoria
        category_stats = []
        
        for category, items in categories.items():
            stats_dict = {
                'category': category,
                'count': len(items)
            }
            
            # Métricas principais
            metrics = ['bertscore_f1', 'latency_ms', 'tokens_used', 
                      'faithfulness', 'answer_relevancy']
            
            for metric in metrics:
                values = [
                    item['metrics'][metric] 
                    for item in items 
                    if metric in item['metrics']
                ]
                
                if values:
                    stats_dict[f'{metric}_mean'] = np.mean(values)
                    stats_dict[f'{metric}_std'] = np.std(values)
                    stats_dict[f'{metric}_min'] = np.min(values)
                    stats_dict[f'{metric}_max'] = np.max(values)
            
            category_stats.append(stats_dict)
        
        df = pd.DataFrame(category_stats)
        df = df.sort_values('count', ascending=False)
        
        return df
    
    def analyze_by_difficulty(self, experiment_name: str) -> pd.DataFrame:
        """
        Analisa métricas agrupadas por dificuldade da questão.
        
        Args:
            experiment_name: Nome do experimento
        
        Returns:
            DataFrame com métricas por dificuldade
        """
        exp = self.experiments[experiment_name]
        results = exp['individual_results']
        
        # Agrupar por dificuldade
        difficulties = defaultdict(list)
        
        for result in results:
            if 'error' in result:
                continue
            
            difficulty = result.get('difficulty', 'unknown')
            difficulties[difficulty].append(result)
        
        # Calcular estatísticas
        difficulty_stats = []
        
        for difficulty, items in difficulties.items():
            stats_dict = {
                'difficulty': difficulty,
                'count': len(items)
            }
            
            metrics = ['bertscore_f1', 'faithfulness', 'answer_relevancy']
            
            for metric in metrics:
                values = [
                    item['metrics'][metric] 
                    for item in items 
                    if metric in item['metrics']
                ]
                
                if values:
                    stats_dict[f'{metric}_mean'] = np.mean(values)
                    stats_dict[f'{metric}_std'] = np.std(values)
            
            difficulty_stats.append(stats_dict)
        
        df = pd.DataFrame(difficulty_stats)
        
        return df
    
    def find_best_worst_cases(
        self,
        experiment_name: str,
        metric: str = 'bertscore_f1',
        n: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Identifica os melhores e piores casos de um experimento.
        
        Args:
            experiment_name: Nome do experimento
            metric: Métrica para ordenar
            n: Número de casos a retornar
        
        Returns:
            Dicionário com 'best' e 'worst' casos
        """
        exp = self.experiments[experiment_name]
        results = exp['individual_results']
        
        # Filtrar resultados válidos
        valid_results = [
            r for r in results 
            if 'error' not in r and metric in r['metrics']
        ]
        
        # Ordenar por métrica
        sorted_results = sorted(
            valid_results,
            key=lambda x: x['metrics'][metric],
            reverse=True
        )
        
        best = sorted_results[:n]
        worst = sorted_results[-n:][::-1]  # Reverter para ordem crescente
        
        # Formatar resultados
        def format_case(case):
            return {
                'question_id': case['question_id'],
                'question': case['question'][:100] + '...',
                'category': case.get('category', 'unknown'),
                'metric_value': case['metrics'][metric],
                'answer_preview': case.get('answer_core', '')[:150] + '...',
                'num_chunks': case['metrics'].get('num_chunks', 0)
            }
        
        return {
            'best': [format_case(c) for c in best],
            'worst': [format_case(c) for c in worst]
        }
    
    def analyze_chunk_retrieval(self, experiment_name: str) -> pd.DataFrame:
        """
        Analisa distribuição de chunks recuperados.
        
        Args:
            experiment_name: Nome do experimento
        
        Returns:
            DataFrame com estatísticas de retrieval
        """
        exp = self.experiments[experiment_name]
        results = exp['individual_results']
        
        chunk_counts = defaultdict(int)
        chunk_quality = defaultdict(list)
        
        for result in results:
            if 'error' in result:
                continue
            
            num_chunks = result['metrics'].get('num_chunks', 0)
            chunk_counts[num_chunks] += 1
            
            # Coletar métricas por número de chunks
            if 'bertscore_f1' in result['metrics']:
                chunk_quality[num_chunks].append({
                    'f1': result['metrics']['bertscore_f1'],
                    'faithfulness': result['metrics'].get('faithfulness'),
                    'context_precision': result['metrics'].get('context_precision')
                })
        
        # Criar DataFrame
        data = []
        for num_chunks, count in sorted(chunk_counts.items()):
            row = {
                'num_chunks': num_chunks,
                'count': count,
                'percentage': (count / len(results)) * 100
            }
            
            if num_chunks in chunk_quality:
                quality = chunk_quality[num_chunks]
                row['avg_f1'] = np.mean([q['f1'] for q in quality])
                
                faithfulness = [q['faithfulness'] for q in quality if q['faithfulness'] is not None]
                if faithfulness:
                    row['avg_faithfulness'] = np.mean(faithfulness)
                
                precision = [q['context_precision'] for q in quality if q['context_precision'] is not None]
                if precision:
                    row['avg_context_precision'] = np.mean(precision)
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        return df
    
    def generate_report(
        self,
        experiment_type: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Gera relatório completo em Markdown.
        
        Args:
            experiment_type: Tipo do experimento
            output_file: Arquivo de saída (None = retorna string)
        
        Returns:
            Relatório em formato Markdown
        """
        report = []
        report.append(f"# Relatório de Análise: {experiment_type}")
        report.append(f"\n**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report.append(f"\n**Experimentos Analisados:** {len(self.experiments)}\n")
        report.append("---\n")
        
        # 1. Sumário Executivo
        report.append("## 1. Sumário Executivo\n")
        
        # Tabela de comparação geral
        metrics = ['bertscore_f1', 'latency_ms', 'tokens_used']
        for metric in metrics:
            df = self.get_metrics_comparison(metric)
            report.append(f"\n### {metric.replace('_', ' ').title()}\n")
            report.append(df.to_markdown(index=False))
            report.append("\n")
        
        # 2. Comparação contra Baseline
        if 'no_rag_baseline' in str(list(self.experiments.keys())):
            baseline_name = [n for n in self.experiments.keys() if 'baseline' in n][0]
            report.append("\n## 2. Comparação contra Baseline\n")
            
            df_comp = self.compare_experiments(baseline_name)
            
            # Filtrar colunas principais para o relatório
            cols = ['experiment', 'config']
            cols += [c for c in df_comp.columns if 'improvement' in c]
            
            if cols:
                report.append(df_comp[cols].to_markdown(index=False))
                report.append("\n")
        
        # 3. Análise por Categoria
        report.append("\n## 3. Análise por Categoria\n")
        
        for exp_name in self.experiments.keys():
            report.append(f"\n### {exp_name}\n")
            df_cat = self.analyze_by_category(exp_name)
            
            # Selecionar colunas principais
            cols = ['category', 'count', 'bertscore_f1_mean', 'latency_ms_mean', 'tokens_used_mean']
            cols = [c for c in cols if c in df_cat.columns]
            
            if cols:
                report.append(df_cat[cols].to_markdown(index=False))
                report.append("\n")
        
        # 4. Análise de Retrieval (se aplicável)
        report.append("\n## 4. Análise de Retrieval\n")
        
        for exp_name in self.experiments.keys():
            exp = self.experiments[exp_name]
            if exp['config'].get('use_rag', False):
                report.append(f"\n### {exp_name}\n")
                df_chunks = self.analyze_chunk_retrieval(exp_name)
                report.append(df_chunks.to_markdown(index=False))
                report.append("\n")
        
        # 5. Melhores e Piores Casos
        report.append("\n## 5. Melhores e Piores Casos\n")
        
        for exp_name in list(self.experiments.keys())[:2]:  # Limitar a 2 experimentos
            report.append(f"\n### {exp_name}\n")
            cases = self.find_best_worst_cases(exp_name, n=3)
            
            report.append("\n**🏆 Top 3 Melhores:**\n")
            for i, case in enumerate(cases['best'], 1):
                report.append(f"\n{i}. **Q{case['question_id']}** ({case['category']})")
                report.append(f"   - Score: {case['metric_value']:.4f}")
                report.append(f"   - Pergunta: {case['question']}")
                report.append(f"   - Chunks: {case['num_chunks']}\n")
            
            report.append("\n**⚠️ Top 3 Piores:**\n")
            for i, case in enumerate(cases['worst'], 1):
                report.append(f"\n{i}. **Q{case['question_id']}** ({case['category']})")
                report.append(f"   - Score: {case['metric_value']:.4f}")
                report.append(f"   - Pergunta: {case['question']}")
                report.append(f"   - Chunks: {case['num_chunks']}\n")
        
        # 6. Testes Estatísticos
        if len(self.experiments) >= 2:
            report.append("\n## 6. Testes Estatísticos\n")
            
            exp_names = list(self.experiments.keys())
            if len(exp_names) >= 2:
                test_result = self.statistical_test(
                    exp_names[0],
                    exp_names[1],
                    metric='bertscore_f1'
                )
                
                report.append(f"\n**Comparação:** {test_result['experiment_1']} vs {test_result['experiment_2']}")
                report.append(f"\n- Métrica: {test_result['metric']}")
                report.append(f"- Média 1: {test_result['mean_1']:.4f} (±{test_result['std_1']:.4f})")
                report.append(f"- Média 2: {test_result['mean_2']:.4f} (±{test_result['std_2']:.4f})")
                report.append(f"- t-statistic: {test_result['t_statistic']:.4f}")
                report.append(f"- p-value: {test_result['p_value']:.4f}")
                report.append(f"- **Significativo (p<0.05):** {'✅ Sim' if test_result['significant'] else '❌ Não'}")
                report.append(f"- Cohen's d: {test_result['cohens_d']:.4f} ({test_result['effect_size']})")
                report.append("\n")
        
        # 7. Conclusões
        report.append("\n## 7. Conclusões e Recomendações\n")
        report.append("\n### Principais Achados\n")
        
        # Identificar melhor configuração
        df_f1 = self.get_metrics_comparison('bertscore_f1')
        if not df_f1.empty and 'mean' in df_f1.columns:
            best_exp = df_f1.iloc[0]
            report.append(f"\n✅ **Melhor BERTScore F1:** {best_exp['experiment']} (F1={best_exp['mean']:.4f})")
        
        df_latency = self.get_metrics_comparison('latency_ms')
        if not df_latency.empty and 'mean' in df_latency.columns:
            fastest_exp = df_latency.iloc[-1]  # Menor latência
            report.append(f"\n⚡ **Menor Latência:** {fastest_exp['experiment']} ({fastest_exp['mean']:.0f}ms)")
        
        df_tokens = self.get_metrics_comparison('tokens_used')
        if not df_tokens.empty and 'mean' in df_tokens.columns:
            efficient_exp = df_tokens.iloc[-1]  # Menor tokens
            report.append(f"\n💰 **Mais Eficiente (tokens):** {efficient_exp['experiment']} ({efficient_exp['mean']:.0f} tokens)")
        
        report.append("\n\n### Recomendações\n")
        report.append("\n1. Considerar trade-off entre qualidade (F1) e eficiência (tokens/latência)")
        report.append("\n2. Analisar qualitativamente os piores casos para identificar padrões de erro")
        report.append("\n3. Testar configurações adicionais baseadas nos insights deste relatório")
        
        report.append("\n\n---\n")
        report.append(f"\n*Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*")
        
        report_text = '\n'.join(report)
        
        # Salvar em arquivo se especificado
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            print(f"✅ Relatório salvo em: {output_path}")
        
        return report_text
    
    # Métodos auxiliares
    
    def _format_config(self, config: Dict) -> str:
        """Formata configuração para exibição"""
        parts = []
        
        if not config.get('use_rag', True):
            return "No RAG"
        
        if 'retrieval_method' in config:
            parts.append(config['retrieval_method'])
        
        if 'k' in config:
            parts.append(f"k={config['k']}")
        
        if 'dense_weight' in config:
            parts.append(f"α={config['dense_weight']}")
        
        return ', '.join(parts) if parts else "RAG"
    
    def _extract_metric_values(self, exp: Dict, metric: str) -> List[float]:
        """Extrai valores individuais de uma métrica"""
        values = []
        
        for result in exp['individual_results']:
            if 'error' in result:
                continue
            
            if metric in result['metrics']:
                values.append(result['metrics'][metric])
        
        return values
    
    def _calculate_cohens_d(self, values1: List[float], values2: List[float]) -> float:
        """Calcula Cohen's d (tamanho do efeito)"""
        mean1, mean2 = np.mean(values1), np.mean(values2)
        std1, std2 = np.std(values1, ddof=1), np.std(values2, ddof=1)
        n1, n2 = len(values1), len(values2)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        cohens_d = (mean1 - mean2) / pooled_std
        
        return cohens_d
    
    def _interpret_cohens_d(self, d: float) -> str:
        """Interpreta tamanho do efeito Cohen's d"""
        d = abs(d)
        
        if d < 0.2:
            return "trivial"
        elif d < 0.5:
            return "small"
        elif d < 0.8:
            return "medium"
        else:
            return "large"


def main():
    parser = argparse.ArgumentParser(
        description='Analisa resultados de experimentos RAG'
    )
    
    parser.add_argument(
        '--experiment',
        required=True,
        help='Tipo de experimento (ex: rag_vs_no_rag)'
    )
    
    parser.add_argument(
        '--results-dir',
        default='experiments/results',
        help='Diretório com resultados'
    )
    
    parser.add_argument(
        '--output',
        default=None,
        help='Arquivo de saída para relatório (ex: report.md)'
    )
    
    parser.add_argument(
        '--metric',
        default='bertscore_f1',
        help='Métrica principal para análise'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Mostrar comparação detalhada'
    )
    
    parser.add_argument(
        '--statistical-test',
        action='store_true',
        help='Realizar testes estatísticos'
    )
    
    args = parser.parse_args()
    
    # Criar analisador
    analyzer = ResultsAnalyzer(results_dir=args.results_dir)
    
    # Carregar experimentos
    analyzer.load_experiment(args.experiment)
    
    print("\n" + "="*70)
    print(f"📊 ANÁLISE DE RESULTADOS: {args.experiment}")
    print("="*70 + "\n")
    
    # 1. Comparação de métrica principal
    print(f"1️⃣  Comparação: {args.metric}\n")
    df_metric = analyzer.get_metrics_comparison(args.metric)
    print(df_metric.to_string(index=False))
    print()
    
    # 2. Comparação contra baseline (se existir)
    baseline_exp = [name for name in analyzer.experiments.keys() if 'baseline' in name]
    
    if baseline_exp and args.compare:
        print("\n2️⃣  Comparação contra Baseline\n")
        df_comp = analyzer.compare_experiments(baseline_exp[0])
        
        # Mostrar apenas colunas de melhoria
        improvement_cols = ['experiment', 'config']
        improvement_cols += [c for c in df_comp.columns if 'improvement' in c]
        
        print(df_comp[improvement_cols].to_string(index=False))
        print()
    
    # 3. Análise por categoria
    print("\n3️⃣  Análise por Categoria (primeiro experimento)\n")
    first_exp = list(analyzer.experiments.keys())[0]
    df_cat = analyzer.analyze_by_category(first_exp)
    
    cols = ['category', 'count', 'bertscore_f1_mean', 'latency_ms_mean']
    cols = [c for c in cols if c in df_cat.columns]
    print(df_cat[cols].to_string(index=False))
    print()
    
    # 4. Análise de chunks (se RAG)
    if any(exp['config'].get('use_rag', False) for exp in analyzer.experiments.values()):
        print("\n4️⃣  Análise de Retrieval\n")
        for exp_name in analyzer.experiments.keys():
            exp = analyzer.experiments[exp_name]
            if exp['config'].get('use_rag', False):
                print(f"\n{exp_name}:")
                df_chunks = analyzer.analyze_chunk_retrieval(exp_name)
                print(df_chunks.to_string(index=False))
                print()
    
    # 5. Teste estatístico
    if args.statistical_test and len(analyzer.experiments) >= 2:
        print("\n5️⃣  Teste Estatístico (t-test)\n")
        
        exp_names = list(analyzer.experiments.keys())[:2]
        test = analyzer.statistical_test(exp_names[0], exp_names[1], args.metric)
        
        print(f"Comparação: {test['experiment_1']} vs {test['experiment_2']}")
        print(f"Métrica: {test['metric']}")
        print(f"\nResultados:")
        print(f"  Exp 1: {test['mean_1']:.4f} ± {test['std_1']:.4f} (n={test['n_samples_1']})")
        print(f"  Exp 2: {test['mean_2']:.4f} ± {test['std_2']:.4f} (n={test['n_samples_2']})")
        print(f"\nEstatística:")
        print(f"  t-statistic: {test['t_statistic']:.4f}")
        print(f"  p-value: {test['p_value']:.4f}")
        print(f"  Significativo (p<0.05): {'✅ Sim' if test['significant'] else '❌ Não'}")
        print(f"  Cohen's d: {test['cohens_d']:.4f} ({test['effect_size']})")
        print()
    
    # 6. Gerar relatório completo
    if args.output:
        print(f"\n6️⃣  Gerando relatório completo...\n")
        analyzer.generate_report(args.experiment, output_file=args.output)
    else:
        # Mostrar apenas melhores/piores casos
        print("\n6️⃣  Melhores e Piores Casos\n")
        first_exp = list(analyzer.experiments.keys())[0]
        cases = analyzer.find_best_worst_cases(first_exp, metric=args.metric, n=3)
        
        print("🏆 Top 3 Melhores:")
        for i, case in enumerate(cases['best'], 1):
            print(f"\n{i}. Q{case['question_id']} ({case['category']}) - Score: {case['metric_value']:.4f}")
            print(f"   {case['question']}")
        
        print("\n\n⚠️  Top 3 Piores:")
        for i, case in enumerate(cases['worst'], 1):
            print(f"\n{i}. Q{case['question_id']} ({case['category']}) - Score: {case['metric_value']:.4f}")
            print(f"   {case['question']}")
    
    print("\n" + "="*70)
    print("✅ Análise concluída!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
