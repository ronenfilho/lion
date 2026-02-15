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

from .metrics.bertscore import (
    BERTScoreEvaluator,
    BERTScoreResult,
    create_bertscore_evaluator
)

from .metrics.ragas_metrics import (
    RAGASEvaluator,
    RAGASMetrics,
    create_ragas_evaluator
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
    
    # BERTScore
    'BERTScoreEvaluator',
    'BERTScoreResult',
    'create_bertscore_evaluator',
    
    # RAGAS
    'RAGASEvaluator',
    'RAGASMetrics',
    'create_ragas_evaluator',
    
    # Experiment Runner
    'ExperimentRunner',
    'ExperimentConfig',
    'QueryResult',
    'ExperimentReport',
    'create_experiment_runner',
]
