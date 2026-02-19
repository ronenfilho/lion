"""
Structural Chunker - LION
Divide documentos em chunks baseado em estrutura semântica

Suporta múltiplos formatos:
- Markdown (arquivos .md processados)
- PDFSection (seções extraídas de PDF/HTML)

Melhorias implementadas:
- Respeita limites de artigos e parágrafos legais
- Adiciona contexto hierárquico automático
- Mescla chunks pequenos com adjacentes
- Mantém coesão semântica entre chunks
"""

import re
import hashlib
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass


@dataclass
class PDFSection:
    """Representa uma seção extraída do documento"""
    title: str
    content: str
    page_number: int
    level: int
    metadata: Dict[str, any]


@dataclass
class Chunk:
    """Representa um chunk de documento"""
    content: str
    metadata: Dict[str, any]
    chunk_id: str
    source: str
    
    def __len__(self):
        return len(self.content)


class StructuralChunker:
    """
    Divide documentos em chunks baseado em estrutura semântica
    
    Suporta:
    - Markdown: Detecta artigos (### Artigo) e headers (##)
    - PDFSection: Processa seções extraídas de PDF/HTML
    
    Estratégias:
    - Respeita seções e hierarquia do documento
    - Mantém contexto de títulos superiores
    - Evita quebras no meio de artigos/parágrafos
    - Adiciona janela de contexto quando necessário
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        overlap: int = 200,
        add_context_window: bool = True,
        respect_boundaries: bool = True
    ):
        """
        Inicializa o chunker estrutural
        
        Args:
            max_chunk_size: Tamanho máximo do chunk em caracteres
            min_chunk_size: Tamanho mínimo do chunk (chunks menores são mesclados)
            overlap: Overlap entre chunks consecutivos
            add_context_window: Adicionar contexto de seções superiores
            respect_boundaries: Respeitar limites de seções/artigos
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
        self.add_context_window = add_context_window
        self.respect_boundaries = respect_boundaries
    
    def chunk_markdown(
        self,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Divide documento Markdown em chunks preservando estrutura
        
        Args:
            content: Conteúdo do documento Markdown
            source: Nome/identificador da fonte
            metadata: Metadados adicionais
            
        Returns:
            Lista de chunks
        """
        if metadata is None:
            metadata = {}
        
        # Dividir por seções (artigos ou headers)
        sections = self._parse_markdown_sections(content)
        
        chunks = []
        chunk_counter = 0
        
        for section_title, section_content in sections:
            # Se a seção é pequena, manter inteira
            if len(section_content) <= self.max_chunk_size:
                chunk_id = self._generate_chunk_id(source, chunk_counter)
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    content=section_content,
                    source=source,
                    metadata={
                        **metadata,
                        "section": section_title,
                        "chunk_index": chunk_counter,
                        "chunk_method": "markdown_section"
                    }
                ))
                chunk_counter += 1
            else:
                # Dividir seção grande em chunks menores com overlap
                section_chunks = self._split_markdown_section(
                    section_content,
                    section_title,
                    source,
                    chunk_counter,
                    metadata
                )
                chunks.extend(section_chunks)
                chunk_counter += len(section_chunks)
        
        return chunks
    
    def _parse_markdown_sections(self, content: str) -> List[Tuple[str, str]]:
        """
        Divide conteúdo Markdown por seções (artigos ou headers)
        
        Returns:
            Lista de tuplas (título_seção, conteúdo_seção)
        """
        sections = []
        
        # Padrões para detectar seções
        patterns = [
            r'^### Artigo \d+.*?{#artigo-.*?}$',  # Artigos
            r'^##+ .*$',  # Headers H2, H3, etc
        ]
        
        lines = content.split('\n')
        current_section = []
        current_title = "Introdução"
        
        for line in lines:
            # Verificar se é início de nova seção
            is_section_start = any(re.match(pattern, line, re.MULTILINE) for pattern in patterns)
            
            if is_section_start:
                # Salvar seção anterior
                if current_section:
                    section_content = '\n'.join(current_section).strip()
                    if len(section_content) >= self.min_chunk_size:
                        sections.append((current_title, section_content))
                
                # Iniciar nova seção
                current_title = line.strip()
                current_section = [line]
            else:
                current_section.append(line)
        
        # Adicionar última seção
        if current_section:
            section_content = '\n'.join(current_section).strip()
            if len(section_content) >= self.min_chunk_size:
                sections.append((current_title, section_content))
        
        return sections if sections else [("Documento Completo", content)]
    
    def _split_markdown_section(
        self,
        section_content: str,
        section_title: str,
        source: str,
        start_index: int,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Divide seção Markdown grande em chunks com overlap
        
        Returns:
            Lista de chunks da seção
        """
        chunks = []
        paragraphs = section_content.split('\n\n')
        
        current_chunk = []
        current_size = 0
        chunk_index = start_index
        
        for para in paragraphs:
            para_size = len(para)
            
            # Se o parágrafo sozinho já é maior que max_chunk_size
            if para_size > self.max_chunk_size:
                # Salvar chunk atual se houver
                if current_chunk:
                    chunk_content = '\n\n'.join(current_chunk)
                    chunk_id = self._generate_chunk_id(source, chunk_index)
                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        content=chunk_content,
                        source=source,
                        metadata={
                            **metadata,
                            "section": section_title,
                            "chunk_index": chunk_index,
                            "chunk_method": "markdown_split"
                        }
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0
                
                # Dividir parágrafo grande por sentenças
                sentences = re.split(r'(?<=[.!?])\s+', para)
                temp_chunk = []
                temp_size = 0
                
                for sent in sentences:
                    sent_size = len(sent)
                    if temp_size + sent_size > self.max_chunk_size:
                        if temp_chunk:
                            chunk_content = ' '.join(temp_chunk)
                            chunk_id = self._generate_chunk_id(source, chunk_index)
                            chunks.append(Chunk(
                                chunk_id=chunk_id,
                                content=chunk_content,
                                source=source,
                                metadata={
                                    **metadata,
                                    "section": section_title,
                                    "chunk_index": chunk_index,
                                    "chunk_method": "markdown_sentence_split"
                                }
                            ))
                            chunk_index += 1
                            
                            # Overlap: manter últimas sentenças
                            if self.overlap > 0 and len(temp_chunk) > 1:
                                overlap_text = ' '.join(temp_chunk[-2:])
                                if len(overlap_text) <= self.overlap:
                                    temp_chunk = temp_chunk[-2:]
                                    temp_size = len(overlap_text)
                                else:
                                    temp_chunk = []
                                    temp_size = 0
                            else:
                                temp_chunk = []
                                temp_size = 0
                        
                        temp_chunk.append(sent)
                        temp_size += sent_size
                    else:
                        temp_chunk.append(sent)
                        temp_size += sent_size
                
                if temp_chunk:
                    chunk_content = ' '.join(temp_chunk)
                    chunk_id = self._generate_chunk_id(source, chunk_index)
                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        content=chunk_content,
                        source=source,
                        metadata={
                            **metadata,
                            "section": section_title,
                            "chunk_index": chunk_index,
                            "chunk_method": "markdown_sentence_split"
                        }
                    ))
                    chunk_index += 1
            
            # Parágrafo normal
            elif current_size + para_size > self.max_chunk_size:
                if current_chunk:
                    chunk_content = '\n\n'.join(current_chunk)
                    chunk_id = self._generate_chunk_id(source, chunk_index)
                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        content=chunk_content,
                        source=source,
                        metadata={
                            **metadata,
                            "section": section_title,
                            "chunk_index": chunk_index,
                            "chunk_method": "markdown_paragraph"
                        }
                    ))
                    chunk_index += 1
                    
                    # Overlap: manter último parágrafo se couber
                    if self.overlap > 0 and current_chunk:
                        last_para = current_chunk[-1]
                        if len(last_para) <= self.overlap:
                            current_chunk = [last_para, para]
                            current_size = len(last_para) + para_size
                        else:
                            current_chunk = [para]
                            current_size = para_size
                    else:
                        current_chunk = [para]
                        current_size = para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Salvar último chunk
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunk_id = self._generate_chunk_id(source, chunk_index)
            chunks.append(Chunk(
                chunk_id=chunk_id,
                content=chunk_content,
                source=source,
                metadata={
                    **metadata,
                    "section": section_title,
                    "chunk_index": chunk_index,
                    "chunk_method": "markdown_final"
                }
            ))
        
        return chunks
    
    def _generate_chunk_id(self, source: str, index: int) -> str:
        """Gera ID único para o chunk"""
        unique_str = f"{source}_{index}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    
    def chunk_sections(
        self, 
        sections: List[PDFSection],
        source: str = "document"
    ) -> List[Chunk]:
        """
        Divide seções em chunks
        
        Args:
            sections: Lista de seções do documento
            source: Nome/identificador do documento fonte
            
        Returns:
            Lista de chunks
        """
        chunks = []
        
        # Manter contexto hierárquico (títulos de níveis superiores)
        context_stack = []
        
        for section in sections:
            # Atualizar pilha de contexto
            context_stack = self._update_context_stack(
                context_stack, 
                section
            )
            
            # Obter contexto atual
            context = self._build_context(context_stack) if self.add_context_window else ""
            
            # Se a seção cabe em um chunk
            if len(section.content) + len(context) <= self.max_chunk_size:
                chunk = Chunk(
                    content=f"{context}{section.content}".strip(),
                    metadata={
                        "section_title": section.title,
                        "section_level": section.level,
                        "page_number": section.page_number,
                        "type": section.metadata.get("type", "unknown"),
                        "has_context": bool(context)
                    },
                    chunk_id=f"{source}_chunk_{len(chunks)}",
                    source=source
                )
                chunks.append(chunk)
            
            else:
                # Seção grande - dividir mantendo contexto
                section_chunks = self._split_large_section(
                    section, 
                    context,
                    source,
                    len(chunks)
                )
                chunks.extend(section_chunks)
        
        return chunks
    
    def _update_context_stack(
        self, 
        stack: List[PDFSection], 
        current_section: PDFSection
    ) -> List[PDFSection]:
        """
        Atualiza pilha de contexto hierárquico
        
        Args:
            stack: Pilha atual de contexto
            current_section: Seção atual
            
        Returns:
            Pilha atualizada
        """
        # Remover seções de nível igual ou inferior
        while stack and stack[-1].level >= current_section.level:
            stack.pop()
        
        # Adicionar seção atual se for um título importante
        if current_section.level <= 3:  # Apenas níveis 1, 2, 3
            stack.append(current_section)
        
        return stack
    
    def _build_context(self, context_stack: List[PDFSection]) -> str:
        """
        Constrói string de contexto a partir da pilha
        
        Args:
            context_stack: Pilha de contexto
            
        Returns:
            String de contexto formatada
        """
        if not context_stack:
            return ""
        
        # Apenas títulos, não o conteúdo completo
        context_titles = [s.title for s in context_stack[:-1]]  # Excluir último (seção atual)
        
        if context_titles:
            return " > ".join(context_titles) + "\n\n"
        
        return ""
    
    def _split_large_section(
        self,
        section: PDFSection,
        context: str,
        source: str,
        start_index: int
    ) -> List[Chunk]:
        """
        Divide seção grande em múltiplos chunks
        
        Args:
            section: Seção a ser dividida
            context: Contexto hierárquico
            source: Documento fonte
            start_index: Índice inicial para chunk_id
            
        Returns:
            Lista de chunks da seção
        """
        chunks = []
        content = section.content
        
        # Tentar dividir por parágrafos
        paragraphs = content.split('\n\n')
        
        current_chunk_content = []
        current_size = len(context)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # Se adicionar este parágrafo ultrapassa o limite
            if current_size + para_size + 2 > self.max_chunk_size:  # +2 para \n\n
                # Salvar chunk atual se houver conteúdo
                if current_chunk_content:
                    chunk = Chunk(
                        content=f"{context}{'  '.join(current_chunk_content)}".strip(),
                        metadata={
                            "section_title": section.title,
                            "section_level": section.level,
                            "page_number": section.page_number,
                            "type": section.metadata.get("type", "unknown"),
                            "has_context": bool(context),
                            "is_partial": True,
                            "part_number": len(chunks) + 1
                        },
                        chunk_id=f"{source}_chunk_{start_index + len(chunks)}",
                        source=source
                    )
                    chunks.append(chunk)
                
                # Iniciar novo chunk
                current_chunk_content = [para]
                current_size = len(context) + para_size
            else:
                current_chunk_content.append(para)
                current_size += para_size + 2
        
        # Salvar último chunk
        if current_chunk_content:
            chunk = Chunk(
                content=f"{context}\n\n{'  '.join(current_chunk_content)}".strip(),
                metadata={
                    "section_title": section.title,
                    "section_level": section.level,
                    "page_number": section.page_number,
                    "type": section.metadata.get("type", "unknown"),
                    "has_context": bool(context),
                    "is_partial": True,
                    "part_number": len(chunks) + 1
                },
                chunk_id=f"{source}_chunk_{start_index + len(chunks)}",
                source=source
            )
            chunks.append(chunk)
        
        return chunks
    
    def chunk_text(
        self,
        text: str,
        source: str = "document",
        metadata: Optional[Dict] = None
    ) -> List[Chunk]:
        """
        Divide texto simples em chunks respeitando estrutura legal
        
        Args:
            text: Texto a ser dividido
            source: Documento fonte
            metadata: Metadados adicionais
            
        Returns:
            Lista de chunks otimizados
        """
        metadata = metadata or {}
        
        # Dividir por sentenças (ponto final + espaço/quebra)
        sentences = re.split(r'\.\s+', text)
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        current_context = None
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # Detectar início de nova estrutura (CAPÍTULO, Art., §)
            is_structural = self._is_structural_marker(sentence)
            
            # Se ultrapassar o tamanho máximo ou encontrar nova estrutura importante
            if current_size > 0 and (current_size + sentence_size > self.max_chunk_size or 
                                      (is_structural and current_size > self.min_chunk_size)):
                # Salvar chunk atual
                content = ' '.join(current_chunk)
                
                # Adicionar contexto se habilitado
                if self.add_context_window and current_context:
                    content = f"[{current_context}]\n\n{content}"
                
                chunks.append({
                    'content': content,
                    'metadata': metadata,
                    'has_context': bool(current_context)
                })
                
                # Resetar para novo chunk
                current_chunk = [sentence]
                current_size = sentence_size
                
                # Atualizar contexto se for marcador estrutural importante
                if is_structural and any(kw in sentence.upper() for kw in ['CAPÍTULO', 'SEÇÃO', 'ART.']):
                    current_context = self._extract_context(sentence)
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1  # +1 para espaço
        
        # Salvar último chunk
        if current_chunk:
            content = ' '.join(current_chunk)
            if self.add_context_window and current_context:
                content = f"[{current_context}]\n\n{content}"
            
            chunks.append({
                'content': content,
                'metadata': metadata,
                'has_context': bool(current_context)
            })
        
        # Otimizar: mesclar chunks muito pequenos
        optimized_chunks = self._merge_small_chunks(chunks)
        
        # Converter para objetos Chunk
        final_chunks = []
        for i, chunk_data in enumerate(optimized_chunks):
            chunk = Chunk(
                content=chunk_data['content'],
                metadata={
                    **chunk_data.get('metadata', {}),
                    "chunk_method": "legal_structural_v2",
                    "has_context": chunk_data.get('has_context', False)
                },
                chunk_id=f"{source}_chunk_{i}",
                source=source
            )
            final_chunks.append(chunk)
        
        return final_chunks
    
    def _is_structural_marker(self, text: str) -> bool:
        """Verifica se o texto começa com um marcador estrutural"""
        patterns = [
            r'^CAPÍTULO [IVXLCDM]+',
            r'^SEÇÃO [IVXLCDM]+',
            r'^Art\.\s*\d+',
            r'^§\s*\d+',
            r'^[IVXLCDM]+ -',  # Incisos
        ]
        return any(re.match(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _extract_context(self, text: str) -> Optional[str]:
        """Extrai contexto de um marcador estrutural"""
        # Pegar apenas o marcador inicial (não todo o conteúdo)
        match = re.match(r'^((?:CAPÍTULO|SEÇÃO|Art\.)\s+[^\s]+(?:\s+[^\s]+)?)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _merge_small_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Mescla chunks muito pequenos com adjacentes"""
        if not chunks:
            return []
        
        optimized = []
        i = 0
        
        while i < len(chunks):
            current = chunks[i]
            current_size = len(current['content'])
            
            # Se o chunk é muito pequeno (<min_chunk_size)
            if current_size < self.min_chunk_size:
                # Tentar mesclar com próximo
                if i + 1 < len(chunks):
                    next_chunk = chunks[i + 1]
                    next_size = len(next_chunk['content'])
                    
                    # Mesclar se razoável
                    if current_size + next_size <= self.max_chunk_size * 1.5:
                        merged = {
                            'content': f"{current['content']} {next_chunk['content']}",
                            'metadata': current.get('metadata', {}),
                            'has_context': current.get('has_context') or next_chunk.get('has_context')
                        }
                        optimized.append(merged)
                        i += 2
                        continue
                # Se não tem próximo, tentar mesclar com anterior
                elif optimized:
                    last = optimized[-1]
                    last_size = len(last['content'])
                    
                    if last_size + current_size <= self.max_chunk_size * 1.5:
                        last['content'] = f"{last['content']} {current['content']}"
                        last['has_context'] = last.get('has_context') or current.get('has_context')
                        i += 1
                        continue
            
            optimized.append(current)
            i += 1
        
        return optimized


def chunk_document(
    sections: List[PDFSection],
    source: str = "document",
    **kwargs
) -> List[Chunk]:
    """
    Função helper para chunking rápido
    
    Args:
        sections: Seções do documento
        source: Nome do documento
        **kwargs: Argumentos para StructuralChunker
        
    Returns:
        Lista de chunks
    """
    chunker = StructuralChunker(**kwargs)
    return chunker.chunk_sections(sections, source)


if __name__ == "__main__":
    # Teste básico
    from .pdf_extractor import PDFSection
    
    # Criar seções de teste
    test_sections = [
        PDFSection(
            title="CAPÍTULO I - Disposições Gerais",
            content="Este capítulo trata das disposições gerais do regulamento.",
            page_number=1,
            level=1,
            metadata={"type": "chapter"}
        ),
        PDFSection(
            title="Art. 1º",
            content="O Imposto de Renda de Pessoa Física (IRPF) incide sobre os rendimentos auferidos por pessoas físicas residentes no Brasil." * 20,
            page_number=1,
            level=3,
            metadata={"type": "article"}
        ),
        PDFSection(
            title="§ 1º",
            content="Consideram-se residentes as pessoas físicas domiciliadas no Brasil.",
            page_number=1,
            level=4,
            metadata={"type": "paragraph"}
        )
    ]
    
    print("📄 Testando Structural Chunker")
    print("=" * 60)
    
    chunks = chunk_document(test_sections, source="test_doc", max_chunk_size=500)
    
    print(f"\n✅ {len(chunks)} chunks criados\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Tamanho: {len(chunk)} caracteres")
        print(f"  Metadados: {chunk.metadata}")
        print(f"  Preview: {chunk.content[:150]}...")
        print()
