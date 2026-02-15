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
            
            return {
                "metadata": metadata,
                "sections": sections,
                "full_text": full_text,
                "num_pages": len(doc),
                "source": str(pdf_path.name)
            }
        
        finally:
            doc.close()
    
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
