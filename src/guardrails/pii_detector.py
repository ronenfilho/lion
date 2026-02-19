"""
PII Detector - LION
Detector de informações pessoais identificáveis (PII)
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PIIMatch:
    """Match de PII encontrado"""
    type: str  # cpf, email, phone, name, address, etc.
    value: str
    start: int
    end: int
    confidence: float  # 0.0-1.0


class PIIDetector:
    """
    Detector de PII usando regex patterns.
    
    Detecta:
    - CPF/CNPJ
    - Email
    - Telefone
    - Cartão de crédito
    - Endereço (básico)
    - CEP
    """
    
    # Patterns regex otimizados para Brasil
    PATTERNS = {
        'cpf': {
            'pattern': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
            'confidence': 0.9
        },
        'cnpj': {
            'pattern': r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',
            'confidence': 0.9
        },
        'email': {
            'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'confidence': 0.95
        },
        'phone': {
            'pattern': r'\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b',
            'confidence': 0.8
        },
        'credit_card': {
            'pattern': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'confidence': 0.7  # Pode ter falsos positivos
        },
        'cep': {
            'pattern': r'\b\d{5}-?\d{3}\b',
            'confidence': 0.85
        },
        'rg': {
            'pattern': r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9xX]\b',
            'confidence': 0.75
        }
    }
    
    def __init__(self, sensitivity: str = 'medium'):
        """
        Inicializa detector.
        
        Args:
            sensitivity: Sensibilidade de detecção
                - 'low': Apenas alta confiança (>0.9)
                - 'medium': Confiança média (>0.7)
                - 'high': Detecta tudo (>0.5)
        """
        self.sensitivity = sensitivity
        self.confidence_threshold = {
            'low': 0.9,
            'medium': 0.7,
            'high': 0.5
        }.get(sensitivity, 0.7)
        
        # Compilar patterns
        self.compiled_patterns = {
            pii_type: re.compile(info['pattern'])
            for pii_type, info in self.PATTERNS.items()
        }
    
    def detect(self, text: str) -> List[PIIMatch]:
        """
        Detecta PII no texto.
        
        Args:
            text: Texto para análise
            
        Returns:
            Lista de PIIMatch encontrados
        """
        matches = []
        
        for pii_type, pattern in self.compiled_patterns.items():
            confidence = self.PATTERNS[pii_type]['confidence']
            
            # Apenas detectar se confiança >= threshold
            if confidence < self.confidence_threshold:
                continue
            
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence
                ))
        
        # Ordenar por posição
        matches.sort(key=lambda x: x.start)
        
        return matches
    
    def mask(self, text: str, mask_char: str = '*') -> Tuple[str, List[PIIMatch]]:
        """
        Detecta e mascara PII no texto.
        
        Args:
            text: Texto original
            mask_char: Caractere para mascarar
            
        Returns:
            Tupla (texto_mascarado, list[PIIMatch])
        """
        matches = self.detect(text)
        
        if not matches:
            return text, []
        
        # Construir texto mascarado
        masked_text = text
        offset = 0
        
        for match in matches:
            # Calcular posições ajustadas pelo offset
            start = match.start + offset
            end = match.end + offset
            
            # Criar máscara
            mask_length = end - start
            mask = mask_char * mask_length
            
            # Substituir
            masked_text = masked_text[:start] + mask + masked_text[end:]
            
            # Offset não muda pois tamanho é o mesmo
        
        return masked_text, matches
    
    def redact(self, text: str, redaction_type: str = 'type') -> Tuple[str, List[PIIMatch]]:
        """
        Detecta e remove PII, substituindo por placeholder.
        
        Args:
            text: Texto original
            redaction_type: Tipo de redação
                - 'type': [CPF], [EMAIL], etc.
                - 'generic': [REDACTED]
                - 'partial': Mantém parte do dado (ex: ***789-01)
                
        Returns:
            Tupla (texto_redacted, list[PIIMatch])
        """
        matches = self.detect(text)
        
        if not matches:
            return text, []
        
        # Construir texto com redações
        redacted_text = text
        offset = 0
        
        for match in matches:
            start = match.start + offset
            end = match.end + offset
            original_length = end - start
            
            # Escolher placeholder
            if redaction_type == 'type':
                placeholder = f"[{match.type.upper()}]"
            elif redaction_type == 'generic':
                placeholder = "[REDACTED]"
            elif redaction_type == 'partial':
                placeholder = self._partial_redact(match.value, match.type)
            else:
                placeholder = "[REDACTED]"
            
            # Substituir
            redacted_text = redacted_text[:start] + placeholder + redacted_text[end:]
            
            # Atualizar offset
            offset += len(placeholder) - original_length
        
        return redacted_text, matches
    
    def _partial_redact(self, value: str, pii_type: str) -> str:
        """
        Redação parcial mantendo últimos dígitos.
        
        Args:
            value: Valor original
            pii_type: Tipo de PII
            
        Returns:
            Valor parcialmente redacted
        """
        if pii_type in ['cpf', 'cnpj', 'phone']:
            # Manter últimos 4 dígitos
            digits = re.sub(r'\D', '', value)
            if len(digits) >= 4:
                return '***' + digits[-4:]
            return '***'
        
        elif pii_type == 'email':
            # Manter domínio
            if '@' in value:
                parts = value.split('@')
                return '***@' + parts[1]
            return '***'
        
        else:
            return '***'
    
    def has_pii(self, text: str) -> bool:
        """
        Verifica se texto contém PII.
        
        Args:
            text: Texto para verificar
            
        Returns:
            True se contém PII
        """
        matches = self.detect(text)
        return len(matches) > 0
    
    def get_pii_summary(self, text: str) -> Dict[str, int]:
        """
        Sumário de PII encontrados por tipo.
        
        Args:
            text: Texto para análise
            
        Returns:
            Dict com contagem por tipo
        """
        matches = self.detect(text)
        
        summary = {}
        for match in matches:
            summary[match.type] = summary.get(match.type, 0) + 1
        
        return summary


def create_pii_detector(sensitivity: str = 'medium') -> PIIDetector:
    """
    Factory function para criar detector de PII.
    
    Args:
        sensitivity: Nível de sensibilidade
        
    Returns:
        PIIDetector configurado
    """
    return PIIDetector(sensitivity=sensitivity)


# Exemplo de uso
if __name__ == "__main__":
    detector = create_pii_detector(sensitivity='medium')
    
    # Texto de teste
    test_text = """
    Olá, meu nome é João Silva. Meu CPF é 123.456.789-01 e meu telefone 
    é (11) 98765-4321. Você pode me enviar um email para joao@example.com.
    Meu CEP é 01234-567 e meu cartão é 1234 5678 9012 3456.
    """
    
    print("🔍 TESTE DO PII DETECTOR")
    print("=" * 60)
    
    # Detectar
    matches = detector.detect(test_text)
    print(f"\n✅ PII encontrados: {len(matches)}")
    for match in matches:
        print(f"   • {match.type.upper()}: {match.value} (conf: {match.confidence})")
    
    # Mascarar
    print("\n🔒 Texto mascarado:")
    masked, _ = detector.mask(test_text)
    print(masked[:200])
    
    # Redatar (type)
    print("\n🔒 Texto redacted (type):")
    redacted, _ = detector.redact(test_text, redaction_type='type')
    print(redacted[:200])
    
    # Redatar (partial)
    print("\n🔒 Texto redacted (partial):")
    redacted_partial, _ = detector.redact(test_text, redaction_type='partial')
    print(redacted_partial[:200])
    
    # Sumário
    print("\n📊 Sumário:")
    summary = detector.get_pii_summary(test_text)
    for pii_type, count in summary.items():
        print(f"   • {pii_type}: {count}")
