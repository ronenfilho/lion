"""
RAGAS Evaluator - LION
Métricas RAG-específicas usando biblioteca RAGAS
"""

import os
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
        context_entity_recall,
        answer_correctness,
        answer_similarity
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError as e:
    RAGAS_AVAILABLE = False
    print(f"⚠️  ragas não instalado corretamente: {e}")
    print("Execute: pip install ragas datasets")


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
    context_entity_recall: Optional[float] = None  # Entidades do contexto recuperadas?
    
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
    - context_entity_recall: Entidades do contexto foram recuperadas?
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
            llm_provider: LLM para métricas que requerem (opcional, usa env se None)
            embeddings_provider: Embeddings para métricas que requerem (opcional)
            verbose: Se True, imprime detalhes
        """
        if not RAGAS_AVAILABLE:
            raise ImportError(
                "ragas não está instalado. "
                "Execute: pip install ragas datasets"
            )
        
        # Definir verbose antes de usá-lo
        self.verbose = verbose
        
        # Configurar LLM e Embeddings a partir do .env se não fornecidos
        if llm_provider is None:
            llm_provider = self._setup_llm_from_env()
        
        if embeddings_provider is None:
            embeddings_provider = self._setup_embeddings_from_env()
        
        self.llm_provider = llm_provider
        self.embeddings_provider = embeddings_provider
    
    def _setup_llm_from_env(self) -> Optional[Any]:
        """
        Configura LLM provider a partir das variáveis de ambiente.
        
        Suporta:
        - RAGAS_LLM_PROVIDER=gemini (usa RAGAS_API_KEY ou GEMINI_API_KEY)
        - RAGAS_LLM_PROVIDER=openai (usa RAGAS_API_KEY ou OPENAI_API_KEY)
        
        Returns:
            LLM provider configurado ou None
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        ragas_provider = os.getenv('RAGAS_LLM_PROVIDER', 'gemini').lower()
        
        # Buscar API key (prioriza RAGAS_API_KEY, depois a específica do provider)
        api_key = os.getenv('RAGAS_API_KEY')
        
        if ragas_provider == 'gemini':
            api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            
            if api_key:
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    
                    # Nome do modelo verificado como funcional em 2026
                    model_name = "gemini-2.5-flash"
                    
                    llm = ChatGoogleGenerativeAI(
                        model=model_name,
                        google_api_key=api_key,
                        temperature=0.2,
                        convert_system_message_to_human=True  # Importante para RAGAS
                    )
                    
                    if self.verbose:
                        print(f"✅ RAGAS configurado com Google Gemini ({model_name})")
                    
                    return llm
                    
                except ImportError:
                    if self.verbose:
                        print("⚠️  langchain-google-genai não instalado")
                        print("   Execute: pip install langchain-google-genai")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Erro ao configurar Gemini: {e}")
        
        elif ragas_provider == 'openai':
            api_key = api_key or os.getenv('OPENAI_API_KEY')
            
            if api_key:
                try:
                    from langchain_openai import ChatOpenAI
                    
                    llm = ChatOpenAI(
                        model="gpt-3.5-turbo",
                        api_key=api_key,
                        temperature=0.2
                    )
                    
                    if self.verbose:
                        print("✅ RAGAS configurado com OpenAI")
                    
                    return llm
                    
                except ImportError:
                    if self.verbose:
                        print("⚠️  langchain-openai não instalado")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Erro ao configurar OpenAI: {e}")
        
        if self.verbose:
            print("⚠️  Nenhum LLM configurado para RAGAS")
            print(f"   Configure RAGAS_LLM_PROVIDER e RAGAS_API_KEY no .env")
        
        return None

    def _setup_embeddings_from_env(self) -> Optional[Any]:
        """
        Configura Embeddings provider a partir do .env.
        """
        ragas_provider = os.getenv('RAGAS_LLM_PROVIDER', 'gemini').lower()
        api_key = os.getenv('RAGAS_API_KEY')
        
        if ragas_provider == 'gemini':
            api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if api_key:
                try:
                    from langchain_google_genai import GoogleGenerativeAIEmbeddings
                    
                    # Modelo de embedding verificado como funcional
                    embed_model = "models/gemini-embedding-001"
                    
                    embeddings = GoogleGenerativeAIEmbeddings(
                        model=embed_model,
                        google_api_key=api_key
                    )
                    
                    if self.verbose:
                        print(f"✅ Embeddings configurados: {embed_model}")
                        
                    return embeddings
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️ Erro ao configurar Gemini Embeddings: {e}")
        
        elif ragas_provider == 'openai':
            api_key = api_key or os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    from langchain_openai import OpenAIEmbeddings
                    return OpenAIEmbeddings(api_key=api_key, model="text-embedding-3-small")
                except Exception:
                    pass
        
        return None
    
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
            # Passar LLM se disponível
            eval_kwargs = {
                'dataset': dataset,
                'metrics': selected_metrics
            }
            
            if self.llm_provider:
                eval_kwargs['llm'] = self.llm_provider
            
            if self.embeddings_provider:
                eval_kwargs['embeddings'] = self.embeddings_provider
            
            result = evaluate(**eval_kwargs)
            
            # Extrair scores de forma robusta
            # RAGAS 0.2+ retorna um objeto EvaluationResult
            metrics_dict = {
                'answer_relevancy': None,
                'faithfulness': None,
                'answer_correctness': None,
                'answer_similarity': None,
                'context_precision': None,
                'context_recall': None,
                'context_entity_recall': None,
                'num_samples': len(questions)
            }
            
            # Tentar acesso direto (funciona na maioria das versões recentes)
            for m_name in metrics_dict.keys():
                if m_name == 'num_samples': continue
                try:
                    # No RAGAS 0.2, result é como um dict de scores médios
                    val = result[m_name]
                    metrics_dict[m_name] = float(val) if val is not None else None
                except (KeyError, TypeError, AttributeError):
                    # Fallback: tentar atributo direto
                    val = getattr(result, m_name, None)
                    if val is not None:
                        metrics_dict[m_name] = float(val)

            # Fallback final: se result.scores existir e for lista
            if hasattr(result, 'scores') and isinstance(result.scores, list):
                for m_name in metrics_dict.keys():
                    if m_name == 'num_samples' or metrics_dict[m_name] is not None:
                        continue
                    
                    # Pegar média dos scores individuais
                    vals = [s.get(m_name) for s in result.scores if isinstance(s, dict) and s.get(m_name) is not None]
                    if vals:
                        metrics_dict[m_name] = sum(vals) / len(vals)
            
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
        
        metrics = ['context_precision', 'context_entity_recall']
        
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
            'context_entity_recall': result.context_entity_recall
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
            'context_entity_recall': context_entity_recall,
            'answer_correctness': answer_correctness,
            'answer_similarity': answer_similarity
        }
        
        # Se não especificou, usar métricas básicas
        if metric_names is None:
            metric_names = ['answer_relevancy', 'faithfulness', 'context_entity_recall']
            
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
    # Teste rápido do RAGASEvaluator
    evaluator = RAGASEvaluator(verbose=True)
    
    questions = [
        "O que é LION?",
        "Qual a data de hoje?"
    ]
    answers = [
        "LION é um sistema de IA para processamento de documentos.",
        "Hoje é 15 de fevereiro de 2026."
    ]
    contexts = [
        ["LION (Legal Intelligent Operations Network) é um sistema RAG."],
        ["O sistema indica que a data atual é 15/02/2026."]
    ]
    ground_truths = [
        "LION é um assistente inteligente baseado em RAG para documentos.",
        "A data de hoje é 15 de fevereiro de 2026."
    ]
    
    print("\n🧪 TESTE DO RAGAS EVALUATOR")
    print("="*80)
    
    try:
        # Usar apenas subconjunto das métricas para ser mais rápido
        metrics = evaluator.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths,
            metrics=['faithfulness']
        )
        
        print("\n✅ Resumo da Avaliação RAGAS:")
        print(f"   - Faithfulness: {metrics.faithfulness:.3f}")
        
    except Exception as e:
        print(f"\n❌ Erro no teste RAGAS: {e}")
        import traceback
        traceback.print_exc()
