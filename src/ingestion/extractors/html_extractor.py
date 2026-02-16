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
            Dict contendo metadata, sections e full_text
        """
        html_path = Path(html_path)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML não encontrado: {html_path}")
        
        # Ler HTML com encoding apropriado
        html_content = self._read_html_file(html_path)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Substituir <br> por quebras de linha antes de processar
        self._replace_br_tags(soup)
        
        # Limpar elementos indesejados
        self._clean_unwanted_elements(soup)
        
        # Extrair dados
        metadata = self._extract_metadata(soup)
        sections = self._identify_sections(soup)
        full_text = "\n\n".join([s.content for s in sections if s.content])
        
        result = {
            "metadata": metadata,
            "sections": sections,
            "full_text": full_text,
            "source": str(html_path.name)
        }
        
        # Salvar em Markdown
        self._save_to_markdown(html_path, result)
        
        return result
    
    def _read_html_file(self, html_path: Path) -> str:
        """Lê arquivo HTML tentando múltiplos encodings"""
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                with open(html_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # Fallback com tratamento de erros
        with open(html_path, 'r', encoding='latin-1', errors='replace') as f:
            return f.read()
    
    def _replace_br_tags(self, soup: BeautifulSoup) -> None:
        """Substitui tags <br> por quebras de linha"""
        for br in soup.find_all('br'):
            br.replace_with('\n')
    
    def _clean_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove elementos indesejados do HTML"""
        if self.remove_scripts:
            for script in soup.find_all('script'):
                script.decompose()
        
        if self.remove_styles:
            for style in soup.find_all('style'):
                style.decompose()
    
    def _save_to_markdown(self, source_path: Path, extracted_data: Dict[str, any]) -> None:
        """Salva o conteúdo extraído em formato Markdown estruturado"""
        import re
        from datetime import datetime
        
        # Criar diretório data/processed se não existir
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo: source_name_processed.md
        md_filename = source_path.stem + "_processed.md"
        md_path = processed_dir / md_filename
        
        # Reprocessar HTML original para capturar tabelas com encoding correto
        html_content = None
        for encoding in ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']:
            try:
                with open(source_path, 'r', encoding=encoding) as f:
                    html_content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if html_content is None:
            # Fallback
            with open(source_path, 'r', encoding='cp1252', errors='ignore') as f:
                html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Montar conteúdo Markdown
        md_lines = []
        
        # Cabeçalho do documento
        md_lines.append(f"# {extracted_data.get('metadata', {}).get('title', source_path.stem)}")
        md_lines.append("")
        md_lines.append(f"> **Fonte**: {source_path.name}  ")
        md_lines.append(f"> **Processado em**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        
        # Extrair artigos para o índice
        full_text = extracted_data.get("full_text", "")
        articles = re.findall(r'Art\.?\s*(\d+[º°]?(?:-[A-Z])?)', full_text)
        unique_articles = []
        for art in articles:
            if art not in unique_articles:
                unique_articles.append(art)
        
        # Índice (Table of Contents)
        if unique_articles:
            md_lines.append("## 📑 Índice")
            md_lines.append("")
            for art_num in unique_articles[:20]:
                art_id = art_num.replace('º', '').replace('°', '').lower()
                md_lines.append(f"- [Artigo {art_num}](#artigo-{art_id})")
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")
        
        # Metadados (seção colapsável)
        if extracted_data.get("metadata"):
            md_lines.append("<details>")
            md_lines.append("<summary>📋 Metadados do Documento</summary>")
            md_lines.append("")
            for key, value in extracted_data["metadata"].items():
                if value and key != 'title':
                    md_lines.append(f"- **{key}**: {value}")
            md_lines.append("")
            md_lines.append("</details>")
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")
        
        # Conteúdo estruturado processando HTML diretamente
        md_lines.append("## 📖 Texto Completo")
        md_lines.append("")
        
        # Processar HTML mantendo estrutura e tabelas
        content_lines = self._process_html_to_markdown(soup)
        md_lines.extend(content_lines)
        
        # Rodapé
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("*Documento processado automaticamente pelo LION RAG System*")
        
        # Salvar arquivo
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))
    
    def _format_article_content(self, text: str) -> List[str]:
        """Formata conteúdo de um artigo com parágrafos, incisos e alíneas"""
        import re
        
        lines = []
        
        # Primeiro, quebrar por parágrafo (§) para garantir separação visual
        para_parts = re.split(r'(\s§\s*(?:único|Único|\d+[º°]?))', text, flags=re.IGNORECASE)
        
        # Processar cada parte
        i = 0
        while i < len(para_parts):
            if i < len(para_parts) - 1 and re.match(r'^\s§', para_parts[i]):
                # É um marcador de parágrafo
                para_marker = para_parts[i].strip()
                para_content = para_parts[i + 1].strip() if i + 1 < len(para_parts) else ''
                
                # Separar incisos do conteúdo do parágrafo
                inciso_parts = re.split(r'(\n?\s*[IVX]+\s*[-–—]\s*)', para_content)
                
                # Conteúdo principal do parágrafo (antes dos incisos)
                main_content = inciso_parts[0].strip()
                
                # Remover capítulos que possam estar no final
                capitulo_match = re.search(r'(CAPÍTULO.*?)$', main_content)
                capitulo_text = ""
                if capitulo_match:
                    capitulo_text = capitulo_match.group(1).strip()
                    main_content = main_content[:capitulo_match.start()].strip()
                
                # Adicionar parágrafo principal
                lines.append("")
                full_para = f"{para_marker} {main_content}".strip()
                
                # Limitar tamanho para legibilidade
                if len(full_para) > 500:
                    sentences = re.split(r'(?<=[.;:])\s+', full_para)
                    lines.append(f"**{sentences[0]}**")
                    for sent in sentences[1:]:
                        if sent.strip():
                            lines.append(sent.strip())
                else:
                    lines.append(f"**{full_para}**")
                lines.append("")
                
                # Processar incisos se existirem
                j = 1
                while j < len(inciso_parts):
                    if re.match(r'^\n?\s*[IVX]+\s*[-–—]', inciso_parts[j]):
                        inciso_content = inciso_parts[j + 1].strip() if j + 1 < len(inciso_parts) else ''
                        lines.append(f"- {inciso_parts[j].strip()} {inciso_content}")
                        j += 2
                    else:
                        j += 1
                
                # Adicionar capítulo se existir
                if capitulo_text:
                    lines.append("")
                    lines.append(f"#### {capitulo_text}")
                    lines.append("")
                
                i += 2
            else:
                # Conteúdo normal ou antes do primeiro §
                content = para_parts[i].strip()
                if not content or len(content) < 3:
                    i += 1
                    continue
                
                # Quebrar por linhas para processar estruturas
                content_lines = content.split('\n')
                
                for line in content_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Incisos romanos (I, II, III, IV, etc)
                    if re.match(r'^[IVX]+\s*[-–—]', line):
                        lines.append(f"- {line}")
                    # Alíneas (a), b), c))
                    elif re.match(r'^[a-z]\)', line):
                        lines.append(f"  - {line}")
                    # Numeração (1., 2., 3.)
                    elif re.match(r'^\d+\.\s+', line):
                        lines.append(f"  - {line}")
                    # Capítulos e seções (texto em maiúsculas)
                    elif line.isupper() and len(line) < 100 and not re.search(r'\d', line):
                        lines.append("")
                        lines.append(f"#### {line}")
                        lines.append("")
                    # Texto normal
                    else:
                        # Quebrar linhas muito longas por frases
                        if len(line) > 400:
                            sentences = re.split(r'(?<=[.;])\s+', line)
                            for sent in sentences:
                                if sent.strip():
                                    lines.append(sent.strip())
                                    lines.append("")
                        else:
                            lines.append(line)
                
                i += 1
        
        return lines
    
    def _process_html_to_markdown(self, soup: BeautifulSoup) -> List[str]:
        """
        Processa HTML convertendo para Markdown com suporte a tabelas
        
        Args:
            soup: Objeto BeautifulSoup com HTML
            
        Returns:
            Lista de linhas Markdown
        """
        import re
        
        md_lines = []
        current_article = None
        processed_elements = set()  # Controlar elementos já processados
        
        # Processar elementos principais do body
        body = soup.find('body')
        if not body:
            return md_lines
        
        # Iterar por elementos em ordem
        for element in body.descendants:
            # Ignorar elementos não tag
            if not hasattr(element, 'name') or element.name is None:
                continue
            
            # Pular se já foi processado
            if id(element) in processed_elements:
                continue
            
            # Ignorar scripts e styles
            if element.name in ['script', 'style']:
                continue
            
            # Processar tabelas
            if element.name == 'table' and not self._is_inside_table(element):
                table_md = self._table_to_markdown(element)
                if table_md:
                    # É uma tabela real de dados - converter para Markdown
                    md_lines.append("")
                    md_lines.append(table_md)
                    md_lines.append("")
                    
                    # Marcar tabela e todo seu conteúdo como processado
                    for desc in element.descendants:
                        processed_elements.add(id(desc))
                    processed_elements.add(id(element))
                    continue
                else:
                    # É uma tabela de layout - extrair texto diretamente
                    text = element.get_text(separator='\n', strip=False)
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 2:
                            md_lines.append(line)
                    md_lines.append("")
                    
                    # Marcar como processado
                    for desc in element.descendants:
                        processed_elements.add(id(desc))
                    processed_elements.add(id(element))
                    continue
            
            # Processar parágrafos com conteúdo
            if element.name in ['p', 'div'] and not self._has_descendant_table(element):
                # Pular se está dentro de uma tabela (já foi processado)
                if element.find_parent('table'):
                    processed_elements.add(id(element))
                    continue
                
                # Usar get_text preservando as quebras de linha que inserimos dos <br>
                text = element.get_text(separator='\n', strip=False)
                
                # Processar cada linha
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    
                    # Pular vazios ou muito curtos
                    if not line or len(line) < 3:
                        continue
                    
                    # Detectar início de artigo
                    art_match = re.match(r'^(Art\.?\s*\d+[º°]?(?:-[A-Z])?\.?)\s*(.*)', line)
                    if art_match:
                        art_header = art_match.group(1)
                        art_content = art_match.group(2)
                        art_num = re.search(r'\d+[º°]?(?:-[A-Z])?', art_header).group(0)
                        art_id = art_num.replace('º', '').replace('°', '').lower()
                        
                        md_lines.append("")
                        md_lines.append(f"### Artigo {art_num} {{#artigo-{art_id}}}")
                        md_lines.append("")
                        
                        if art_content.strip():
                            md_lines.append(art_content.strip())
                            md_lines.append("")
                        
                        current_article = art_num
                        continue
                    
                    # Detectar parágrafos (§)
                    if re.match(r'^§\s*(?:único|Único|\d+[º°]?)', line, re.IGNORECASE):
                        md_lines.append("")
                        md_lines.append(f"**{line}**")
                        md_lines.append("")
                        continue
                    
                    # Detectar capítulos/seções
                    if re.match(r'^(CAPÍTULO|SEÇÃO|Capítulo|Seção)', line):
                        md_lines.append("")
                        md_lines.append(f"#### {line}")
                        md_lines.append("")
                        continue
                    
                    # Detectar incisos (I, II, III, etc)
                    if re.match(r'^[IVX]+\s*[-–—]', line):
                        md_lines.append(f"- {line}")
                        continue
                    
                    # Detectar alíneas (a), b), c))
                    if re.match(r'^[a-z]\)', line):
                        md_lines.append(f"  - {line}")
                        continue
                    
                    # Texto normal - adicionar cada linha
                    md_lines.append(line)
                
                # Adicionar espaço após o elemento se tiver conteúdo
                if any(l.strip() for l in lines):
                    md_lines.append("")
                
                continue
        
        return md_lines
    
    def _is_inside_table(self, element) -> bool:
        """Verifica se elemento está dentro de uma tabela"""
        parent = element.parent
        while parent:
            if parent.name == 'table':
                return True
            parent = parent.parent
        return False
    
    def _has_descendant_table(self, element) -> bool:
        """Verifica se elemento contém uma tabela"""
        return element.find('table') is not None
    
    def _table_to_markdown(self, table_element) -> str:
        """
        Converte tabela HTML para formato Markdown
        
        Args:
            table_element: Elemento BeautifulSoup da tabela
            
        Returns:
            String com tabela em formato Markdown (vazio se for tabela de layout)
        """
        rows = []
        
        # Extrair todas as linhas
        for tr in table_element.find_all('tr'):
            cells = []
            for cell in tr.find_all(['td', 'th']):
                # Extrair texto da célula
                cell_text = cell.get_text(separator=' ', strip=True)
                # Limpar espaços extras
                cell_text = ' '.join(cell_text.split())
                # Remover pipes que possam quebrar a tabela Markdown
                cell_text = cell_text.replace('|', '\\|')
                cells.append(cell_text)
            
            if cells and any(c.strip() for c in cells):  # Apenas linhas com conteúdo
                rows.append(cells)
        
        if not rows or len(rows) < 1:
            return ""
        
        # DETECTAR TABELAS DE LAYOUT (não converter para Markdown)
        # Tabelas de layout geralmente têm:
        # 1. Poucas linhas (1-2 linhas)
        # 2. Uma coluna vazia ou com imagem
        # 3. Conteúdo que seria melhor como texto simples (cabeçalho, navegação)
        
        if len(rows) <= 2:
            # Verificar se é tabela de cabeçalho/layout
            for row in rows:
                # Se tem célula vazia ou muito curta (imagem, espaço)
                if any(len(cell.strip()) < 5 for cell in row):
                    # É provável que seja tabela de layout - não converter
                    return ""
                
                # Se tem palavras típicas de cabeçalho de documento
                for cell in row:
                    if any(word in cell for word in ['Presidência', 'República', 'Casa Civil', 'Secretaria']):
                        # É cabeçalho do documento - não converter para tabela
                        return ""
        
        # Determinar número de colunas
        max_cols = max(len(row) for row in rows)
        
        # Se a tabela tem dados estruturados (3+ linhas ou 2+ colunas com dados)
        # E não é uma tabela de uma única linha, converter para Markdown
        if len(rows) < 2 or max_cols < 2:
            return ""
        
        # Normalizar número de colunas em todas as linhas
        for row in rows:
            while len(row) < max_cols:
                row.append("")
        
        # Montar tabela Markdown
        md_table = []
        
        # Primeira linha como cabeçalho
        header = rows[0]
        md_table.append("| " + " | ".join(header) + " |")
        md_table.append("| " + " | ".join(["---"] * len(header)) + " |")
        
        # Linhas de dados (se houver mais de uma linha)
        for row in rows[1:]:
            md_table.append("| " + " | ".join(row[:len(header)]) + " |")
        
        return "\n".join(md_table)
    
    def _format_legal_text(self, text: str) -> str:
        """Formata texto legal com parágrafos, incisos e alíneas"""
        import re
        
        lines = text.split('\n')
        formatted = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parágrafos (§)
            if re.match(r'^§\s*\d+[º°]?', line):
                formatted.append(f"\n**{line}**\n")
            # Incisos (I, II, III, etc)
            elif re.match(r'^[IVX]+\s*[-–]', line):
                formatted.append(f"- {line}")
            # Alíneas (a), b), c))
            elif re.match(r'^[a-z]\)', line):
                formatted.append(f"  - {line}")
            # Texto normal
            else:
                formatted.append(line)
        
        return "\n".join(formatted) + "\n"
    
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
