"""
Text Cleaner - LION
Normaliza e limpa texto extraído de documentos
"""

import re
import unicodedata
from typing import List, Optional


class TextCleaner:
    """
    Limpa e normaliza texto extraído de documentos
    
    Funcionalidades:
    - Normalização de espaços e quebras de linha
    - Remoção de caracteres especiais
    - Normalização de Unicode
    - Remoção de headers/footers repetidos
    - Correção de hifenização
    """
    
    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        fix_hyphenation: bool = True,
        remove_urls: bool = False,
        lowercase: bool = False
    ):
        """
        Inicializa o limpador de texto
        
        Args:
            remove_extra_whitespace: Remove espaços extras
            normalize_unicode: Normaliza caracteres Unicode
            fix_hyphenation: Corrige palavras hifenizadas
            remove_urls: Remove URLs do texto
            lowercase: Converte para minúsculas
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.fix_hyphenation = fix_hyphenation
        self.remove_urls = remove_urls
        self.lowercase = lowercase
    
    def clean(self, text: str) -> str:
        """
        Aplica todas as limpezas configuradas no texto
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        cleaned = text
        
        # Normalizar Unicode
        if self.normalize_unicode:
            cleaned = self._normalize_unicode(cleaned)
        
        # Corrigir hifenização
        if self.fix_hyphenation:
            cleaned = self._fix_hyphenation(cleaned)
        
        # Remover URLs
        if self.remove_urls:
            cleaned = self._remove_urls(cleaned)
        
        # Limpar espaços
        if self.remove_extra_whitespace:
            cleaned = self._clean_whitespace(cleaned)
        
        # Converter para minúsculas
        if self.lowercase:
            cleaned = cleaned.lower()
        
        return cleaned.strip()
    
    def _normalize_unicode(self, text: str) -> str:
        """
        Normaliza caracteres Unicode (NFD -> NFC)
        
        Args:
            text: Texto original
            
        Returns:
            Texto normalizado
        """
        # NFD = decomposição canônica
        # NFC = composição canônica (preferida para texto)
        return unicodedata.normalize('NFC', text)
    
    def _fix_hyphenation(self, text: str) -> str:
        """
        Corrige palavras quebradas por hifenização
        
        Exemplo: "documen-\nto" -> "documento"
        
        Args:
            text: Texto com hifenização
            
        Returns:
            Texto sem hifenização incorreta
        """
        # Padrão: palavra seguida de hífen e quebra de linha
        pattern = r'(\w+)-\s*\n\s*(\w+)'
        
        def replace_hyphen(match):
            # Verificar se é uma palavra composta legítima (ex: "guarda-chuva")
            word1, word2 = match.group(1), match.group(2)
            
            # Se word2 começa com minúscula, provavelmente é continuação
            if word2[0].islower():
                return word1 + word2
            else:
                return word1 + '-' + word2
        
        return re.sub(pattern, replace_hyphen, text)
    
    def _remove_urls(self, text: str) -> str:
        """
        Remove URLs do texto
        
        Args:
            text: Texto com URLs
            
        Returns:
            Texto sem URLs
        """
        # Padrão para URLs
        url_pattern = r'https?://\S+|www\.\S+'
        return re.sub(url_pattern, '', text)
    
    def _clean_whitespace(self, text: str) -> str:
        """
        Limpa espaços em branco excessivos
        
        Args:
            text: Texto com espaços extras
            
        Returns:
            Texto com espaços normalizados
        """
        # Substituir múltiplos espaços por um único
        text = re.sub(r' +', ' ', text)
        
        # Substituir múltiplas quebras de linha por no máximo duas
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remover espaços no início e fim de cada linha
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def remove_repeated_headers(
        self, 
        text: str, 
        min_repetitions: int = 3
    ) -> str:
        """
        Remove headers/footers repetidos em documentos
        
        Args:
            text: Texto completo
            min_repetitions: Número mínimo de repetições para considerar header
            
        Returns:
            Texto sem headers repetidos
        """
        lines = text.split('\n')
        
        # Contar ocorrências de cada linha
        line_counts = {}
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and len(line_stripped) < 100:  # Headers geralmente são curtos
                line_counts[line_stripped] = line_counts.get(line_stripped, 0) + 1
        
        # Identificar linhas que se repetem muito (headers/footers)
        repeated_lines = {
            line for line, count in line_counts.items() 
            if count >= min_repetitions
        }
        
        # Remover linhas repetidas
        cleaned_lines = [
            line for line in lines 
            if line.strip() not in repeated_lines or not line.strip()
        ]
        
        return '\n'.join(cleaned_lines)
    
    def clean_legal_text(self, text: str) -> str:
        """
        Limpeza especializada para textos legais brasileiros
        
        Args:
            text: Texto legal
            
        Returns:
            Texto limpo mantendo estrutura legal
        """
        cleaned = text
        
        # Normalizar referências legais
        # Ex: "art. 1º" -> "Art. 1º"
        cleaned = re.sub(
            r'\bart\.?\s+(\d+)', 
            r'Art. \1', 
            cleaned, 
            flags=re.IGNORECASE
        )
        
        # Normalizar parágrafos
        # Ex: "paragrafo 1" -> "§ 1º"
        cleaned = re.sub(
            r'\bpar[áa]grafo\s+(\d+)', 
            r'§ \1º', 
            cleaned, 
            flags=re.IGNORECASE
        )
        
        # Preservar estrutura de incisos (I, II, III, etc.)
        # Não fazer nada - apenas garantir que não sejam removidos
        
        return cleaned
    
    def split_sentences(self, text: str) -> List[str]:
        """
        Divide texto em sentenças
        
        Args:
            text: Texto completo
            
        Returns:
            Lista de sentenças
        """
        # Padrão básico de fim de sentença
        # Considera: ponto final, exclamação, interrogação
        # Mas não divide em abreviações comuns (Art., Dr., etc.)
        
        # Primeiro, proteger abreviações
        text = re.sub(r'\b(Art|Dr|Sr|Sra|Inc)\.\s', r'\1<PONTO> ', text)
        
        # Dividir em sentenças
        sentences = re.split(r'[.!?]\s+', text)
        
        # Restaurar pontos em abreviações
        sentences = [s.replace('<PONTO>', '.') for s in sentences]
        
        # Remover sentenças vazias
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences


def clean_text(text: str, **kwargs) -> str:
    """
    Função helper para limpeza rápida de texto
    
    Args:
        text: Texto a ser limpo
        **kwargs: Argumentos para TextCleaner
        
    Returns:
        Texto limpo
    """
    cleaner = TextCleaner(**kwargs)
    return cleaner.clean(text)


if __name__ == "__main__":
    # Testes básicos
    test_text = """
    Este    é  um   texto    com    espaços     extras.
    
    
    
    E   múltiplas  quebras   de   linha.
    
    Também tem pala-
    vras hifenizadas.
    
    E URLs como https://exemplo.com que podem ser removidas.
    
    Art. 1º - Este artigo trata de...
    § 1º - O parágrafo primeiro estabelece...
    """
    
    print("📝 Texto Original:")
    print("=" * 60)
    print(test_text)
    
    print("\n🧹 Texto Limpo:")
    print("=" * 60)
    cleaned = clean_text(test_text)
    print(cleaned)
    
    print("\n🏛️ Texto Legal Normalizado:")
    print("=" * 60)
    cleaner = TextCleaner()
    legal_cleaned = cleaner.clean_legal_text(cleaned)
    print(legal_cleaned)
