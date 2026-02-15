"""
Metrics package - LION
Métricas de avaliação para RAG
"""

from .rag_metrics import RAGEvaluator, RAGMetrics, create_rag_evaluator
from .comparative_metrics import (
    ComparativeEvaluator,
    ABTestRunner,
    SystemConfig,
    RunResult,
    ComparisonReport,
    create_comparative_evaluator
)


__all__ = [
    'RAGEvaluator',
    'RAGMetrics',
    'create_rag_evaluator',
    'ComparativeEvaluator',
    'ABTestRunner',
    'SystemConfig',
    'RunResult',
    'ComparisonReport',
    'create_comparative_evaluator',
]
