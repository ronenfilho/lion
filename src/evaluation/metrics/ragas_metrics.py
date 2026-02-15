"""
RAGAS Evaluator - LION
Métricas RAG-específicas usando biblioteca RAGAS
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import warnings

try:
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        faithfulness,
        context_precision,
        context_recall,
        context_relevancy,
        answer_correctness,
        answer_similarity
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("⚠️  ragas não instalado. Execute: pip install ragas datasets")


@dataclass
class RAGASMetrics:
    """Métricas RAGAS agregadas"""
    # Generation quality
    answer_relevancy: float  # Resposta relevante à pergunta?
    faithfulness: float  # Resposta fundamentada no contexto?
    answer_correctness: Optional[float] = None  # Resposta correta? (requer ground truth)
    answer_similarity: Optional[float] = None  # Similar ao ground truth? (requer ground truth)
    
    # Retrieval quality
    context_precision: Optional[float] = None  # Contexto relevante está ranqueado alto?
    context_recall: Optional[float] = None  # Todo contexto relevante foi recuperado?
    context_relevancy: Optional[float] = None  # Contexto recuperado é relevante?
    
    # Metadata
    num_samples: int = 1


class RAGASEvaluator:
    """
    Avaliador usando métricas RAGAS para sistemas RAG.
    
    RAGAS (Retrieval Augmented Generation Assessment) fornece métricas
    específicas para avaliar tanto retrieval quanto generation:
    
    Generation Metrics:
    - answer_relevancy: A resposta é relevante para a pergunta?
    - faithfulness: A resposta é fundamentada no contexto fornecido?
    - answer_correctness: A resposta está correta? (requer ground truth)
    - answer_similarity: Quão similar é da resposta esperada? (requer ground truth)
    
    Retrieval Metrics:
    - context_precision: Contexto relevante está bem ranqueado?
    - context_recall: Todo contexto relevante foi recuperado?
    - context_relevancy: O contexto recuperado é relevante para a pergunta?
    """
    
    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        embeddings_provider: Optional[Any] = None,
        verbose: bool = False
    ):
        """
        Inicializa avaliador RAGAS.
        
        Args:
            llm_provider: LLM para métricas que requerem (opcional)
            embeddings_provider: Embeddings para métricas que requerem (opcional)
            verbose: Se True, imprime detalhes
        """
        if not RAGAS_AVAILABLE:
            raise ImportError(
                "ragas não está instalado. "
                "Execute: pip install ragas datasets"
            )
        
        self.llm_provider = llm_provider
        self.embeddings_provider = embeddings_provider
        self.verbose = verbose
    
    def evaluate(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> RAGASMetrics:
        """
        Avalia sistema RAG usando métricas RAGAS.
        
        Args:
            questions: Lista de perguntas
            answers: Lista de respostas geradas
            contexts: Lista de contextos (cada um é lista de chunks)
            ground_truths: Lista de respostas esperadas (opcional)
            metrics: Lista de nomes de métricas a calcular (None = todas disponíveis)
            
        Returns:
            RAGASMetrics com scores agregados
        """
        # Validar inputs
        if not (len(questions) == len(answers) == len(contexts)):
            raise ValueError("questions, answers e contexts devem ter mesmo tamanho")
        
        if ground_truths and len(ground_truths) != len(questions):
            raise ValueError("ground_truths deve ter mesmo tamanho que questions")
        
        # Criar dataset
        data = {
            'question': questions,
            'answer': answers,
            'contexts': contexts
        }
        
        if ground_truths:
            data['ground_truth'] = ground_truths
        
        dataset = Dataset.from_dict(data)
        
        # Selecionar métricas
        selected_metrics = self._select_metrics(metrics, has_ground_truth=ground_truths is not None)
        
        # Suprimir warnings se não verbose
        if not self.verbose:
            warnings.filterwarnings('ignore')
        
        # Avaliar
        try:
            result = evaluate(
                dataset=dataset,
                metrics=selected_metrics
            )
            
            # Extrair scores
            metrics_dict = {
                'answer_relevancy': result.get('answer_relevancy'),
                'faithfulness': result.get('faithfulness'),
                'answer_correctness': result.get('answer_correctness'),
                'answer_similarity': result.get('answer_similarity'),
                'context_precision': result.get('context_precision'),
                'context_recall': result.get('context_recall'),
                'context_relevancy': result.get('context_relevancy'),
                'num_samples': len(questions)
            }
            
            return RAGASMetrics(**metrics_dict)
            
        finally:
            if not self.verbose:
                warnings.filterwarnings('default')
    
    def evaluate_single(
        self,
        question: str,
        answer: str,
        context: List[str],
        ground_truth: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> RAGASMetrics:
        """
        Avalia uma única query RAG.
        
        Args:
            question: Pergunta
            answer: Resposta gerada
            context: Lista de chunks de contexto
            ground_truth: Resposta esperada (opcional)
            metrics: Métricas a calcular (None = todas)
            
        Returns:
            RAGASMetrics
        """
        return self.evaluate(
            questions=[question],
            answers=[answer],
            contexts=[context],
            ground_truths=[ground_truth] if ground_truth else None,
            metrics=metrics
        )
    
    def evaluate_generation_only(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Avalia apenas qualidade de geração (não retrieval).
        
        Args:
            questions: Perguntas
            answers: Respostas geradas
            contexts: Contextos usados
            ground_truths: Respostas esperadas (opcional)
            
        Returns:
            Dict com métricas de geração
        """
        metrics = ['answer_relevancy', 'faithfulness']
        
        if ground_truths:
            metrics.extend(['answer_correctness', 'answer_similarity'])
        
        result = self.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths,
            metrics=metrics
        )
        
        return {
            'answer_relevancy': result.answer_relevancy,
            'faithfulness': result.faithfulness,
            'answer_correctness': result.answer_correctness,
            'answer_similarity': result.answer_similarity
        }
    
    def evaluate_retrieval_only(
        self,
        questions: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Avalia apenas qualidade de retrieval.
        
        Args:
            questions: Perguntas
            contexts: Contextos recuperados
            ground_truths: Para context_recall (opcional)
            
        Returns:
            Dict com métricas de retrieval
        """
        # Para RAGAS, precisamos de answers dummy
        dummy_answers = ["Resposta placeholder"] * len(questions)
        
        metrics = ['context_precision', 'context_relevancy']
        
        if ground_truths:
            metrics.append('context_recall')
        
        result = self.evaluate(
            questions=questions,
            answers=dummy_answers,
            contexts=contexts,
            ground_truths=ground_truths,
            metrics=metrics
        )
        
        return {
            'context_precision': result.context_precision,
            'context_recall': result.context_recall,
            'context_relevancy': result.context_relevancy
        }
    
    def _select_metrics(
        self,
        metric_names: Optional[List[str]],
        has_ground_truth: bool
    ) -> List:
        """
        Seleciona objetos de métricas RAGAS.
        
        Args:
            metric_names: Nomes das métricas desejadas
            has_ground_truth: Se tem ground truth disponível
            
        Returns:
            Lista de objetos de métrica RAGAS
        """
        # Mapeamento nome -> objeto
        available_metrics = {
            'answer_relevancy': answer_relevancy,
            'faithfulness': faithfulness,
            'context_precision': context_precision,
            'context_recall': context_recall,
            'context_relevancy': context_relevancy,
            'answer_correctness': answer_correctness,
            'answer_similarity': answer_similarity
        }
        
        # Se não especificou, usar métricas básicas
        if metric_names is None:
            metric_names = ['answer_relevancy', 'faithfulness', 'context_relevancy']
            
            # Adicionar métricas que requerem ground truth
            if has_ground_truth:
                metric_names.extend(['context_precision', 'context_recall'])
        
        # Filtrar métricas que requerem ground truth
        if not has_ground_truth:
            metric_names = [
                m for m in metric_names
                if m not in ['answer_correctness', 'answer_similarity', 'context_recall']
            ]
        
        # Retornar objetos
        return [available_metrics[name] for name in metric_names if name in available_metrics]
    
    def compare_systems(
        self,
        questions: List[str],
        answers_a: List[str],
        answers_b: List[str],
        contexts_a: List[List[str]],
        contexts_b: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compara dois sistemas RAG lado a lado.
        
        Args:
            questions: Perguntas
            answers_a: Respostas do sistema A
            answers_b: Respostas do sistema B
            contexts_a: Contextos do sistema A
            contexts_b: Contextos do sistema B
            ground_truths: Respostas esperadas (opcional)
            
        Returns:
            Dict com comparação
        """
        result_a = self.evaluate(
            questions=questions,
            answers=answers_a,
            contexts=contexts_a,
            ground_truths=ground_truths
        )
        
        result_b = self.evaluate(
            questions=questions,
            answers=answers_b,
            contexts=contexts_b,
            ground_truths=ground_truths
        )
        
        # Calcular vencedor
        score_a = (result_a.answer_relevancy + result_a.faithfulness) / 2
        score_b = (result_b.answer_relevancy + result_b.faithfulness) / 2
        
        winner = 'B' if score_b > score_a else 'A'
        improvement = abs(score_b - score_a) / score_a * 100 if score_a > 0 else 0
        
        return {
            'system_a': asdict(result_a),
            'system_b': asdict(result_b),
            'winner': winner,
            'improvement_pct': improvement
        }


def create_ragas_evaluator(
    llm_provider: Optional[Any] = None,
    embeddings_provider: Optional[Any] = None,
    verbose: bool = False
) -> RAGASEvaluator:
    """
    Factory function para criar RAGAS evaluator.
    
    Args:
        llm_provider: LLM provider (opcional)
        embeddings_provider: Embeddings provider (opcional)
        verbose: Se True, imprime detalhes
        
    Returns:
        RAGASEvaluator
    """
    return RAGASEvaluator(
        llm_provider=llm_provider,
        embeddings_provider=embeddings_provider,
        verbose=verbose
    )


# Exemplo de uso
if __name__ == "__main__":
    print("🧪 TESTE DO RAGAS EVALUATOR")
    print("=" * 80)
    
    if not RAGAS_AVAILABLE:
        print("❌ ragas não está instalado")
        print("Execute: pip install ragas datasets")
        exit(1)
    
    # Criar avaliador
    evaluator = create_ragas_evaluator(verbose=True)
    print("✅ Avaliador RAGAS criado\n")
    
    # Dados de teste
    questions = [
        "Como declarar aposentadoria no IRPF?",
        "Posso deduzir plano de saúde?"
    ]
    
    answers = [
        "A aposentadoria deve ser declarada na ficha de Rendimentos Tributáveis. "
        "É importante incluir todos os comprovantes fornecidos pelo INSS.",
        "Sim, despesas com plano de saúde são dedutíveis sem limite de valor. "
        "Devem ser declaradas na ficha de Pagamentos Efetuados."
    ]
    
    contexts = [
        [
            "Aposentadorias e pensões são rendimentos tributáveis recebidos de pessoa jurídica.",
            "Devem ser declarados na ficha Rendimentos Tributáveis Recebidos de PJ.",
            "O INSS fornece informe de rendimentos para a declaração."
        ],
        [
            "Despesas médicas e com plano de saúde podem ser deduzidas integralmente.",
            "Não há limite para dedução de despesas médicas.",
            "Declarar na ficha Pagamentos Efetuados, código 26 para planos de saúde."
        ]
    ]
    
    ground_truths = [
        "Aposentadoria é declarada como rendimento tributável recebido de pessoa jurídica.",
        "Plano de saúde é dedutível integralmente na declaração de IRPF."
    ]
    
    print("📝 Teste 1: Avaliação completa (com ground truth)")
    try:
        result = evaluator.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths
        )
        
        print(f"   Answer Relevancy:  {result.answer_relevancy:.3f}")
        print(f"   Faithfulness:      {result.faithfulness:.3f}")
        print(f"   Context Relevancy: {result.context_relevancy:.3f}")
        
        if result.context_precision:
            print(f"   Context Precision: {result.context_precision:.3f}")
        if result.context_recall:
            print(f"   Context Recall:    {result.context_recall:.3f}")
        
        print(f"   Samples:           {result.num_samples}")
        print(f"   ✅ Avaliação completa\n")
        
    except Exception as e:
        print(f"   ⚠️  Erro na avaliação: {e}")
        print(f"   (RAGAS pode requerer configuração de LLM)\n")
    
    print("📝 Teste 2: Avaliação sem ground truth")
    try:
        result2 = evaluator.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts
        )
        
        print(f"   Answer Relevancy:  {result2.answer_relevancy:.3f}")
        print(f"   Faithfulness:      {result2.faithfulness:.3f}")
        print(f"   Context Relevancy: {result2.context_relevancy:.3f}")
        print(f"   ✅ Avaliação sem ground truth\n")
        
    except Exception as e:
        print(f"   ⚠️  Erro: {e}")
        print(f"   (RAGAS requer OpenAI API key ou LLM configurado)\n")
    
    print("=" * 80)
    print("✅ Testes RAGAS concluídos")
    print("\n💡 Nota: RAGAS usa LLMs internamente para algumas métricas.")
    print("   Configure OPENAI_API_KEY ou passe llm_provider customizado.")
