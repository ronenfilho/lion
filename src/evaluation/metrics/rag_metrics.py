"""
RAG Metrics - LION
Métricas específicas para avaliação de sistemas RAG
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class RAGMetrics:
    """Métricas agregadas de avaliação RAG"""
    # Retrieval
    retrieval_precision: float  # Chunks relevantes / Total recuperado
    retrieval_recall: float  # Chunks relevantes recuperados / Total relevantes
    retrieval_mrr: float  # Mean Reciprocal Rank
    
    # Generation
    faithfulness: float  # Fidelidade ao contexto (0-1)
    answer_relevance: float  # Relevância da resposta (0-1)
    context_relevance: float  # Relevância do contexto (0-1)
    
    # Qualidade
    has_citations: bool
    citation_accuracy: float
    hallucination_score: float  # Risco de alucinação (0-1, menor é melhor)
    
    # Overall
    overall_score: float  # Score geral (0-1)


class RAGEvaluator:
    """
    Avaliador de sistemas RAG sem modelos pesados.
    
    Implementa métricas que não requerem BERT, GPT, etc.:
    - Retrieval: Precision, Recall, MRR
    - Faithfulness: Overlap de n-gramas
    - Relevance: Similaridade de keywords
    - Hallucination: Detecção de informações não presentes
    """
    
    def __init__(self):
        """Inicializa avaliador."""
        pass
    
    def evaluate_retrieval(
        self,
        retrieved_chunks: List[str],
        relevant_chunk_ids: List[int],
        retrieved_chunk_ids: List[int]
    ) -> Dict[str, float]:
        """
        Avalia qualidade do retrieval.
        
        Args:
            retrieved_chunks: Chunks recuperados
            relevant_chunk_ids: IDs dos chunks relevantes (ground truth)
            retrieved_chunk_ids: IDs dos chunks recuperados
            
        Returns:
            Dict com precision, recall, mrr, f1
        """
        relevant_set = set(relevant_chunk_ids)
        retrieved_set = set(retrieved_chunk_ids)
        
        # Precision: quantos recuperados são relevantes
        if not retrieved_set:
            precision = 0.0
        else:
            precision = len(relevant_set & retrieved_set) / len(retrieved_set)
        
        # Recall: quantos relevantes foram recuperados
        if not relevant_set:
            recall = 1.0  # Se não há relevantes, recall perfeito
        else:
            recall = len(relevant_set & retrieved_set) / len(relevant_set)
        
        # F1
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        # MRR (Mean Reciprocal Rank)
        mrr = self._calculate_mrr(retrieved_chunk_ids, relevant_chunk_ids)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'mrr': mrr
        }
    
    def _calculate_mrr(
        self,
        retrieved_ids: List[int],
        relevant_ids: List[int]
    ) -> float:
        """
        Calcula Mean Reciprocal Rank.
        
        Args:
            retrieved_ids: IDs recuperados (ordenados por rank)
            relevant_ids: IDs relevantes
            
        Returns:
            MRR score
        """
        relevant_set = set(relevant_ids)
        
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    def evaluate_faithfulness(
        self,
        answer: str,
        context_chunks: List[str]
    ) -> float:
        """
        Avalia fidelidade da resposta ao contexto.
        
        Mede quanto da resposta está baseada no contexto usando overlap de n-gramas.
        
        Args:
            answer: Resposta gerada
            context_chunks: Chunks do contexto
            
        Returns:
            Score de fidelidade (0-1)
        """
        # Concatenar contexto
        full_context = ' '.join(context_chunks).lower()
        answer_lower = answer.lower()
        
        # Extrair sentenças da resposta
        sentences = self._split_sentences(answer_lower)
        
        if not sentences:
            return 0.0
        
        # Calcular overlap para cada sentença
        faithful_sentences = 0
        
        for sentence in sentences:
            # Extrair n-gramas (trigrams)
            ngrams = self._get_ngrams(sentence, n=3)
            
            if not ngrams:
                continue
            
            # Verificar quantos n-gramas estão no contexto
            overlap = sum(1 for ng in ngrams if ng in full_context)
            overlap_ratio = overlap / len(ngrams)
            
            # Sentença é fiel se > 50% dos trigrams estão no contexto
            if overlap_ratio > 0.5:
                faithful_sentences += 1
        
        return faithful_sentences / len(sentences)
    
    def evaluate_answer_relevance(
        self,
        answer: str,
        question: str
    ) -> float:
        """
        Avalia relevância da resposta em relação à pergunta.
        
        Args:
            answer: Resposta gerada
            question: Pergunta original
            
        Returns:
            Score de relevância (0-1)
        """
        # Extrair keywords da pergunta
        question_keywords = self._extract_keywords(question)
        
        if not question_keywords:
            return 1.0  # Não pode avaliar
        
        # Verificar presença na resposta
        answer_lower = answer.lower()
        
        present_keywords = sum(
            1 for kw in question_keywords
            if kw in answer_lower
        )
        
        return present_keywords / len(question_keywords)
    
    def evaluate_context_relevance(
        self,
        context_chunks: List[str],
        question: str
    ) -> float:
        """
        Avalia se contexto recuperado é relevante para a pergunta.
        
        Args:
            context_chunks: Chunks recuperados
            question: Pergunta
            
        Returns:
            Score de relevância do contexto (0-1)
        """
        if not context_chunks:
            return 0.0
        
        # Extrair keywords da pergunta
        question_keywords = self._extract_keywords(question)
        
        if not question_keywords:
            return 1.0
        
        # Calcular relevância de cada chunk
        relevant_chunks = 0
        
        for chunk in context_chunks:
            chunk_lower = chunk.lower()
            
            # Chunk é relevante se contém > 30% das keywords
            present = sum(1 for kw in question_keywords if kw in chunk_lower)
            if present / len(question_keywords) > 0.3:
                relevant_chunks += 1
        
        return relevant_chunks / len(context_chunks)
    
    def detect_hallucination(
        self,
        answer: str,
        context_chunks: List[str]
    ) -> float:
        """
        Detecta potencial alucinação (informações não no contexto).
        
        Args:
            answer: Resposta gerada
            context_chunks: Contexto usado
            
        Returns:
            Score de alucinação (0-1, 0=sem alucinação)
        """
        # Extrair claims (sentenças declarativas)
        claims = self._extract_claims(answer)
        
        if not claims:
            return 0.0
        
        # Contexto completo
        full_context = ' '.join(context_chunks).lower()
        
        # Verificar cada claim
        unsupported_claims = 0
        
        for claim in claims:
            # Extrair termos importantes do claim
            terms = self._extract_important_terms(claim)
            
            # Verificar se termos aparecem no contexto
            support_ratio = sum(1 for term in terms if term in full_context) / len(terms)
            
            # Claim não suportado se < 40% dos termos aparecem
            if support_ratio < 0.4:
                unsupported_claims += 1
        
        return unsupported_claims / len(claims)
    
    def evaluate_citations(
        self,
        answer: str,
        context_chunks: List[str]
    ) -> Dict[str, any]:
        """
        Avalia citações na resposta.
        
        Args:
            answer: Resposta com citações
            context_chunks: Chunks do contexto
            
        Returns:
            Dict com has_citations, citation_count, accuracy
        """
        # Detectar citações
        citation_patterns = [
            r'(?:Art\.?|Artigo)\s*\d+',
            r'§\s*\d+',
            r'(?:Lei|IN)\s+(?:nº?\s*)?\d+',
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            citations.extend(matches)
        
        has_citations = len(citations) > 0
        
        # Validar se citações estão no contexto
        if not citations:
            return {
                'has_citations': False,
                'citation_count': 0,
                'accuracy': 1.0  # Sem citações = sem erro
            }
        
        full_context = ' '.join(context_chunks).lower()
        valid_citations = sum(
            1 for cit in citations
            if cit.lower() in full_context
        )
        
        accuracy = valid_citations / len(citations)
        
        return {
            'has_citations': has_citations,
            'citation_count': len(citations),
            'accuracy': accuracy
        }
    
    def evaluate_full_rag(
        self,
        question: str,
        answer: str,
        context_chunks: List[str],
        retrieved_chunk_ids: Optional[List[int]] = None,
        relevant_chunk_ids: Optional[List[int]] = None
    ) -> RAGMetrics:
        """
        Avaliação completa do sistema RAG.
        
        Args:
            question: Pergunta
            answer: Resposta gerada
            context_chunks: Contexto usado
            retrieved_chunk_ids: IDs recuperados (opcional)
            relevant_chunk_ids: IDs relevantes ground truth (opcional)
            
        Returns:
            RAGMetrics com todas as métricas
        """
        # Retrieval metrics (se disponível)
        if retrieved_chunk_ids and relevant_chunk_ids:
            retrieval = self.evaluate_retrieval(
                context_chunks,
                relevant_chunk_ids,
                retrieved_chunk_ids
            )
            retrieval_precision = retrieval['precision']
            retrieval_recall = retrieval['recall']
            retrieval_mrr = retrieval['mrr']
        else:
            retrieval_precision = 1.0
            retrieval_recall = 1.0
            retrieval_mrr = 1.0
        
        # Generation metrics
        faithfulness = self.evaluate_faithfulness(answer, context_chunks)
        answer_relevance = self.evaluate_answer_relevance(answer, question)
        context_relevance = self.evaluate_context_relevance(context_chunks, question)
        
        # Citations
        citation_eval = self.evaluate_citations(answer, context_chunks)
        
        # Hallucination
        hallucination_score = self.detect_hallucination(answer, context_chunks)
        
        # Overall score (média ponderada)
        overall_score = (
            0.15 * retrieval_precision +
            0.15 * retrieval_recall +
            0.25 * faithfulness +
            0.20 * answer_relevance +
            0.15 * context_relevance +
            0.10 * (1 - hallucination_score)  # Inverter pois menor é melhor
        )
        
        return RAGMetrics(
            retrieval_precision=retrieval_precision,
            retrieval_recall=retrieval_recall,
            retrieval_mrr=retrieval_mrr,
            faithfulness=faithfulness,
            answer_relevance=answer_relevance,
            context_relevance=context_relevance,
            has_citations=citation_eval['has_citations'],
            citation_accuracy=citation_eval['accuracy'],
            hallucination_score=hallucination_score,
            overall_score=overall_score
        )
    
    # Helper methods
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split texto em sentenças."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _get_ngrams(self, text: str, n: int = 3) -> List[str]:
        """Extrair n-gramas."""
        words = text.split()
        if len(words) < n:
            return []
        return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrair keywords (palavras > 3 chars, sem stopwords)."""
        stopwords = {
            'qual', 'quais', 'como', 'onde', 'quando', 'porque', 'para',
            'sobre', 'pode', 'posso', 'devo', 'isso', 'esse', 'aquele',
            'esta', 'este', 'pela', 'pelo', 'com', 'sem', 'mais', 'menos'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        
        return list(set(keywords))
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extrair sentenças declarativas."""
        # Sentenças que não terminam com '?'
        sentences = self._split_sentences(text)
        claims = [s for s in sentences if not s.endswith('?')]
        return claims
    
    def _extract_important_terms(self, text: str) -> List[str]:
        """Extrair termos importantes (substantivos, números, nomes)."""
        # Simplificado: palavras maiúsculas, números, palavras longas
        terms = []
        
        # Números
        numbers = re.findall(r'\b\d+(?:[.,]\d+)?\b', text)
        terms.extend(numbers)
        
        # Palavras capitalizadas (nomes próprios)
        caps = re.findall(r'\b[A-Z][a-z]+\b', text)
        terms.extend(caps)
        
        # Palavras longas (> 6 chars)
        long_words = [w for w in text.split() if len(w) > 6]
        terms.extend(long_words)
        
        return [t.lower() for t in terms]


def create_rag_evaluator() -> RAGEvaluator:
    """
    Factory function para criar avaliador RAG.
    
    Returns:
        RAGEvaluator configurado
    """
    return RAGEvaluator()


# Exemplo de uso
if __name__ == "__main__":
    evaluator = create_rag_evaluator()
    
    print("🧪 TESTE DO RAG EVALUATOR")
    print("=" * 60)
    
    # Dados de teste
    question = "Quais são as deduções permitidas no IRPF?"
    
    context_chunks = [
        "Art. 68. São permitidas deduções de despesas com educação até R$ 3.561,50.",
        "§ 1º. As deduções devem ser comprovadas com documentos.",
        "Art. 69. Despesas médicas podem ser deduzidas integralmente."
    ]
    
    answer = """De acordo com o Art. 68, são permitidas deduções de:
    1. Despesas com educação até R$ 3.561,50
    2. Despesas médicas sem limite (Art. 69)
    
    As deduções requerem comprovação documental conforme § 1º."""
    
    # Avaliar
    metrics = evaluator.evaluate_full_rag(
        question=question,
        answer=answer,
        context_chunks=context_chunks
    )
    
    print(f"\n📊 MÉTRICAS RAG:")
    print(f"   Faithfulness: {metrics.faithfulness:.2f}")
    print(f"   Answer Relevance: {metrics.answer_relevance:.2f}")
    print(f"   Context Relevance: {metrics.context_relevance:.2f}")
    print(f"   Has Citations: {metrics.has_citations}")
    print(f"   Citation Accuracy: {metrics.citation_accuracy:.2f}")
    print(f"   Hallucination Score: {metrics.hallucination_score:.2f}")
    print(f"   Overall Score: {metrics.overall_score:.2f}")
    
    # Teste de alucinação
    print(f"\n\n🔍 TESTE DE ALUCINAÇÃO:")
    hallucinated_answer = "O limite é R$ 10.000,00 e você pode deduzir carros."
    
    hallucination = evaluator.detect_hallucination(
        hallucinated_answer,
        context_chunks
    )
    
    print(f"   Answer: {hallucinated_answer}")
    print(f"   Hallucination Score: {hallucination:.2f}")
    print(f"   {'⚠️ Provável alucinação!' if hallucination > 0.5 else '✅ OK'}")
