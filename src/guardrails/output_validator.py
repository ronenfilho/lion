"""
Output Validator - LION
Validação de saída do LLM com verificações de qualidade e segurança
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OutputValidationResult:
    """Resultado da validação de saída"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    quality_score: float  # 0.0-1.0
    has_citations: bool
    citation_accuracy: float  # 0.0-1.0 (% de citações válidas)
    is_relevant: bool
    hallucination_risk: float  # 0.0-1.0 (risco de alucinação)


class OutputValidator:
    """
    Validador de saída do LLM.
    
    Validações implementadas:
    1. Verificação de citações
    2. Detecção de alucinações
    3. Relevância da resposta
    4. Qualidade do conteúdo
    5. Conformidade com guidelines
    6. Verificação de disclaimers
    """
    
    # Frases que indicam alucinação/incerteza
    HALLUCINATION_INDICATORS = [
        r'\b(?:não tenho certeza|não sei ao certo|acho que|talvez)\b',
        r'\b(?:pode ser que|possivelmente|provavelmente)\b',
        r'\b(?:conforme meu conhecimento|até onde sei)\b',
        r'\b(?:não consigo confirmar|não posso garantir)\b',
    ]
    
    # Frases que indicam falta de informação (correto)
    HONEST_UNCERTAINTY = [
        r'não encontrei (?:essa informação|esses dados)',
        r'não há informação disponível',
        r'não consta nos documentos',
        r'não está presente no contexto',
    ]
    
    # Patterns de citação válida
    CITATION_PATTERNS = [
        r'(?:Art\.?|Artigo)\s*\d+',
        r'§\s*\d+º?',
        r'(?:Lei|Decreto|Instrução Normativa)\s+(?:nº?\s*)?\d+',
        r'IN\s+RFB\s+(?:nº?\s*)?\d+',
    ]
    
    def __init__(
        self,
        require_citations: bool = True,
        min_quality_score: float = 0.6,
        check_hallucinations: bool = True,
        require_disclaimer: bool = False
    ):
        """
        Inicializa validador de saída.
        
        Args:
            require_citations: Exigir citações na resposta
            min_quality_score: Score mínimo de qualidade
            check_hallucinations: Verificar indicadores de alucinação
            require_disclaimer: Exigir disclaimer na resposta
        """
        self.require_citations = require_citations
        self.min_quality_score = min_quality_score
        self.check_hallucinations = check_hallucinations
        self.require_disclaimer = require_disclaimer
        
        # Compilar patterns
        self.hallucination_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.HALLUCINATION_INDICATORS
        ]
        
        self.honest_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.HONEST_UNCERTAINTY
        ]
        
        self.citation_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.CITATION_PATTERNS
        ]
    
    def validate(
        self,
        response: str,
        query: str,
        context_chunks: Optional[List[str]] = None
    ) -> OutputValidationResult:
        """
        Valida resposta do LLM.
        
        Args:
            response: Resposta gerada
            query: Pergunta original
            context_chunks: Chunks usados no contexto (opcional)
            
        Returns:
            OutputValidationResult
        """
        errors = []
        warnings = []
        
        # 1. Validar comprimento
        if len(response) < 20:
            errors.append("Resposta muito curta (< 20 caracteres)")
        
        if len(response) > 3000:
            warnings.append("Resposta muito longa (> 3000 caracteres)")
        
        # 2. Verificar citações
        has_citations, citations_found = self._check_citations(response)
        
        if self.require_citations and not has_citations:
            # Verificar se é uma resposta de "não encontrei"
            is_honest_no_info = any(p.search(response) for p in self.honest_patterns)
            if not is_honest_no_info:
                warnings.append("Resposta não contém citações de fontes")
        
        # 3. Validar citações contra contexto
        citation_accuracy = 1.0
        if context_chunks and citations_found:
            citation_accuracy = self._validate_citations_accuracy(
                citations_found,
                context_chunks
            )
            
            if citation_accuracy < 0.8:
                warnings.append(
                    f"Algumas citações podem não estar no contexto "
                    f"(acurácia: {citation_accuracy:.1%})"
                )
        
        # 4. Detectar alucinações
        hallucination_risk = 0.0
        if self.check_hallucinations:
            hallucination_risk = self._detect_hallucinations(response)
            
            if hallucination_risk > 0.5:
                errors.append(
                    "Resposta contém indicadores de incerteza ou alucinação"
                )
            elif hallucination_risk > 0.3:
                warnings.append("Resposta pode conter informações incertas")
        
        # 5. Verificar relevância
        is_relevant = self._check_relevance(response, query)
        
        if not is_relevant:
            warnings.append("Resposta pode não estar respondendo à pergunta")
        
        # 6. Calcular score de qualidade
        quality_score = self._calculate_quality_score(
            response=response,
            has_citations=has_citations,
            citation_accuracy=citation_accuracy,
            hallucination_risk=hallucination_risk,
            is_relevant=is_relevant
        )
        
        if quality_score < self.min_quality_score:
            errors.append(
                f"Qualidade da resposta abaixo do mínimo "
                f"({quality_score:.2f} < {self.min_quality_score})"
            )
        
        # 7. Verificar disclaimer
        if self.require_disclaimer:
            if not self._has_disclaimer(response):
                warnings.append("Resposta não contém disclaimer recomendado")
        
        # 8. Verificar respostas vazias/genéricas
        if self._is_generic_response(response):
            warnings.append("Resposta pode ser muito genérica")
        
        return OutputValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score,
            has_citations=has_citations,
            citation_accuracy=citation_accuracy,
            is_relevant=is_relevant,
            hallucination_risk=hallucination_risk
        )
    
    def _check_citations(self, response: str) -> Tuple[bool, List[str]]:
        """
        Verifica presença de citações.
        
        Args:
            response: Texto da resposta
            
        Returns:
            Tupla (has_citations, list_of_citations)
        """
        citations = []
        
        for pattern in self.citation_patterns:
            matches = pattern.findall(response)
            citations.extend(matches)
        
        return len(citations) > 0, citations
    
    def _validate_citations_accuracy(
        self,
        citations: List[str],
        context_chunks: List[str]
    ) -> float:
        """
        Valida se citações estão presentes no contexto.
        
        Args:
            citations: Lista de citações encontradas
            context_chunks: Chunks do contexto
            
        Returns:
            Score de acurácia (0.0-1.0)
        """
        if not citations:
            return 1.0
        
        # Concatenar contexto
        full_context = ' '.join(context_chunks).lower()
        
        # Verificar quantas citações estão no contexto
        valid_citations = 0
        for citation in citations:
            # Normalizar citação
            normalized = citation.lower().replace(' ', '')
            
            if normalized in full_context.replace(' ', ''):
                valid_citations += 1
        
        return valid_citations / len(citations)
    
    def _detect_hallucinations(self, response: str) -> float:
        """
        Detecta indicadores de alucinação.
        
        Args:
            response: Texto da resposta
            
        Returns:
            Score de risco (0.0-1.0)
        """
        # Contar matches de indicadores
        indicator_count = 0
        for pattern in self.hallucination_patterns:
            matches = pattern.findall(response)
            indicator_count += len(matches)
        
        # Verificar respostas honestas de "não sei"
        has_honest_uncertainty = any(p.search(response) for p in self.honest_patterns)
        
        # Se diz honestamente que não sabe, não é alucinação
        if has_honest_uncertainty:
            return 0.0
        
        # Normalizar por comprimento (indicadores por 100 palavras)
        words = len(response.split())
        if words == 0:
            return 0.0
        
        normalized_count = (indicator_count / words) * 100
        
        # Mapear para 0-1
        risk_score = min(1.0, normalized_count / 5)  # 5+ indicadores = alto risco
        
        return risk_score
    
    def _check_relevance(self, response: str, query: str) -> bool:
        """
        Verifica relevância da resposta em relação à query.
        
        Args:
            response: Resposta gerada
            query: Pergunta original
            
        Returns:
            True se relevante
        """
        # Extrair palavras-chave da query (simplificado)
        query_words = set(
            word.lower() for word in re.findall(r'\b\w+\b', query)
            if len(word) > 3  # Ignorar palavras curtas
        )
        
        # Stopwords comuns (simplificado)
        stopwords = {
            'qual', 'quais', 'como', 'onde', 'quando', 'porque', 'para',
            'sobre', 'pode', 'posso', 'devo', 'isso', 'esse', 'aquele'
        }
        query_words -= stopwords
        
        if not query_words:
            return True  # Não pode validar
        
        # Verificar se palavras-chave aparecem na resposta
        response_lower = response.lower()
        
        overlap = sum(1 for word in query_words if word in response_lower)
        relevance_ratio = overlap / len(query_words)
        
        # Considerar relevante se > 30% de overlap
        return relevance_ratio > 0.3
    
    def _calculate_quality_score(
        self,
        response: str,
        has_citations: bool,
        citation_accuracy: float,
        hallucination_risk: float,
        is_relevant: bool
    ) -> float:
        """
        Calcula score de qualidade geral.
        
        Args:
            response: Texto da resposta
            has_citations: Se tem citações
            citation_accuracy: Acurácia das citações
            hallucination_risk: Risco de alucinação
            is_relevant: Se é relevante
            
        Returns:
            Score de qualidade (0.0-1.0)
        """
        score = 0.5  # Base
        
        # +0.2 por citações
        if has_citations:
            score += 0.2 * citation_accuracy
        
        # +0.15 por relevância
        if is_relevant:
            score += 0.15
        
        # +0.15 por comprimento adequado
        length = len(response)
        if 50 <= length <= 1500:
            score += 0.15
        elif length > 1500:
            score += 0.05
        
        # -0.3 por risco de alucinação
        score -= 0.3 * hallucination_risk
        
        # Garantir 0-1
        return max(0.0, min(1.0, score))
    
    def _has_disclaimer(self, response: str) -> bool:
        """
        Verifica se resposta contém disclaimer.
        
        Args:
            response: Texto da resposta
            
        Returns:
            True se contém disclaimer
        """
        disclaimer_indicators = [
            '⚠️',
            'importante:',
            'aviso:',
            'consulte um',
            'busque orientação',
            'não constitui consultoria',
        ]
        
        response_lower = response.lower()
        return any(ind in response_lower for ind in disclaimer_indicators)
    
    def _is_generic_response(self, response: str) -> bool:
        """
        Detecta respostas muito genéricas.
        
        Args:
            response: Texto da resposta
            
        Returns:
            True se resposta é genérica
        """
        generic_phrases = [
            'depende do caso',
            'varia de acordo',
            'consulte um especialista',
            'entre em contato',
            'não posso fornecer',
        ]
        
        response_lower = response.lower()
        
        # Se resposta tem apenas frases genéricas
        has_generic = sum(1 for phrase in generic_phrases if phrase in response_lower)
        
        return has_generic >= 2 and len(response) < 200


def create_output_validator(
    require_citations: bool = True,
    min_quality_score: float = 0.6
) -> OutputValidator:
    """
    Factory function para criar validador de saída.
    
    Args:
        require_citations: Exigir citações
        min_quality_score: Score mínimo de qualidade
        
    Returns:
        OutputValidator configurado
    """
    return OutputValidator(
        require_citations=require_citations,
        min_quality_score=min_quality_score
    )


# Exemplo de uso
if __name__ == "__main__":
    validator = create_output_validator()
    
    print("🛡️ TESTE DO OUTPUT VALIDATOR")
    print("=" * 60)
    
    # Casos de teste
    test_cases = [
        {
            'response': """De acordo com o Art. 68, § 1º, são permitidas deduções 
            de despesas com educação até R$ 3.561,50 por dependente.""",
            'query': 'Quais deduções são permitidas?',
            'context': ['Art. 68, § 1º. São permitidas deduções...'],
            'description': 'Resposta válida com citação'
        },
        {
            'response': 'Não encontrei essa informação nos documentos consultados.',
            'query': 'Quanto é a multa?',
            'context': [],
            'description': 'Resposta honesta de não-informação'
        },
        {
            'response': 'Talvez você possa deduzir, mas não tenho certeza.',
            'query': 'Posso deduzir?',
            'context': [],
            'description': 'Resposta com alucinação'
        },
        {
            'response': 'Python é uma linguagem de programação.',
            'query': 'Quais são as deduções do IRPF?',
            'context': [],
            'description': 'Resposta irrelevante'
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Teste {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Response: {test['response'][:80]}...")
        
        result = validator.validate(
            response=test['response'],
            query=test['query'],
            context_chunks=test.get('context', [])
        )
        
        print(f"\n{'✅ Válido' if result.is_valid else '❌ Inválido'}")
        print(f"Score de qualidade: {result.quality_score:.2f}")
        print(f"Citações: {'Sim' if result.has_citations else 'Não'}")
        print(f"Relevante: {'Sim' if result.is_relevant else 'Não'}")
        print(f"Risco de alucinação: {result.hallucination_risk:.2f}")
        
        if result.errors:
            print(f"Erros: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")
