"""
PDF Extractor - LION
Extrai texto de documentos PDF preservando estrutura e metadados
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class PDFSection:
    """Representa uma seção extraída do PDF"""
    title: str
    content: str
    page_number: int
    level: int  # Nível hierárquico (1=título, 2=subtítulo, etc.)
    metadata: Dict[str, any]


class PDFExtractor:
    """
    Extrai texto estruturado de documentos PDF
    
    Funcionalidades:
    - Extração de texto com preservação de estrutura
    - Identificação de seções e hierarquia
    - Extração de metadados do documento
    - Detecção de títulos e subtítulos
    - Limpeza básica de formatação
    """
    
    def __init__(
        self,
        preserve_layout: bool = True,
        extract_images: bool = False,
        min_section_length: int = 50
    ):
        """
        Inicializa o extrator de PDF
        
        Args:
            preserve_layout: Preservar layout original do texto
            extract_images: Extrair imagens (não implementado ainda)
            min_section_length: Tamanho mínimo de seção em caracteres
        """
        self.preserve_layout = preserve_layout
        self.extract_images = extract_images
        self.min_section_length = min_section_length
    
    def extract(self, pdf_path: str) -> Dict[str, any]:
        """
        Extrai conteúdo completo do PDF
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Dict contendo:
                - metadata: Metadados do documento
                - sections: Lista de seções extraídas
                - full_text: Texto completo do documento
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
        
        doc = fitz.open(str(pdf_path))
        
        try:
            # Extrair metadados
            metadata = self._extract_metadata(doc)
            
            # Extrair texto por página
            pages_text = []
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                pages_text.append({
                    "page_number": page_num,
                    "text": text,
                    "bbox": page.rect
                })
            
            # Identificar seções
            sections = self._identify_sections(pages_text)
            
            # Texto completo
            full_text = "\n\n".join([s.content for s in sections])
            
            result = {
                "metadata": metadata,
                "sections": sections,
                "full_text": full_text,
                "num_pages": len(doc),
                "source": str(pdf_path.name)
            }
            
            # Salvar em Markdown
            self._save_to_markdown(pdf_path, result)
            
            return result
        
        finally:
            doc.close()
    
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
        
        # Montar conteúdo Markdown
        md_lines = []
        
        # Cabeçalho do documento
        doc_title = extracted_data.get('metadata', {}).get('title', source_path.stem)
        md_lines.append(f"# {doc_title if doc_title else source_path.stem}")
        md_lines.append("")
        md_lines.append(f"> **Fonte**: {source_path.name}  ")
        md_lines.append(f"> **Processado em**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        if "num_pages" in extracted_data:
            md_lines.append(f"> **Páginas**: {extracted_data['num_pages']}")
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
        
        # Conteúdo estruturado por artigos
        md_lines.append("## 📖 Texto Completo")
        md_lines.append("")
        
        # Dividir texto em artigos usando regex mais robusto
        article_pattern = r'(Art\.?\s*\d+[º°]?(?:-[A-Z])?\.?)'
        parts = re.split(article_pattern, full_text)
        
        # Pré-processar: juntar artigo com seu conteúdo
        structured_parts = []
        i = 0
        while i < len(parts):
            if i < len(parts) - 1 and re.match(r'^Art\.?\s*\d+', parts[i]):
                structured_parts.append({
                    'header': parts[i],
                    'content': parts[i + 1] if i + 1 < len(parts) else ''
                })
                i += 2
            else:
                if parts[i].strip():
                    structured_parts.append({
                        'header': None,
                        'content': parts[i]
                    })
                i += 1
        
        # Renderizar partes estruturadas
        for part in structured_parts:
            if part['header']:
                # É um artigo
                art_match = re.search(r'Art\.?\s*(\d+[º°]?(?:-[A-Z])?)', part['header'])
                if art_match:
                    art_num = art_match.group(1)
                    art_id = art_num.replace('º', '').replace('°', '').lower()
                    
                    md_lines.append(f"### Artigo {art_num} {{#artigo-{art_id}}}")
                    md_lines.append("")
                    
                    # Processar conteúdo do artigo
                    content = part['content'].strip()
                    if content:
                        formatted_content = self._format_article_content(content)
                        md_lines.extend(formatted_content)
                    
                    md_lines.append("")
            else:
                # Texto sem artigo (introdução, etc)
                content = part['content'].strip()
                if content and len(content) > 20:  # Evitar fragmentos pequenos
                    md_lines.append(content)
                    md_lines.append("")
        
        # Rodapé
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
    
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, str]:
        """
        Extrai metadados do documento PDF
        
        Args:
            doc: Documento PyMuPDF
            
        Returns:
            Dict com metadados
        """
        metadata = doc.metadata or {}
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "num_pages": len(doc)
        }
    
    def _identify_sections(self, pages_text: List[Dict]) -> List[PDFSection]:
        """
        Identifica seções no documento baseado em padrões de formatação
        
        Para documentos IRPF, identifica:
        - Artigos (Art. 1º, Art. 2º, etc.)
        - Capítulos (CAPÍTULO I, II, etc.)
        - Seções (Seção I, II, etc.)
        - Parágrafos (§ 1º, § 2º, etc.)
        
        Args:
            pages_text: Lista de páginas com texto
            
        Returns:
            Lista de seções identificadas
        """
        sections = []
        current_section = None
        current_content = []
        
        for page_data in pages_text:
            page_num = page_data["page_number"]
            text = page_data["text"]
            
            # Dividir em linhas
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detectar título de seção
                section_match = self._match_section_header(line)
                
                if section_match:
                    # Salvar seção anterior
                    if current_section and current_content:
                        current_section.content = "\n".join(current_content).strip()
                        if len(current_section.content) >= self.min_section_length:
                            sections.append(current_section)
                    
                    # Nova seção
                    current_section = PDFSection(
                        title=section_match["title"],
                        content="",
                        page_number=page_num,
                        level=section_match["level"],
                        metadata={"type": section_match["type"]}
                    )
                    current_content = []
                else:
                    # Adicionar ao conteúdo da seção atual
                    current_content.append(line)
        
        # Salvar última seção
        if current_section and current_content:
            current_section.content = "\n".join(current_content).strip()
            if len(current_section.content) >= self.min_section_length:
                sections.append(current_section)
        
        # Se não encontrou seções, criar uma única seção com todo o conteúdo
        if not sections:
            full_text = "\n".join([p["text"] for p in pages_text]).strip()
            sections.append(PDFSection(
                title="Documento Completo",
                content=full_text,
                page_number=1,
                level=1,
                metadata={"type": "full_document"}
            ))
        
        return sections
    
    def _match_section_header(self, line: str) -> Optional[Dict]:
        """
        Identifica se uma linha é um cabeçalho de seção
        
        Padrões para documentos legais brasileiros:
        - CAPÍTULO I, CAPÍTULO II, etc.
        - SEÇÃO I, SEÇÃO II, etc.
        - Art. 1º, Art. 2º, etc.
        - § 1º, § 2º, etc.
        
        Args:
            line: Linha de texto
            
        Returns:
            Dict com informações da seção ou None
        """
        line_upper = line.upper()
        
        # CAPÍTULO
        if re.match(r'^CAP[ÍI]TULO\s+[IVXLCDM]+', line_upper):
            return {
                "title": line,
                "level": 1,
                "type": "chapter"
            }
        
        # SEÇÃO
        if re.match(r'^SE[ÇC][ÃA]O\s+[IVXLCDM]+', line_upper):
            return {
                "title": line,
                "level": 2,
                "type": "section"
            }
        
        # ARTIGO
        if re.match(r'^ART\.?\s+\d+', line_upper):
            return {
                "title": line,
                "level": 3,
                "type": "article"
            }
        
        # PARÁGRAFO
        if re.match(r'^§\s*\d+', line):
            return {
                "title": line,
                "level": 4,
                "type": "paragraph"
            }
        
        # Títulos em MAIÚSCULAS (linhas curtas e todas em maiúsculas)
        if (len(line) < 100 and 
            line.isupper() and 
            not line.startswith('ART') and
            not line.startswith('§')):
            return {
                "title": line,
                "level": 2,
                "type": "title"
            }
        
        return None
    
    def extract_text_by_page(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Extrai texto página por página
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Lista de dicionários com texto por página
        """
        pdf_path = Path(pdf_path)
        doc = fitz.open(str(pdf_path))
        
        try:
            pages = []
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                pages.append({
                    "page_number": page_num,
                    "text": text.strip(),
                    "char_count": len(text)
                })
            
            return pages
        
        finally:
            doc.close()


def extract_pdf(pdf_path: str, **kwargs) -> Dict[str, any]:
    """
    Função helper para extração rápida de PDF
    
    Args:
        pdf_path: Caminho para o PDF
        **kwargs: Argumentos adicionais para PDFExtractor
        
    Returns:
        Dict com conteúdo extraído
    """
    extractor = PDFExtractor(**kwargs)
    return extractor.extract(pdf_path)


if __name__ == "__main__":
    # Teste básico
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python pdf_extractor.py <caminho_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print(f"📄 Extraindo PDF: {pdf_path}")
    print("=" * 60)
    
    result = extract_pdf(pdf_path)
    
    print(f"✅ Metadados:")
    for key, value in result["metadata"].items():
        if value:
            print(f"   {key}: {value}")
    
    print(f"\n📊 Estatísticas:")
    print(f"   Páginas: {result['num_pages']}")
    print(f"   Seções: {len(result['sections'])}")
    print(f"   Caracteres: {len(result['full_text'])}")
    
    print(f"\n📑 Seções encontradas:")
    for i, section in enumerate(result["sections"][:5], 1):
        print(f"   {i}. {section.title} (pág. {section.page_number}, nível {section.level})")
        print(f"      Preview: {section.content[:100]}...")
    
    if len(result["sections"]) > 5:
        print(f"   ... e mais {len(result['sections']) - 5} seções")
