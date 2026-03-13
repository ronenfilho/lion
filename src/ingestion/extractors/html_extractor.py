"""
HTMLExtractor - LION
Extrai texto estruturado de documentos HTML de legislação brasileira.

Suporta dois padrões de fonte identificados na análise:

  1. Padrão Planalto / Câmara dos Deputados
     Arquivos: D9580.html, L15270.html, L9250compilado.html, L7713compilada.html
     Característica: Rich CSS classes semânticas (.Livro, .Titulo, .Capitulo,
                     .Secao, .Subsecao, .Artigo, .Artart, .04ParteNormativa...)
     Estratégia: mapeamento direto CSS class → nível Markdown hierárquico

  2. Padrão RFB / Normas.RFB (Angular SPA com SSR parcial)
     Arquivos: IN RFB nº *.html
     Característica: <app-root> com <div class="segmento"> por artigo/capítulo,
                     encoding cp1252 com mojibake visível ao ler como utf-8
     Estratégia: extrair div.conteudo-ato → div.segmento, aplicar heurísticas
                 de regex para detectar CAPÍTULO / Art. / § / incisos

Herda de BaseExtractor (encoding, mojibake, heurísticas, save_to_markdown).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, NavigableString, Tag

from .base_extractor import BaseExtractor


# ---------------------------------------------------------------------------
# Dataclass de seção
# ---------------------------------------------------------------------------

@dataclass
class HTMLSection:
    """Representa uma seção extraída do HTML."""
    title: str
    content: str
    level: int           # 1=H1/Livro ... 6=Artigo; 0=body text sem título
    tag_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mapeamento CSS → hierarquia Markdown  (Padrão Planalto)
# ---------------------------------------------------------------------------

# Cada entrada: (nome_css, nível_hierárquico, marcador_md, tipo)
# tipo: 'heading' | 'article' | 'body' | 'blockquote'
PLANALTO_CSS_MAP: List[Tuple[str, int, str, str]] = [
    ("Livro",             1,  "# ",       "heading"),
    ("Titulo",            2,  "## ",      "heading"),
    ("Subtitulo",         2,  "## ",      "heading"),
    ("Parte",             2,  "## ",      "heading"),
    ("04ParteNormativa",  3,  "### ",     "article"),
    ("16ParteNormativa",  3,  "### ",     "article"),
    ("Capitulo",          3,  "### ",     "heading"),
    ("Cap",               3,  "### ",     "heading"),
    ("Secao",             4,  "#### ",    "heading"),
    ("Subsecao",          5,  "##### ",   "heading"),
    ("TpicodeSeo",        5,  "##### ",   "heading"),
    ("Artigo",            6,  "###### ",  "article"),
    ("Artart",            6,  "###### ",  "article"),
    ("06Alterao",         6,  "###### ",  "article"),
    ("06CitaoPN",         0,  "> ",       "blockquote"),
    ("CitacaoPN",         0,  "> ",       "blockquote"),
    ("MsoNormal",         0,  "",         "body"),
    ("texto1",            0,  "",         "body"),
    ("texto2",            0,  "",         "body"),
]

# Lookup: classe_css_lower → (nivel, marcador, tipo)
_PLANALTO_LOOKUP: Dict[str, Tuple[int, str, str]] = {
    cls.lower(): (lvl, marker, tipo)
    for cls, lvl, marker, tipo in PLANALTO_CSS_MAP
}


def _lookup_css(classes: List[str]) -> Optional[Tuple[int, str, str]]:
    """Retorna mapeamento para a primeira classe CSS reconhecida."""
    for cls in classes:
        key = cls.lower().strip()
        if key in _PLANALTO_LOOKUP:
            return _PLANALTO_LOOKUP[key]
    return None


# ---------------------------------------------------------------------------
# Extrator principal
# ---------------------------------------------------------------------------

class HTMLExtractor(BaseExtractor):
    """
    Extrai texto estruturado de documentos HTML de legislação brasileira.

    Detecta automaticamente o padrão do documento (Planalto ou RFB SPA)
    e aplica a estratégia de extração adequada.

    Uso rápido:
        extractor = HTMLExtractor()
        result = extractor.extract("data/raw/legislation/D9580.html")
        # Arquivo .md salvo automaticamente em data/raw/legislation/
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        min_text_length: int = 3,
        auto_save: bool = True,
    ):
        self.output_dir = output_dir or Path("data/processed/markdown/legislation")
        self.min_text_length = min_text_length
        self.auto_save = auto_save

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extrai conteúdo estruturado do arquivo HTML.

        Returns:
            {
                "metadata": {...},
                "sections": List[HTMLSection],
                "full_text": str,
                "source": str,
                "pattern": "planalto" | "rfb_spa" | "generic"
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"HTML não encontrado: {path}")

        raw = self._read_with_encoding(path)
        encoding_used = self._detect_encoding(path)

        if _has_mojibake(raw):
            raw = self._fix_mojibake(raw)

        soup = BeautifulSoup(raw, "html.parser")

        for tag in soup.find_all(["script", "style", "noscript"]):
            tag.decompose()

        pattern = _detect_pattern(soup)

        metadata = self._extract_metadata(soup, path, pattern)
        metadata["encoding_detected"] = encoding_used
        metadata["pattern"] = pattern

        if pattern == "planalto":
            sections = self._extract_planalto(soup)
        elif pattern == "rfb_spa":
            sections = self._extract_rfb_spa(soup)
        else:
            sections = self._extract_generic(soup)

        full_text = "\n\n".join(
            s.content for s in sections if s.content.strip()
        )

        result: Dict[str, Any] = {
            "metadata": metadata,
            "sections": sections,
            "full_text": full_text,
            "source": path.name,
            "pattern": pattern,
        }

        if self.auto_save:
            self.save_to_markdown(path, result, self.output_dir)

        return result

    # ------------------------------------------------------------------
    # Padrão Planalto
    # ------------------------------------------------------------------

    def _extract_planalto(self, soup: BeautifulSoup) -> List[HTMLSection]:
        body = soup.find("body") or soup
        sections: List[HTMLSection] = []
        current_section: Optional[HTMLSection] = None
        content_buffer: List[str] = []

        def _flush():
            nonlocal current_section, content_buffer
            if current_section is not None:
                current_section.content = "\n".join(content_buffer).strip()
                sections.append(current_section)
            current_section = None
            content_buffer = []

        # Processar elementos em ordem: parágrafos, headings, E tabelas
        processed_elements = set()
        for el in body.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "table"]):
            if el in processed_elements:
                continue
            
            # Pular tabelas aninhadas
            if el.find_parent("table"):
                continue
            
            # Processar tabelas
            if el.name == "table":
                table_md = _table_to_markdown(el)
                if table_md:
                    # Adicionar a tabela ao buffer de conteúdo da seção atual
                    if content_buffer:
                        content_buffer.append("")  # linha vazia
                    content_buffer.append(table_md)
                processed_elements.add(el)
                continue

            # Processar parágrafos e headings
            text = _get_element_text(el)
            if not text or len(text) < self.min_text_length:
                continue

            # ── Prioridade máxima: detectar títulos estruturais especiais ────
            # ANEXO e REGULAMENTO devem ser seções de nível 2, independente de CSS
            if re.match(r"^\s*ANEXO\s*$", text, re.I):
                _flush()
                current_section = HTMLSection(title=text, content="", level=2, tag_name=el.name)
                content_buffer = []
                processed_elements.add(el)
                continue
            
            if re.match(r"^\s*REGULAMENTO\s+(DO\s+|DA\s+)?IMPOSTO", text, re.I):
                _flush()
                current_section = HTMLSection(title=text, content="", level=2, tag_name=el.name)
                content_buffer = []
                processed_elements.add(el)
                continue
            
            # LIVRO, TÍTULO, CAPÍTULO estruturais (podem vir com CSS incorreto)
            if re.match(r"^\s*LIVRO\s+[IVXLCDM]+\s*$", text, re.I):
                _flush()
                current_section = HTMLSection(title=text, content="", level=1, tag_name=el.name)
                content_buffer = []
                processed_elements.add(el)
                continue
            
            if re.match(r"^\s*TÍTULO\s+[IVXLCDM]+\s*$", text, re.I):
                _flush()
                current_section = HTMLSection(title=text, content="", level=2, tag_name=el.name)
                content_buffer = []
                processed_elements.add(el)
                continue

            classes = el.get("class", [])
            mapping = _lookup_css(classes) if classes else None

            # ── Sobrescrever mapping se texto começar com "Art." ─────────────
            # Artigos podem ter classes incorretas (MsoNormal, 04ParteNormativa)
            # mas devem SEMPRE criar uma seção de artigo
            if _is_article_start(text):
                mapping = (3, "### ", "article")  # Nível 3 para artigos do preâmbulo

            if mapping is None and el.name in ("h1","h2","h3","h4","h5","h6"):
                lvl = int(el.name[1])
                mapping = (lvl, "#" * lvl + " ", "heading")

            # Parágrafos sem classe CSS ou com MsoNormal: aplicar heurística de artigo/parágrafo/inciso
            if mapping is None or (mapping and mapping[0] == 0 and mapping[2] == "body"):
                if _is_article_start(text):
                    mapping = (6, "###### ", "article")
                elif re.match(r"^\s*§\s*(?:único|Único|\d+[º°]?)", text, re.I):
                    mapping = (0, "", "body")  # parágrafo → formato negrito via _format_legal_line
                elif re.match(r"^\s*[IVX]+\s*[-–]", text):
                    mapping = (0, "", "body")  # inciso
                elif re.match(r"^\s*[a-z]\)", text):
                    mapping = (0, "", "body")  # alínea
                elif re.match(r"^\s*LIVRO\s+", text, re.I):
                    mapping = (1, "# ", "heading")
                elif re.match(r"^\s*T[ÍI]TULO\s+", text, re.I):
                    mapping = (2, "## ", "heading")
                elif re.match(r"^\s*CAP[IÍ]TULO\s+", text, re.I):
                    mapping = (3, "### ", "heading")
                elif re.match(r"^\s*SE[ÇC][ÃA]O\s+", text, re.I):
                    mapping = (4, "#### ", "heading")
                elif re.match(r"^\s*SUBSE[ÇC][ÃA]O\s+", text, re.I):
                    mapping = (5, "##### ", "heading")
                # Textos curtos que começam com maiúscula (possíveis títulos descritivos/subtítulos)
                # Não devem ter marcadores típicos de conteúdo de artigo OU estruturas principais
                # Também não devem ser números romanos seguidos de hífen (incisos)
                elif len(text) < 100 and text and text[0].isupper() and \
                     not any(pattern in text.lower() for pattern in ['§', 'art.', 'lei nº', 'decreto', 'inciso', 'alínea']) and \
                     not re.match(r"^\s*(LIVRO|TÍTULO|CAPÍTULO|SE[ÇC][ÃA]O|SUBSE[ÇC][ÃA]O|[IVXLCDM]+\s*[-–])\s+", text, re.I):
                    mapping = (5, "##### ", "heading")  # Nível 5 = TpicodeSeo (subtítulo)
                elif mapping is None:
                    mapping = (0, "", "body")

            level, marker, tipo = mapping

            if tipo == "heading":
                _flush()
                current_section = HTMLSection(title=text, content="", level=level, tag_name=el.name)
                content_buffer = []

            elif tipo == "article":
                if _is_article_start(text):
                    _flush()
                    art_title, art_body = _split_article_head(text)
                    current_section = HTMLSection(
                        title=art_title, content="", level=level, tag_name=el.name,
                        metadata={"type": "artigo"},
                    )
                    content_buffer = []
                    if art_body:
                        content_buffer.append(art_body)
                else:
                    if current_section is None:
                        current_section = HTMLSection(title="", content="", level=0)
                    content_buffer.append(_format_legal_line(text))

            elif tipo == "blockquote":
                if current_section is None:
                    current_section = HTMLSection(title="", content="", level=0)
                content_buffer.append(f"> {text}")

            else:
                if current_section is None:
                    current_section = HTMLSection(title="", content="", level=0)
                content_buffer.append(_format_legal_line(text))

            processed_elements.add(el)

        _flush()

        # Tabelas já foram processadas na iteração principal


        # ── Pós-processamento: combinar títulos consecutivos específicos ─────
        # Combinar apenas padrões conhecidos da legislação brasileira:
        # 1. "ANEXO" + "REGULAMENTO..."
        # 2. "LIVRO X" + "DA/DO/DAS..."
        # 3. "TÍTULO X" + "DA/DO/DAS..."
        # 4. "CAPÍTULO X" + texto descritivo
        # 5. "Seção X" + texto descritivo
        # 6. "Subseção X" + texto descritivo
        combined_sections: List[HTMLSection] = []
        i = 0
        while i < len(sections):
            current = sections[i]
            
            # Continuar combinando elementos consecutivos
            combined_count = 0
            while current.title and not current.content.strip() and (i + 1 + combined_count) < len(sections):
                next_sec = sections[i + 1 + combined_count]
                
                # A próxima deve ter título
                if not next_sec.title:
                    break
                    
                current_title_upper = current.title.upper().strip()
                next_title_upper = next_sec.title.upper().strip()
                
                should_combine = False
                
                # ANEXO + REGULAMENTO
                if current_title_upper == "ANEXO" and "REGULAMENTO" in next_title_upper:
                    should_combine = True
                
                # LIVRO X + DA/DO/DAS... (ambas vazias)
                elif not next_sec.content.strip() and \
                     re.match(r"LIVRO\s+[IVXLCDM]+$", current_title_upper) and \
                     re.match(r"^(DA|DO|DAS|DOS)\s+", next_title_upper):
                    should_combine = True
                
                # TÍTULO X + DA/DO/DAS... (ambas vazias)
                elif not next_sec.content.strip() and \
                     re.match(r"TÍTULO\s+[IVXLCDM]+$", current_title_upper) and \
                     re.match(r"^(DA|DO|DAS|DOS)\s+", next_title_upper):
                    should_combine = True
                
                # CAPÍTULO X + texto descritivo (começando com DA/DO/DAS/DOS ou não artigo)
                elif not next_sec.content.strip() and \
                     re.match(r"CAPÍTULO\s+[IVXLCDM0-9]+$", current_title_upper) and \
                     (re.match(r"^(DA|DO|DAS|DOS)\s+", next_title_upper) or not re.match(r"^ART\.", next_title_upper)):
                    should_combine = True
                
                # Seção X + texto descritivo (ambas vazias, não artigo)
                elif not next_sec.content.strip() and \
                     re.match(r"SE[ÇC][ÃA]O\s+[IVXLCDM0-9]+$", current_title_upper, re.I) and \
                     not re.match(r"^ART\.", next_title_upper):
                    should_combine = True
                
                # Subseção X/única + texto descritivo (ambas vazias, não artigo)
                elif not next_sec.content.strip() and \
                     re.match(r"SUBSE[ÇC][ÃA]O\s+(ÚNICA|[IVXLCDM0-9]+)$", current_title_upper, re.I) and \
                     not re.match(r"^ART\.", next_title_upper):
                    should_combine = True
                
                # Título já combinado + mais texto descritivo (só combinar se começar com DA/DO/DAS/DOS)
                # Não combinar textos curtos que devem ser subtítulos separados
                elif not next_sec.content.strip() and \
                     (" - " in current.title or "\n" in current.title) and \
                     not re.match(r"^(LIVRO|TÍTULO|CAPÍTULO|SE[ÇC][ÃA]O|SUBSE[ÇC][ÃA]O|ART\.)", next_title_upper, re.I) and \
                     re.match(r"^(DA|DO|DAS|DOS)\s+", next_title_upper):
                    should_combine = True
                
                if should_combine:
                    # Combinar os títulos
                    if " - " in current.title:
                        # Já tem hífen, adicionar mais texto
                        combined_title = f"{current.title}\n{next_sec.title}"
                    else:
                        combined_title = f"{current.title} - {next_sec.title}"
                    
                    current = HTMLSection(
                        title=combined_title,
                        content=next_sec.content,  # Pegar conteúdo da segunda (pode estar vazio ou não)
                        level=current.level,  # Preservar nível da estrutura principal (não usar max)
                        tag_name=current.tag_name,
                        metadata=current.metadata,
                    )
                    combined_count += 1
                else:
                    break
            
            # Adicionar a seção (combinada ou não)
            combined_sections.append(current)
            i += 1 + combined_count

        return combined_sections

    # ------------------------------------------------------------------
    # Padrão RFB SPA
    # ------------------------------------------------------------------

    def _extract_rfb_spa(self, soup: BeautifulSoup) -> List[HTMLSection]:
        app_root = soup.find("app-root")
        if not app_root:
            return self._extract_generic(soup)

        sections: List[HTMLSection] = []

        epigrafe = app_root.find(class_="epigrafe-ato")
        if epigrafe:
            text = _get_element_text(epigrafe)
            if text:
                sections.append(HTMLSection(title=text, content="", level=1, tag_name="div",
                                             metadata={"type": "epigrafe"}))

        ementa = app_root.find(class_="caixinha-ementa") or app_root.find(class_="area-ementa-ato")
        if ementa:
            text = _get_element_text(ementa)
            if text:
                sections.append(HTMLSection(title="Ementa", content=text, level=2, tag_name="div",
                                             metadata={"type": "ementa"}))

        conteudo = app_root.find(class_="conteudo-ato") or app_root

        current_section: Optional[HTMLSection] = None
        content_buffer: List[str] = []

        def _flush_rfb():
            nonlocal current_section, content_buffer
            if current_section is not None:
                current_section.content = "\n".join(content_buffer).strip()
                sections.append(current_section)
            current_section = None
            content_buffer = []

        for seg in conteudo.find_all("div", class_="segmento"):
            span = seg.find(class_="conteudo-segmento-ato")
            if span is None:
                span = seg
            text = _get_element_text(span)
            if not text or len(text) < self.min_text_length:
                continue

            heading_level = _classify_rfb_segment(text)
            if heading_level is not None:
                _flush_rfb()
                current_section = HTMLSection(title=text, content="", level=heading_level, tag_name="div")
                content_buffer = []
            else:
                if current_section is None:
                    current_section = HTMLSection(title="", content="", level=0)
                content_buffer.append(_format_legal_line(text))

        _flush_rfb()
        return sections

    # ------------------------------------------------------------------
    # Genérico (fallback)
    # ------------------------------------------------------------------

    def _extract_generic(self, soup: BeautifulSoup) -> List[HTMLSection]:
        body = soup.find("body") or soup
        sections: List[HTMLSection] = []
        current_section: Optional[HTMLSection] = None
        content_buffer: List[str] = []

        def _flush_g():
            nonlocal current_section, content_buffer
            if current_section is not None:
                processed = self._apply_legal_heuristics(content_buffer)
                current_section.content = "\n".join(processed).strip()
                sections.append(current_section)
            current_section = None
            content_buffer = []

        for el in body.descendants:
            if not hasattr(el, "name") or el.name is None:
                continue
            if el.name in ("script", "style"):
                continue
            if el.name in ("h1","h2","h3","h4","h5","h6"):
                _flush_g()
                text = el.get_text(strip=True)
                lvl = int(el.name[1])
                current_section = HTMLSection(title=text, content="", level=lvl, tag_name=el.name)
                content_buffer = []
            elif el.name == "p":
                text = _get_element_text(el)
                if text and len(text) >= self.min_text_length:
                    if current_section is None:
                        current_section = HTMLSection(title="", content="", level=0)
                    content_buffer.append(text)

        _flush_g()
        return sections

    # ------------------------------------------------------------------
    # Metadados
    # ------------------------------------------------------------------

    def _extract_metadata(self, soup: BeautifulSoup, path: Path, pattern: str) -> Dict[str, str]:
        meta: Dict[str, str] = {}
        title_tag = soup.find("title")
        meta["title"] = title_tag.get_text(strip=True) if title_tag else ""

        for m in soup.find_all("meta"):
            name = m.get("name") or m.get("property", "")
            content = m.get("content", "")
            if name and content:
                meta[name] = content

        if pattern == "rfb_spa" and not meta.get("title"):
            epigrafe = soup.find(class_="epigrafe-ato")
            if epigrafe:
                meta["title"] = _get_element_text(epigrafe)

        if not meta.get("title"):
            h1 = soup.find("h1")
            if h1:
                meta["title"] = h1.get_text(strip=True)

        if not meta.get("title"):
            meta["title"] = path.stem

        return meta

    # ------------------------------------------------------------------
    # Esquema hierárquico customizado
    # ------------------------------------------------------------------

    def _build_esquema(
        self,
        sections: List[HTMLSection],
        full_text: str,
        max_entries: int = None,  # None = sem limite
        doc_title: str = "",  # Título do documento
    ) -> List[str]:
        """
        Constrói o Esquema hierárquico da legislação.
        
        IMPORTANTE: Mostra APENAS os TÍTULOS das seções (headings),
        SEM incluir o conteúdo dos artigos (parágrafos, incisos, alíneas).
        Esses elementos devem aparecer apenas no corpo do documento.
        """
        # ── Detectar contexto estrutural ────────────────────────────────────
        has_preamble = False
        has_anexo = False
        first_structural_idx = -1

        for i, sec in enumerate(sections):
            # Detectar se há artigos antes da estrutura principal
            if sec.level == 0 or (sec.level == 3 and re.match(r"Art\.?\s*\d+(?:\.\d{3})*", sec.title, re.I)):
                if first_structural_idx == -1:  # Ainda não encontrou estrutura principal
                    has_preamble = True
            # Encontrar onde começa a estrutura principal
            if re.match(r"ANEXO.*REGULAMENTO|REGULAMENTO", sec.title, re.I):
                has_anexo = True
                if first_structural_idx == -1:
                    first_structural_idx = i
                break
            if sec.level == 1 or (sec.level == 2 and re.match(r"(LIVRO|TÍTULO)", sec.title, re.I)):
                if first_structural_idx == -1:
                    first_structural_idx = i
                break

        # ── Construir lista de headings remapeados (APENAS TÍTULOS) ─────────
        headings: List[Tuple[int, str]] = []

        # ── Adicionar título do documento no início (nível 1) ───────────────
        if doc_title:
            headings.append((1, doc_title))

        for idx, sec in enumerate(sections):
            raw_level = sec.level
            title = sec.title.strip()

            if not title:
                continue

            # Limpar título
            clean_title = re.sub(r"\s*\{#[^}]+\}", "", title).strip()
            clean_title = re.sub(r"\s*\((?:Incluído|Redação|Revogado|Acrescido)[^)]*\)", "", clean_title, flags=re.I).strip()
            clean_title = re.sub(r"\s+Produção de efeitos.*$", "", clean_title).strip()
            
            # ── Verificar se é artigo ANTES de truncar ────────
            is_article = _is_article_start(clean_title)
            
            # ── Para artigos REAIS, manter apenas "Art. Xº" sem o conteúdo ────────
            if is_article:
                art_match = re.match(r"(Art\.?\s*\d+(?:\.\d{3})*[º°]?(?:-[A-Z])?)\s*.*", clean_title, re.I)
                if art_match:
                    clean_title = art_match.group(1)
            # Não truncar títulos estruturais importantes
            elif len(clean_title) > 100 and not re.match(r"^(LIVRO|TÍTULO|CAPÍTULO|SE[ÇC][ÃA]O|SUBSE[ÇC][ÃA]O)\s+", clean_title, re.I):
                clean_title = clean_title[:97] + "…"

            # ── Remapear níveis (mesma lógica do save_to_markdown) ──────────
            md_level = 0
            is_anexo = bool(re.match(r"ANEXO.*REGULAMENTO|REGULAMENTO", clean_title, re.I))

            # Preâmbulo: artigos ANTES do first_structural_idx
            if first_structural_idx > 0 and idx < first_structural_idx and is_article:
                md_level = 7  # Artigos sempre nível 7 (lista indentada)

            # ANEXO
            elif is_anexo:
                md_level = 2

            # Pós-anexo: hierarquia LC 95/98
            elif first_structural_idx >= 0 and idx >= first_structural_idx:
                if raw_level == 1:  # Livro
                    md_level = 3
                elif raw_level == 2:  # Título
                    md_level = 4
                elif raw_level == 3:  # Capítulo / Artigo RIR
                    if is_article:
                        md_level = 7  # Artigos #######
                    else:
                        md_level = 5  # Capítulos #####
                elif raw_level == 4:  # Seção
                    md_level = 6
                elif raw_level == 5:  # Subseção / TpicodeSeo
                    # TpicodeSeo sempre é nível 7 (subtítulo ou Subseção)
                    md_level = 7
                elif raw_level == 6:  # Artigo
                    # Apenas se for realmente um artigo (não uma referência legislativa)
                    if is_article:
                        md_level = 7
                    else:
                        md_level = 0  # Referência legislativa não entra no esquema
                else:
                    md_level = raw_level

            # Artigos em documentos sem hierarquia estrutural → sempre lista (nível 7)
            elif is_article:
                md_level = 7

            else:
                md_level = raw_level

            if md_level > 0:
                headings.append((md_level, clean_title))

        if not headings:
            return []

        # ── Montar linhas Markdown ───────────────────────────────────────────
        out: List[str] = []
        out += ["<details>", "<summary>📋 Esquema da Legislação</summary>", ""]

        for lvl, title in headings:
            # Detectar se é artigo REAL (não referência legislativa)
            is_article_heading = _is_article_start(title)
            is_subsecao = bool(re.match(r"^SUBSE[ÇC][ÃA]O\s+", title, re.I))
            
            if lvl <= 6:
                hashes = "#" * lvl
                out.append(f"{hashes} {title}")
            elif lvl == 7:
                # Artigos: sempre com indentação de 2 espaços
                if is_article_heading:
                    out.append(f"  * {title}")
                # Subseções com negrito
                elif is_subsecao:
                    out.append(f"* **{title}**")
                # Outros (subtítulos TpicodeSeo) sem negrito
                else:
                    out.append(f"* {title}")
            elif lvl == 8:
                out.append(f"  - {title}")
            elif lvl == 9:
                out.append(f"    - {title}")
            else:  # lvl >= 10
                indent = "  " * (lvl - 8)
                out.append(f"{indent}- {title}")

        out += ["", "</details>", "", "---", ""]
        return out

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    def save_to_markdown(
        self,
        source_path: Path,
        result: Dict[str, Any],
        output_dir: Optional[Path] = None,
        suffix: str = "_processed",
    ) -> Path:
        from datetime import datetime

        if output_dir is None:
            output_dir = self.output_dir or Path("data/processed/markdown/legislation")
        output_dir.mkdir(parents=True, exist_ok=True)

        md_path = output_dir / f"{source_path.stem}{suffix}.md"
        metadata = result.get("metadata", {})
        sections: List[HTMLSection] = result.get("sections", [])
        full_text = result.get("full_text", "")
        pattern = result.get("pattern", "generic")

        lines: List[str] = []
        title = metadata.get("title") or source_path.stem
        
        # ── Tentar extrair título real do decreto da primeira seção L0 ──────
        if sections and sections[0].level == 0 and sections[0].content:
            first_line = sections[0].content.split('\n')[0].strip()
            # Se parece com título de decreto/lei, usar
            if re.match(r"^(DECRETO|LEI|INSTRUÇÃO NORMATIVA|PORTARIA|RESOLUÇÃO)", first_line, re.I):
                title = first_line
        
        lines += [f"# {title}", ""]

        lines += [
            "<details>",
            "<summary>📋 Metadados do Documento</summary>",
            "",
            f"- **Arquivo**: `{source_path.name}`",
            f"- **Padrão detectado**: {pattern}",
            f"- **Processado em**: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ]
        for key, value in metadata.items():
            if value and key not in ("title", "pattern"):
                lines.append(f"- **{key}**: {value}")
        lines += ["", "</details>", "", "---", ""]

        # --- Esquema hierárquico da legislação ---
        lines.extend(self._build_esquema(sections, full_text, doc_title=title))

        lines += ["## 📖 Texto Normativo", ""]

        # ── Detectar contexto estrutural do documento ────────────────────────
        # Identifica se há preâmbulo (seções L0 ou Art. antes do primeiro Livro/Anexo)
        # e se há anexo explícito para calcular offset correto dos níveis
        has_preamble = False
        has_anexo = False
        first_structural_idx = -1

        for i, sec in enumerate(sections):
            if sec.level == 0 or (sec.level == 3 and re.match(r"Art\.?\s*\d+(?:\.\d{3})*", sec.title, re.I)):
                has_preamble = True
            if re.match(r"ANEXO|REGULAMENTO", sec.title, re.I):
                has_anexo = True
                first_structural_idx = i
                break
            if sec.level == 1 or (sec.level > 1 and re.match(r"(LIVRO|TÍTULO|CAPÍTULO)", sec.title, re.I)):
                first_structural_idx = i
                break

        # ── Processar seções com remapeamento dinâmico de níveis ────────────
        
        # Rastrear contexto de Subseção para indentar artigos
        in_subsecao = False
        
        for idx, section in enumerate(sections):
            raw_level = section.level
            title = section.title
            content = section.content

            # ── Detectar se estamos em contexto de Subseção ─────────────────
            is_subsecao = bool(re.match(r"Subse[çc][ãa]o", title, re.I))
            if is_subsecao:
                in_subsecao = True
            elif raw_level <= 4:  # Nova Seção ou nível superior reseta contexto
                in_subsecao = False

            # ── Determinar nível markdown ajustado ──────────────────────────
            # Estrutura esperada:
            #   # → Decreto (raiz)
            #   ## → Artigos do preâmbulo / ANEXO
            #   ### → LIVRO
            #   #### → TÍTULO
            #   ##### → CAPÍTULO
            #   ###### → SEÇÃO / Artigo (contexto RIR)
            #   ####### → SUBSEÇÃO / § (parágrafo)
            #   ######## → Inciso I, II, III
            #   ######### → Alínea a), b), c)

            md_level = 0
            is_article = _is_article_start(title)
            is_anexo = bool(re.match(r"ANEXO|REGULAMENTO", title, re.I))

            # Preâmbulo: artigos antes da estrutura principal
            if has_preamble and idx < first_structural_idx and is_article:
                md_level = 7  # Artigos sempre nível 7 (lista indentada)

            # ANEXO é nível 2
            elif is_anexo:
                md_level = 2

            # Contexto pós-anexo: mapear estrutura hierárquica LC 95/98
            elif first_structural_idx >= 0 and idx >= first_structural_idx:
                if raw_level == 1:  # Livro
                    md_level = 3
                elif raw_level == 2:  # Título
                    md_level = 4
                elif raw_level == 3:  # Capítulo / Artigo RIR
                    if is_article:
                        md_level = 7  # Artigos sempre nível 7 (lista com indentação)
                    else:
                        md_level = 5  # Capítulos #####
                elif raw_level == 4:  # Seção
                    md_level = 6
                elif raw_level == 5:  # Subseção / TpicodeSeo
                    # Se parece com artigo mas não é (referência), ainda renderiza como subtítulo
                    # TpicodeSeo sempre md_level = 7 (subtítulo com *)
                    md_level = 7
                elif raw_level == 6:  # Artigo
                    # Apenas se for realmente um artigo (não uma referência legislativa)
                    if is_article:
                        md_level = 7
                    else:
                        md_level = 0  # Referência legislativa vira corpo de texto
                else:
                    md_level = raw_level  # fallback

            # Seções L0 (texto sem título estrutural)
            elif raw_level == 0:
                md_level = 0

            # Artigos em documentos sem hierarquia estrutural → sempre lista (nível 7)
            elif is_article:
                md_level = 7

            # Fallback: manter nível original
            else:
                md_level = raw_level

            # ── Renderizar título da seção ──────────────────────────────────
            if title and md_level > 0:
                if md_level <= 6:
                    lines += ["", f"{'#' * md_level} {title}", ""]
                elif md_level == 7:
                    # Se é Subseção, com negrito
                    if is_subsecao:
                        lines += ["", f"  * **{title}**", ""]
                    # Se é Artigo: sempre com indentação de 2 espaços
                    elif is_article:
                        lines += ["", f"  * {title}", ""]
                    # Outros níveis 7 (subtítulos TpicodeSeo), sem negrito
                    else:
                        lines += ["", f"  * {title}", ""]
                elif md_level == 8:
                    lines += ["", f"  - **{title}**", ""]
                elif md_level == 9:
                    lines += ["", f"    - **{title}**", ""]
                else:  # md_level >= 10
                    indent = "  " * (md_level - 8)
                    lines += ["", f"{indent}- **{title}**", ""]
            elif title and md_level == 0:
                lines += ["", f"**{title}**", ""]

            # ── Processar conteúdo com sub-hierarquia ───────────────────────
            # Expandir parágrafos (§), incisos (I, II, III), alíneas (a, b, c)
            # como níveis hierárquicos adicionais
            if content:
                content_lines = content.split("\n")
                for line in content_lines:
                    line_stripped = line.strip()
                    if not line_stripped:
                        lines.append("")
                        continue

                    # Parágrafo: * ou -
                    par_m = re.match(r"^(\*\*)?\s*(§\s*(?:único|Único|\d+[º°]?)\.?)\s*(.*?)(\*\*)?$", line_stripped)
                    if par_m:
                        par_marker = par_m.group(2)
                        par_text = par_m.group(3).strip()
                        # Nível 8 para § (um abaixo de artigo nível 7)
                        par_level = md_level + 1 if md_level > 0 else 7
                        
                        # Sempre adicionar indentação extra se estiver em artigo (nível 7)
                        extra_indent = "  " if is_article else ""
                        
                        if par_level <= 6:
                            if par_text:
                                lines += ["", f"{'#' * par_level} {par_marker} {par_text}", ""]
                            else:
                                lines += ["", f"{'#' * par_level} {par_marker}", ""]
                        elif par_level == 7:
                            if par_text:
                                lines += ["", f"{extra_indent}* **{par_marker}** {par_text}", ""]
                            else:
                                lines += ["", f"{extra_indent}* **{par_marker}**", ""]
                        elif par_level == 8:
                            if par_text:
                                lines += ["", f"{extra_indent}  - **{par_marker}** {par_text}", ""]
                            else:
                                lines += ["", f"{extra_indent}  - **{par_marker}**", ""]
                        else:  # par_level >= 9
                            base_indent = "  " * (par_level - 8)
                            if par_text:
                                lines += ["", f"{extra_indent}{base_indent}- **{par_marker}** {par_text}", ""]
                            else:
                                lines += ["", f"{extra_indent}{base_indent}- **{par_marker}**", ""]
                        continue

                    # Inciso romano: I -, II -, III - ...
                    inciso_m = re.match(r"^-?\s*([IVX]+)\s*[-–—]\s*(.*)", line_stripped)
                    if inciso_m:
                        inciso_num = inciso_m.group(1)
                        inciso_text = inciso_m.group(2).strip()
                        # Nível 9 para incisos (dentro de §)
                        inciso_level = md_level + 2 if md_level > 0 else 8
                        
                        # Sempre adicionar indentação extra se estiver em artigo
                        extra_indent = "  " if is_article else ""
                        
                        if inciso_level <= 6:
                            lines += ["", f"{'#' * inciso_level} {inciso_num} - {inciso_text}", ""]
                        elif inciso_level == 7:
                            lines += ["", f"{extra_indent}* {inciso_num} - {inciso_text}", ""]
                        elif inciso_level == 8:
                            lines += ["", f"{extra_indent}  - {inciso_num} - {inciso_text}", ""]
                        elif inciso_level == 9:
                            lines += ["", f"{extra_indent}    - {inciso_num} - {inciso_text}", ""]
                        else:  # inciso_level >= 10
                            base_indent = "  " * (inciso_level - 8)
                            lines += ["", f"{extra_indent}{base_indent}- {inciso_num} - {inciso_text}", ""]
                        continue

                    # Alínea: a), b), c) ...
                    alinea_m = re.match(r"^-?\s*([a-z])\)\s*(.*)", line_stripped)
                    if alinea_m:
                        alinea_letra = alinea_m.group(1)
                        alinea_text = alinea_m.group(2).strip()
                        # Nível 10 para alíneas (dentro de inciso)
                        alinea_level = md_level + 3 if md_level > 0 else 9
                        
                        # Sempre adicionar indentação extra se estiver em artigo
                        extra_indent = "  " if is_article else ""
                        
                        if alinea_level <= 6:
                            lines += ["", f"{'#' * alinea_level} {alinea_letra}) {alinea_text}", ""]
                        elif alinea_level == 7:
                            lines += ["", f"{extra_indent}* {alinea_letra}) {alinea_text}", ""]
                        elif alinea_level == 8:
                            lines += ["", f"{extra_indent}  - {alinea_letra}) {alinea_text}", ""]
                        elif alinea_level == 9:
                            lines += ["", f"{extra_indent}    - {alinea_letra}) {alinea_text}", ""]
                        else:  # alinea_level >= 10
                            base_indent = "  " * (alinea_level - 8)
                            lines += ["", f"{extra_indent}{base_indent}- {alinea_letra}) {alinea_text}", ""]
                        continue

                    # Texto normal
                    lines.append(line)

                lines.append("")

        lines += ["---", "", "*Processado automaticamente pelo LION RAG System*"]

        md_path.write_text("\n".join(lines), encoding="utf-8")
        return md_path


# ===========================================================================
# Funções auxiliares
# ===========================================================================

def _detect_pattern(soup: BeautifulSoup) -> str:
    if soup.find("app-root"):
        return "rfb_spa"
    planalto_classes = {cls.lower() for cls, *_ in PLANALTO_CSS_MAP}
    body = soup.find("body")
    if body:
        for p in body.find_all("p", limit=200):
            for cls in p.get("class", []):
                if cls.lower() in planalto_classes:
                    return "planalto"
    return "generic"


def _has_mojibake(text: str) -> bool:
    mojibake_patterns = ["Ã§", "Ã£", "Ã©", "Ã¡", "Ã³", "nÂº"]
    return any(p in text for p in mojibake_patterns)


def _get_element_text(el) -> str:
    for br in el.find_all("br"):
        br.replace_with(" ")
    text = el.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _is_article_start(text: str) -> bool:
    """Verifica se o texto começa com Art. e é um artigo real, não uma referência."""
    # Aceitar números com separador de milhar (ex: Art. 1.000)
    if not re.match(r"^\s*Art\.?\s*\d+(?:\.\d{3})*[º°]?", text, re.I):
        return False
    
    # Extrair o que vem depois de "Art. Xº"
    m = re.match(r"^\s*Art\.?\s*\d+(?:\.\d{3})*[º°]?(?:-[A-Z])?\.?\s*(.*)", text, re.DOTALL | re.I)
    if not m:
        return True  # Apenas "Art. X" sem nada, é artigo
    
    resto = m.group(1).strip()
    
    # Se está vazio ou começa com maiúscula/texto normal, é artigo
    if not resto or (resto and resto[0].isupper() and not resto.startswith(',')):
        return True
    
    # Se começa com vírgula, é uma referência legislativa, não um artigo
    if resto.startswith(','):
        return False
    
    # Se contém múltiplas referências a artigos antes de um ponto (e.g. "art. 2º e art. 4º ao art. 71"), 
    # é lista de referências
    if re.match(r'^[^.]*\bart\.\s*\d+', resto, re.I):
        return False
    
    return True


def _split_article_head(text: str) -> Tuple[str, str]:
    m = re.match(r"^(Art\.?\s*\d+(?:\.\d{3})*[º°]?(?:-[A-Z])?\.?)\s*(.*)", text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return text, ""


def _format_legal_line(text: str) -> str:
    if re.match(r"^\s*§\s*(?:único|Único|\d+[º°]?)", text, re.I):
        return f"\n**{text.strip()}**\n"
    if re.match(r"^\s*[IVX]+\s*[-–—]", text):
        return f"- {text.strip()}"
    if re.match(r"^\s*[a-z]\)\s", text):
        return f"  - {text.strip()}"
    return text.strip()


def _classify_rfb_segment(text: str) -> Optional[int]:
    if re.match(r"^\s*CAP[IÍ]TULO\s+[IVX0-9]", text, re.I):
        return 3
    if re.match(r"^\s*SE[ÇC][ÃA]O\s+[IVX0-9]", text, re.I):
        return 4
    if re.match(r"^\s*SUBSE[ÇC][ÃA]O", text, re.I):
        return 5
    if re.match(r"^\s*Art\.?\s*\d+(?:\.\d{3})*[º°]?", text, re.I):
        return 6
    return None


def _table_to_markdown(table) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            cell_text = re.sub(r"\s+", " ", cell.get_text(separator=" ", strip=True))
            cell_text = cell_text.replace("|", "\\|")
            cells.append(cell_text)
        if cells and any(c.strip() for c in cells):
            rows.append(cells)

    if len(rows) < 2:
        return ""
    max_cols = max(len(r) for r in rows)
    if max_cols < 2:
        return ""

    for row in rows:
        while len(row) < max_cols:
            row.append("")

    md: List[str] = []
    md.append("| " + " | ".join(rows[0]) + " |")
    md.append("| " + " | ".join(["---"] * max_cols) + " |")
    for row in rows[1:]:
        md.append("| " + " | ".join(row[:max_cols]) + " |")
    return "\n".join(md)


# ===========================================================================
# Helper público e CLI
# ===========================================================================

def extract_html(html_path: str, **kwargs) -> Dict[str, Any]:
    """Extração rápida de HTML."""
    return HTMLExtractor(**kwargs).extract(html_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python html_extractor.py <caminho_html>")
        sys.exit(1)
    r = extract_html(sys.argv[1])
    print(f"Padrão   : {r['pattern']}")
    print(f"Título   : {r['metadata'].get('title','')[:80]}")
    print(f"Seções   : {len(r['sections'])}")
    print(f"Chars    : {len(r['full_text'])}")
    for sec in r["sections"][:10]:
        indent = "  " * (sec.level - 1) if sec.level > 0 else ""
        print(f"{indent}[L{sec.level}] {sec.title[:70]} ({len(sec.content)} chars)")
