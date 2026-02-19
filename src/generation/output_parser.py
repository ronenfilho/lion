"""
Output Parser - LION
Parser para estruturar e validar respostas do LLM
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Citation:
    """Citação extraída da resposta"""
    article: Optional[str] = None  # Ex: "Art. 68"
    paragraph: Optional[str] = None  # Ex: "§ 1º"
    section: Optional[str] = None  # Ex: "Seção III"
    text: Optional[str] = None  # Trecho citado
    source_index: Optional[int] = None  # Índice do chunk usado


@dataclass
class ExtractedData:
    """Dados estruturados extraídos"""
    monetary_values: List[float] = field(default_factory=list)  # Valores em reais
    percentages: List[float] = field(default_factory=list)  # Percentuais
    dates: List[str] = field(default_factory=list)  # Datas mencionadas
    articles: List[str] = field(default_factory=list)  # Artigos citados
    key_terms: List[str] = field(default_factory=list)  # Termos importantes


@dataclass
class ParsedResponse:
    """Resposta parseada e estruturada"""
    raw_text: str
    clean_text: str
    citations: List[Citation]
    extracted_data: ExtractedData
    confidence: float  # 0.0-1.0
    has_answer: bool  # Se contém resposta definitiva
    needs_clarification: bool  # Se pede esclarecimentos
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'text': self.clean_text,
            'citations': [
                {
                    'article': c.article,
                    'paragraph': c.paragraph,
                    'text': c.text
                }
                for c in self.citations
            ],
            'data': {
                'values': self.extracted_data.monetary_values,
                'percentages': self.extracted_data.percentages,
                'dates': self.extracted_data.dates,
                'articles': self.extracted_data.articles
            },
            'confidence': self.confidence,
            'has_answer': self.has_answer,
            'warnings': self.warnings
        }


class OutputParser:
    """
    Parser para saídas do LLM.
    
    Extrai informações estruturadas, valida formato,
    identifica citações e dados numéricos.
    """
    
    # Patterns regex
    ARTICLE_PATTERN = r'(?:Art\.?|Artigo)\s*(\d+(?:-[A-Z])?)'
    PARAGRAPH_PATTERN = r'§\s*(\d+º?)'
    INCISO_PATTERN = r'inciso\s+([IVX]+|[a-z])'
    MONEY_PATTERN = r'R\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)'
    PERCENTAGE_PATTERN = r'(\d+(?:,\d+)?)\s*%'
    DATE_PATTERN = r'\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+de\s+\w+\s+de\s+\d{4}'
    
    # Frases que indicam falta de informação
    NO_INFO_PHRASES = [
        'não encontrei',
        'não há informação',
        'não consta',
        'não está presente',
        'não disponível',
        'informação ausente'
    ]
    
    # Frases que pedem esclarecimento
    CLARIFICATION_PHRASES = [
        'poderia esclarecer',
        'preciso de mais informações',
        'qual especificamente',
        'você pode especificar',
        'preciso saber'
    ]
    
    def __init__(self):
        """Inicializa parser."""
        pass
    
    def parse(self, response_text: str, context_chunks: Optional[List[str]] = None) -> ParsedResponse:
        """
        Parse completo da resposta do LLM.
        
        Args:
            response_text: Texto gerado pelo LLM
            context_chunks: Chunks usados no contexto (opcional)
            
        Returns:
            ParsedResponse com dados estruturados
        """
        # Limpar texto
        clean_text = self._clean_text(response_text)
        
        # Extrair citações
        citations = self._extract_citations(clean_text)
        
        # Extrair dados estruturados
        extracted_data = self._extract_structured_data(clean_text)
        
        # Calcular confiança
        confidence = self._calculate_confidence(clean_text, citations, extracted_data)
        
        # Detectar se tem resposta
        has_answer = self._has_definitive_answer(clean_text)
        
        # Detectar se pede esclarecimento
        needs_clarification = self._needs_clarification(clean_text)
        
        # Validar resposta
        warnings = self._validate_response(clean_text, citations, extracted_data)
        
        return ParsedResponse(
            raw_text=response_text,
            clean_text=clean_text,
            citations=citations,
            extracted_data=extracted_data,
            confidence=confidence,
            has_answer=has_answer,
            needs_clarification=needs_clarification,
            warnings=warnings
        )
    
    def _clean_text(self, text: str) -> str:
        """
        Limpa texto da resposta.
        
        Args:
            text: Texto bruto
            
        Returns:
            Texto limpo
        """
        # Remover espaços extras
        text = re.sub(r'\s+', ' ', text)
        
        # Remover marcadores de contexto se vazaram
        text = re.sub(r'\[Trecho \d+\]', '', text)
        
        return text.strip()
    
    def _extract_citations(self, text: str) -> List[Citation]:
        """
        Extrai citações de artigos, parágrafos, etc.
        
        Args:
            text: Texto da resposta
            
        Returns:
            Lista de citações
        """
        citations = []
        
        # Buscar artigos
        articles = re.finditer(self.ARTICLE_PATTERN, text, re.IGNORECASE)
        for match in articles:
            article_num = match.group(1)
            
            # Buscar parágrafo próximo
            paragraph = None
            remaining_text = text[match.end():match.end()+50]
            para_match = re.search(self.PARAGRAPH_PATTERN, remaining_text)
            if para_match:
                paragraph = para_match.group(1)
            
            citations.append(Citation(
                article=f"Art. {article_num}",
                paragraph=f"§ {paragraph}" if paragraph else None
            ))
        
        return citations
    
    def _extract_structured_data(self, text: str) -> ExtractedData:
        """
        Extrai dados estruturados (valores, percentuais, datas).
        
        Args:
            text: Texto da resposta
            
        Returns:
            ExtractedData
        """
        data = ExtractedData()
        
        # Valores monetários
        money_matches = re.finditer(self.MONEY_PATTERN, text)
        for match in money_matches:
            value_str = match.group(1).replace('.', '').replace(',', '.')
            try:
                data.monetary_values.append(float(value_str))
            except ValueError:
                pass
        
        # Percentuais
        perc_matches = re.finditer(self.PERCENTAGE_PATTERN, text)
        for match in perc_matches:
            perc_str = match.group(1).replace(',', '.')
            try:
                data.percentages.append(float(perc_str))
            except ValueError:
                pass
        
        # Datas
        date_matches = re.finditer(self.DATE_PATTERN, text)
        data.dates = [match.group(0) for match in date_matches]
        
        # Artigos citados
        article_matches = re.finditer(self.ARTICLE_PATTERN, text, re.IGNORECASE)
        data.articles = list(set([f"Art. {m.group(1)}" for m in article_matches]))
        
        # Termos-chave (palavras importantes em maiúsculas ou com destaque)
        # Ex: IRPF, DARF, etc.
        key_terms_pattern = r'\b[A-Z]{2,}\b'
        key_matches = re.finditer(key_terms_pattern, text)
        data.key_terms = list(set([m.group(0) for m in key_matches]))
        
        return data
    
    def _calculate_confidence(
        self,
        text: str,
        citations: List[Citation],
        extracted_data: ExtractedData
    ) -> float:
        """
        Calcula confiança na resposta.
        
        Fatores:
        - Presença de citações (+)
        - Dados estruturados (+)
        - Comprimento adequado (+)
        - Frases de incerteza (-)
        
        Args:
            text: Texto da resposta
            citations: Citações extraídas
            extracted_data: Dados extraídos
            
        Returns:
            Score de confiança (0.0-1.0)
        """
        score = 0.5  # Base
        
        # +0.2 se tem citações
        if citations:
            score += 0.2
        
        # +0.1 se tem dados numéricos
        if extracted_data.monetary_values or extracted_data.percentages:
            score += 0.1
        
        # +0.1 se tem comprimento razoável (50-1000 chars)
        if 50 <= len(text) <= 1000:
            score += 0.1
        
        # -0.2 por frases de incerteza
        uncertainty_words = ['talvez', 'possivelmente', 'provavelmente', 'pode ser']
        if any(word in text.lower() for word in uncertainty_words):
            score -= 0.2
        
        # -0.3 se diz que não tem informação
        if any(phrase in text.lower() for phrase in self.NO_INFO_PHRASES):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _has_definitive_answer(self, text: str) -> bool:
        """
        Verifica se resposta tem informação definitiva.
        
        Args:
            text: Texto da resposta
            
        Returns:
            True se tem resposta
        """
        # Se diz que não tem informação, não tem resposta definitiva
        if any(phrase in text.lower() for phrase in self.NO_INFO_PHRASES):
            return False
        
        # Se é muito curto, provavelmente não tem resposta completa
        if len(text) < 30:
            return False
        
        return True
    
    def _needs_clarification(self, text: str) -> bool:
        """
        Verifica se LLM está pedindo esclarecimento.
        
        Args:
            text: Texto da resposta
            
        Returns:
            True se pede esclarecimento
        """
        return any(phrase in text.lower() for phrase in self.CLARIFICATION_PHRASES)
    
    def _validate_response(
        self,
        text: str,
        citations: List[Citation],
        extracted_data: ExtractedData
    ) -> List[str]:
        """
        Valida resposta e retorna warnings.
        
        Args:
            text: Texto da resposta
            citations: Citações
            extracted_data: Dados extraídos
            
        Returns:
            Lista de warnings
        """
        warnings = []
        
        # Resposta muito curta
        if len(text) < 20:
            warnings.append("Resposta muito curta")
        
        # Resposta muito longa
        if len(text) > 2000:
            warnings.append("Resposta muito longa")
        
        # Sem citações em resposta sobre legislação
        legal_keywords = ['art.', 'artigo', 'lei', 'decreto', '§']
        if any(kw in text.lower() for kw in legal_keywords) and not citations:
            warnings.append("Menciona legislação mas não cita artigos específicos")
        
        # Valores sem contexto
        if extracted_data.monetary_values and not citations:
            warnings.append("Menciona valores mas sem referência legal")
        
        # Muita incerteza
        if text.lower().count('talvez') + text.lower().count('possivelmente') > 2:
            warnings.append("Muitas expressões de incerteza")
        
        return warnings
    
    def format_for_display(self, parsed: ParsedResponse) -> str:
        """
        Formata resposta parseada para exibição ao usuário.
        
        Args:
            parsed: Resposta parseada
            
        Returns:
            Texto formatado
        """
        output = parsed.clean_text
        
        # Adicionar seção de citações se houver
        if parsed.citations:
            output += "\n\n📚 **Referências:**\n"
            for citation in parsed.citations:
                ref = citation.article
                if citation.paragraph:
                    ref += f", {citation.paragraph}"
                output += f"- {ref}\n"
        
        # Adicionar warnings se houver
        if parsed.warnings:
            output += "\n\n⚠️ **Observações:**\n"
            for warning in parsed.warnings:
                output += f"- {warning}\n"
        
        return output


def create_output_parser() -> OutputParser:
    """
    Factory function para criar parser.
    
    Returns:
        OutputParser configurado
    """
    return OutputParser()


# Exemplo de uso
if __name__ == "__main__":
    parser = create_output_parser()
    
    # Teste com resposta simulada
    test_response = """
    De acordo com o Art. 68, § 1º, são permitidas deduções de despesas com educação 
    até o limite de R$ 3.561,50 por dependente. A alíquota aplicável é de 27,5% 
    para rendimentos acima de R$ 55.976,16 anuais.
    """
    
    parsed = parser.parse(test_response)
    
    print("📊 Análise da resposta:")
    print(f"\n   Texto limpo: {parsed.clean_text[:100]}...")
    print(f"\n   Citações encontradas: {len(parsed.citations)}")
    for citation in parsed.citations:
        print(f"      • {citation.article}")
    
    print(f"\n   Dados extraídos:")
    print(f"      • Valores: {parsed.extracted_data.monetary_values}")
    print(f"      • Percentuais: {parsed.extracted_data.percentages}")
    print(f"      • Artigos: {parsed.extracted_data.articles}")
    
    print(f"\n   Confiança: {parsed.confidence:.2f}")
    print(f"   Tem resposta definitiva: {parsed.has_answer}")
    print(f"   Warnings: {parsed.warnings if parsed.warnings else 'Nenhum'}")
    
    print("\n\n📝 Resposta formatada:")
    print(parser.format_for_display(parsed))
