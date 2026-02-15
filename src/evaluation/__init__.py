"""
Evaluation package - LION
Sistema de avaliação e experimentos
"""

from .metrics.rag_metrics import (
    RAGEvaluator,
    RAGMetrics,
    create_rag_evaluator
)

from .metrics.comparative_metrics import (
    ComparativeEvaluator,
    ABTestRunner,
    SystemConfig,
    RunResult,
    ComparisonReport,
    create_comparative_evaluator
)

from .experiments.runner import (
    ExperimentRunner,
    ExperimentConfig,
    QueryResult,
    ExperimentReport,
    create_experiment_runner
)


__all__ = [
    # RAG Metrics
    'RAGEvaluator',
    'RAGMetrics',
    'create_rag_evaluator',
    
    # Comparative Metrics
    'ComparativeEvaluator',
    'ABTestRunner',
    'SystemConfig',
    'RunResult',
    'ComparisonReport',
    'create_comparative_evaluator',
    
    # Experiment Runner
    'ExperimentRunner',
    'ExperimentConfig',
    'QueryResult',
    'ExperimentReport',
    'create_experiment_runner',
]
