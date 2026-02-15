"""
BERTScore Evaluator - LION
Avaliação de similaridade semântica usando BERT embeddings
"""

from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import numpy as np

try:
    from bert_score import score as bert_score
    BERTSCORE_AVAILABLE = True
except ImportError:
    BERTSCORE_AVAILABLE = False
    print("⚠️  bert-score não instalado. Execute: pip install bert-score")


@dataclass
class BERTScoreResult:
    """Resultado de avaliação BERTScore"""
    precision: float
    recall: float
    f1: float
    
    # Estatísticas agregadas (para múltiplas comparações)
    precision_list: Optional[List[float]] = None
    recall_list: Optional[List[float]] = None
    f1_list: Optional[List[float]] = None
    
    # Metadados
    model: str = "default"
    num_samples: int = 1


class BERTScoreEvaluator:
    """
    Avaliador usando BERTScore para similaridade semântica.
    
    BERTScore mede similaridade entre textos usando embeddings BERT:
    - Precision: relevância das palavras na resposta
    - Recall: cobertura das palavras da referência
    - F1: média harmônica de P e R
    
    Vantagens sobre métricas léxicas (BLEU, ROUGE):
    - Captura sinonímia e paráfrases
    - Mais robusto a reformulações
    - Correlação maior com avaliação humana
    """
    
    def __init__(
        self,
        model_type: str = "microsoft/deberta-xlarge-mnli",
        lang: str = "pt",
        device: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Inicializa avaliador BERTScore.
        
        Args:
            model_type: Modelo BERT a usar. Opções:
                - "microsoft/deberta-xlarge-mnli" (melhor, mais lento)
                - "bert-base-multilingual-cased" (rápido, suporta PT)
                - "neuralmind/bert-base-portuguese-cased" (PT nativo)
            lang: Código do idioma (pt, en, etc)
            device: 'cuda' ou 'cpu' (None = auto-detect)
            verbose: Se True, imprime detalhes
        """
        if not BERTSCORE_AVAILABLE:
            raise ImportError(
                "bert-score não está instalado. "
                "Execute: pip install bert-score"
            )
        
        self.model_type = model_type
        self.lang = lang
        self.device = device
        self.verbose = verbose
    
    def evaluate(
        self,
        candidates: Union[str, List[str]],
        references: Union[str, List[str]],
        batch_size: int = 64
    ) -> BERTScoreResult:
        """
        Avalia similaridade entre candidatos e referências.
        
        Args:
            candidates: Texto(s) gerado(s) pelo sistema
            references: Texto(s) de referência (ground truth)
            batch_size: Tamanho do batch para processamento
            
        Returns:
            BERTScoreResult com métricas P, R, F1
        """
        # Normalizar inputs para lista
        if isinstance(candidates, str):
            candidates = [candidates]
        if isinstance(references, str):
            references = [references]
        
        if len(candidates) != len(references):
            raise ValueError(
                f"Número de candidatos ({len(candidates)}) deve ser igual "
                f"ao número de referências ({len(references)})"
            )
        
        # Calcular BERTScore
        P, R, F1 = bert_score(
            cands=candidates,
            refs=references,
            model_type=self.model_type,
            lang=self.lang,
            device=self.device,
            verbose=self.verbose,
            batch_size=batch_size
        )
        
        # Converter tensors para numpy
        precision_list = P.cpu().numpy().tolist()
        recall_list = R.cpu().numpy().tolist()
        f1_list = F1.cpu().numpy().tolist()
        
        # Métricas agregadas
        precision_mean = float(np.mean(precision_list))
        recall_mean = float(np.mean(recall_list))
        f1_mean = float(np.mean(f1_list))
        
        return BERTScoreResult(
            precision=precision_mean,
            recall=recall_mean,
            f1=f1_mean,
            precision_list=precision_list,
            recall_list=recall_list,
            f1_list=f1_list,
            model=self.model_type,
            num_samples=len(candidates)
        )
    
    def evaluate_single(
        self,
        candidate: str,
        reference: str
    ) -> BERTScoreResult:
        """
        Avalia um único par candidate-reference.
        
        Args:
            candidate: Texto gerado
            reference: Texto de referência
            
        Returns:
            BERTScoreResult
        """
        return self.evaluate([candidate], [reference])
    
    def evaluate_rag_answer(
        self,
        generated_answer: str,
        expected_answer: str
    ) -> Dict[str, float]:
        """
        Avalia resposta RAG contra resposta esperada.
        
        Args:
            generated_answer: Resposta gerada pelo sistema RAG
            expected_answer: Resposta esperada (ground truth)
            
        Returns:
            Dict com precision, recall, f1
        """
        result = self.evaluate_single(generated_answer, expected_answer)
        
        return {
            'bertscore_precision': result.precision,
            'bertscore_recall': result.recall,
            'bertscore_f1': result.f1
        }
    
    def batch_evaluate(
        self,
        results: List[Dict[str, str]],
        batch_size: int = 64
    ) -> Dict[str, float]:
        """
        Avalia múltiplos resultados RAG em batch.
        
        Args:
            results: Lista de dicts com keys 'generated' e 'expected'
            batch_size: Tamanho do batch
            
        Returns:
            Dict com métricas agregadas
        """
        candidates = [r['generated'] for r in results]
        references = [r['expected'] for r in results]
        
        bert_result = self.evaluate(
            candidates=candidates,
            references=references,
            batch_size=batch_size
        )
        
        return {
            'bertscore_precision': bert_result.precision,
            'bertscore_recall': bert_result.recall,
            'bertscore_f1': bert_result.f1,
            'num_samples': bert_result.num_samples
        }
    
    def compare_models(
        self,
        candidates_a: List[str],
        candidates_b: List[str],
        references: List[str]
    ) -> Dict[str, any]:
        """
        Compara dois modelos usando mesmas referências.
        
        Args:
            candidates_a: Respostas do modelo A
            candidates_b: Respostas do modelo B
            references: Referências ground truth
            
        Returns:
            Dict com comparação
        """
        result_a = self.evaluate(candidates_a, references)
        result_b = self.evaluate(candidates_b, references)
        
        # Calcular diferenças
        f1_diff = result_b.f1 - result_a.f1
        f1_improvement = (f1_diff / result_a.f1 * 100) if result_a.f1 > 0 else 0
        
        winner = 'B' if result_b.f1 > result_a.f1 else 'A'
        
        return {
            'model_a': {
                'precision': result_a.precision,
                'recall': result_a.recall,
                'f1': result_a.f1
            },
            'model_b': {
                'precision': result_b.precision,
                'recall': result_b.recall,
                'f1': result_b.f1
            },
            'difference': {
                'precision': result_b.precision - result_a.precision,
                'recall': result_b.recall - result_a.recall,
                'f1': f1_diff
            },
            'improvement_pct': f1_improvement,
            'winner': winner
        }


def create_bertscore_evaluator(
    model_type: str = "bert-base-multilingual-cased",
    lang: str = "pt",
    device: Optional[str] = None
) -> BERTScoreEvaluator:
    """
    Factory function para criar BERTScore evaluator.
    
    Args:
        model_type: Modelo BERT a usar
        lang: Idioma
        device: Device (cuda/cpu)
        
    Returns:
        BERTScoreEvaluator
    """
    return BERTScoreEvaluator(
        model_type=model_type,
        lang=lang,
        device=device
    )


# Exemplo de uso
if __name__ == "__main__":
    print("🧪 TESTE DO BERTSCORE EVALUATOR")
    print("=" * 80)
    
    if not BERTSCORE_AVAILABLE:
        print("❌ bert-score não está instalado")
        print("Execute: pip install bert-score")
        exit(1)
    
    # Criar avaliador (modelo leve para teste)
    evaluator = create_bertscore_evaluator(
        model_type="bert-base-multilingual-cased",
        lang="pt"
    )
    
    print(f"✅ Avaliador criado com modelo: {evaluator.model_type}\n")
    
    # Teste 1: Resposta idêntica (deve ter score alto)
    print("📝 Teste 1: Resposta idêntica")
    candidate1 = "O imposto de renda é declarado anualmente."
    reference1 = "O imposto de renda é declarado anualmente."
    
    result1 = evaluator.evaluate_single(candidate1, reference1)
    print(f"   Precision: {result1.precision:.3f}")
    print(f"   Recall:    {result1.recall:.3f}")
    print(f"   F1:        {result1.f1:.3f}")
    print(f"   ✅ Score alto (texto idêntico)\n")
    
    # Teste 2: Paráfrase (deve ter score bom)
    print("📝 Teste 2: Paráfrase")
    candidate2 = "A declaração do IR acontece uma vez por ano."
    reference2 = "O imposto de renda é declarado anualmente."
    
    result2 = evaluator.evaluate_single(candidate2, reference2)
    print(f"   Precision: {result2.precision:.3f}")
    print(f"   Recall:    {result2.recall:.3f}")
    print(f"   F1:        {result2.f1:.3f}")
    print(f"   ✅ Score bom (paráfrase válida)\n")
    
    # Teste 3: Resposta incorreta (deve ter score baixo)
    print("📝 Teste 3: Resposta incorreta")
    candidate3 = "Python é uma linguagem de programação."
    reference3 = "O imposto de renda é declarado anualmente."
    
    result3 = evaluator.evaluate_single(candidate3, reference3)
    print(f"   Precision: {result3.precision:.3f}")
    print(f"   Recall:    {result3.recall:.3f}")
    print(f"   F1:        {result3.f1:.3f}")
    print(f"   ✅ Score baixo (totalmente diferente)\n")
    
    # Teste 4: Batch evaluation
    print("📝 Teste 4: Avaliação em batch")
    results = [
        {
            'generated': "A aposentadoria é tributável.",
            'expected': "Aposentadoria é rendimento tributável."
        },
        {
            'generated': "Plano de saúde pode ser deduzido.",
            'expected': "Gastos com saúde são dedutíveis."
        }
    ]
    
    batch_result = evaluator.batch_evaluate(results)
    print(f"   Samples:   {batch_result['num_samples']}")
    print(f"   Precision: {batch_result['bertscore_precision']:.3f}")
    print(f"   Recall:    {batch_result['bertscore_recall']:.3f}")
    print(f"   F1:        {batch_result['bertscore_f1']:.3f}")
    print(f"   ✅ Batch evaluation completo\n")
    
    print("=" * 80)
    print("✅ Todos os testes concluídos com sucesso!")
