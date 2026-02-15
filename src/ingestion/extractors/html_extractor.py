"""
HTML Extractor - LION
Extrai texto estruturado de documentos HTML
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag


@dataclass
class HTMLSection:
    """Representa uma seção extraída do HTML"""
    title: str
    content: str
    level: int  # Nível hierárquico (1=h1, 2=h2, etc.)
    metadata: Dict[str, any]
    tag_name: str


class HTMLExtractor:
    """
    Extrai texto estruturado de documentos HTML
    
    Funcionalidades:
    - Extração de texto preservando hierarquia
    - Identificação de seções (h1, h2, h3, etc.)
    - Remoção de scripts, estilos e elementos não textuais
    - Preservação de estrutura de listas e tabelas
    - Extração de metadados HTML
    """
    
    def __init__(
        self,
        remove_scripts: bool = True,
        remove_styles: bool = True,
        preserve_links: bool = False,
        min_section_length: int = 50
    ):
        """
        Inicializa o extrator de HTML
        
        Args:
            remove_scripts: Remover tags <script>
            remove_styles: Remover tags <style>
            preserve_links: Preservar URLs dos links
            min_section_length: Tamanho mínimo de seção em caracteres
        """
        self.remove_scripts = remove_scripts
        self.remove_styles = remove_styles
        self.preserve_links = preserve_links
        self.min_section_length = min_section_length
    
    def extract(self, html_path: str) -> Dict[str, any]:
        """
        Extrai conteúdo completo do HTML
        
        Args:
            html_path: Caminho para o arquivo HTML
            
        Returns:
            Dict contendo:
                - metadata: Metadados do documento
                - sections: Lista de seções extraídas
                - full_text: Texto completo do documento
        """
        html_path = Path(html_path)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML não encontrado: {html_path}")
        
        # Tenta múltiplos encodings comuns em documentos brasileiros
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                with open(html_path, 'r', encoding=encoding) as f:
                    html_content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            # Se nenhum encoding funcionar, usa latin-1 com tratamento de erros
            with open(html_path, 'r', encoding='latin-1', errors='replace') as f:
                html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Limpar elementos indesejados
        if self.remove_scripts:
            for script in soup.find_all('script'):
                script.decompose()
        
        if self.remove_styles:
            for style in soup.find_all('style'):
                style.decompose()
        
        # Extrair metadados
        metadata = self._extract_metadata(soup)
        
        # Identificar seções baseadas em headers
        sections = self._identify_sections(soup)
        
        # Texto completo
        full_text = "\n\n".join([s.content for s in sections if s.content])
        
        return {
            "metadata": metadata,
            "sections": sections,
            "full_text": full_text,
            "source": str(html_path.name)
        }
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extrai metadados do HTML
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Dict com metadados
        """
        metadata = {}
        
        # Título
        title_tag = soup.find('title')
        metadata['title'] = title_tag.get_text().strip() if title_tag else ""
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # H1 principal (se não houver title)
        if not metadata['title']:
            h1 = soup.find('h1')
            if h1:
                metadata['title'] = h1.get_text().strip()
        
        return metadata
    
    def _identify_sections(self, soup: BeautifulSoup) -> List[HTMLSection]:
        """
        Identifica seções no documento baseado em headers (h1-h6)
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Lista de seções identificadas
        """
        sections = []
        
        # Encontrar todos os headers e conteúdo subsequente
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headers:
            # Se não há headers, extrair todo o body
            body = soup.find('body')
            if body:
                content = self._extract_text_content(body)
                if len(content) >= self.min_section_length:
                    sections.append(HTMLSection(
                        title="Documento Completo",
                        content=content,
                        level=1,
                        metadata={"type": "full_document"},
                        tag_name="body"
                    ))
            return sections
        
        for i, header in enumerate(headers):
            # Extrair título do header
            title = header.get_text().strip()
            if not title:
                continue
            
            # Determinar nível (h1=1, h2=2, etc.)
            level = int(header.name[1])
            
            # Coletar conteúdo até o próximo header
            content_elements = []
            current = header.next_sibling
            
            while current:
                # Parar se encontrar outro header
                if hasattr(current, 'name') and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                
                # Adicionar elemento se for tag
                if isinstance(current, Tag):
                    text = self._extract_text_content(current)
                    if text.strip():
                        content_elements.append(text)
                
                current = current.next_sibling
            
            # Montar conteúdo da seção
            content = "\n".join(content_elements).strip()
            
            # Adicionar seção se tiver conteúdo suficiente
            if len(content) >= self.min_section_length or level <= 2:
                sections.append(HTMLSection(
                    title=title,
                    content=content,
                    level=level,
                    metadata={"type": "section", "header": header.name},
                    tag_name=header.name
                ))
        
        return sections
    
    def _extract_text_content(self, element: Tag) -> str:
        """
        Extrai texto de um elemento HTML
        
        Args:
            element: Elemento BeautifulSoup
            
        Returns:
            Texto extraído
        """
        # Tratar listas
        if element.name in ['ul', 'ol']:
            items = []
            for li in element.find_all('li', recursive=False):
                text = li.get_text(separator=' ', strip=True)
                items.append(f"• {text}")
            return "\n".join(items)
        
        # Tratar tabelas
        if element.name == 'table':
            return self._extract_table_text(element)
        
        # Tratar parágrafos e divs
        if element.name in ['p', 'div', 'section', 'article']:
            text = element.get_text(separator=' ', strip=True)
            return text
        
        # Texto genérico
        return element.get_text(separator=' ', strip=True)
    
    def _extract_table_text(self, table: Tag) -> str:
        """
        Extrai texto de uma tabela HTML
        
        Args:
            table: Elemento table
            
        Returns:
            Texto formatado da tabela
        """
        rows = []
        
        # Headers
        headers = table.find_all('th')
        if headers:
            header_text = ' | '.join([th.get_text(strip=True) for th in headers])
            rows.append(header_text)
            rows.append('-' * len(header_text))
        
        # Linhas
        for tr in table.find_all('tr'):
            cells = tr.find_all(['td', 'th'])
            if cells:
                row_text = ' | '.join([cell.get_text(strip=True) for cell in cells])
                rows.append(row_text)
        
        return '\n'.join(rows)
    
    def extract_links(self, html_path: str) -> List[Dict[str, str]]:
        """
        Extrai todos os links do documento HTML
        
        Args:
            html_path: Caminho para o arquivo HTML
            
        Returns:
            Lista de dicionários com texto e URL dos links
        """
        html_path = Path(html_path)
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            links.append({
                'text': a.get_text(strip=True),
                'url': a['href']
            })
        
        return links


def extract_html(html_path: str, **kwargs) -> Dict[str, any]:
    """
    Função helper para extração rápida de HTML
    
    Args:
        html_path: Caminho para o HTML
        **kwargs: Argumentos adicionais para HTMLExtractor
        
    Returns:
        Dict com conteúdo extraído
    """
    extractor = HTMLExtractor(**kwargs)
    return extractor.extract(html_path)


if __name__ == "__main__":
    # Teste básico
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python html_extractor.py <caminho_html>")
        sys.exit(1)
    
    html_path = sys.argv[1]
    
    print(f"🌐 Extraindo HTML: {html_path}")
    print("=" * 60)
    
    result = extract_html(html_path)
    
    print(f"✅ Metadados:")
    for key, value in result["metadata"].items():
        if value:
            print(f"   {key}: {value[:100]}")
    
    print(f"\n📊 Estatísticas:")
    print(f"   Seções: {len(result['sections'])}")
    print(f"   Caracteres: {len(result['full_text'])}")
    
    print(f"\n📑 Seções encontradas:")
    for i, section in enumerate(result["sections"][:10], 1):
        print(f"   {i}. {section.title} (nível {section.level})")
        print(f"      Tamanho: {len(section.content)} caracteres")
        print(f"      Preview: {section.content[:150]}...")
        print()
    
    if len(result["sections"]) > 10:
        print(f"   ... e mais {len(result['sections']) - 10} seções")
