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

        for el in body.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"]):
            if el.find_parent("table"):
                continue

            text = _get_element_text(el)
            if not text or len(text) < self.min_text_length:
                continue

            classes = el.get("class", [])
            mapping = _lookup_css(classes) if classes else None

            if mapping is None and el.name in ("h1","h2","h3","h4","h5","h6"):
                lvl = int(el.name[1])
                mapping = (lvl, "#" * lvl + " ", "heading")

            # Parágrafos sem classe CSS: aplicar heurística de artigo/parágrafo/inciso
            if mapping is None:
                if _is_article_start(text):
                    mapping = (6, "###### ", "article")
                elif re.match(r"^\s*§\s*(?:único|Único|\d+[º°]?)", text, re.I):
                    mapping = (0, "", "body")  # parágrafo → formato negrito via _format_legal_line
                elif re.match(r"^\s*CAP[IÍ]TULO\s+", text, re.I):
                    mapping = (3, "### ", "heading")
                elif re.match(r"^\s*SE[ÇC][ÃA]O\s+", text, re.I):
                    mapping = (4, "#### ", "heading")
                else:
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

        _flush()

        # Tabelas
        for table in body.find_all("table"):
            if table.find_parent("table"):
                continue
            table_md = _table_to_markdown(table)
            if table_md:
                sections.append(HTMLSection(
                    title="", content=table_md, level=0, tag_name="table",
                    metadata={"type": "tabela"},
                ))

        return sections

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

        # --- Índice de artigos: coletado dos títulos de seção (não do full_text)
        # para garantir que cada entrada corresponda a uma âncora real no documento
        art_sections = [
            s for s in sections
            if s.title and re.match(r"^\s*Art\.?\s*\d+", s.title, re.I)
        ]
        # Deduplicar por número normalizado (sem º/°)
        seen_nums: set = set()
        unique_arts: List[HTMLSection] = []
        for s in art_sections:
            m = re.search(r"(\d+)", s.title)
            key = m.group(1) if m else s.title
            if key not in seen_nums:
                seen_nums.add(key)
                unique_arts.append(s)

        if unique_arts:
            lines += ["## 📑 Índice de Artigos", ""]
            for s in unique_arts:
                m = re.search(r"(\d+[º°]?(?:-[A-Z])?)", s.title)
                art_raw = m.group(1) if m else s.title
                art_id = re.sub(r"[º°]", "", art_raw).lower()
                lines.append(f"- [Art. {art_raw}](#art-{art_id})")
            lines += ["", "---", ""]

        lines += ["## 📖 Texto Normativo", ""]

        for section in sections:
            level = max(1, min(section.level, 6)) if section.level > 0 else 0

            if section.title:
                if level > 0:
                    # Adicionar âncora em TODOS os headings de artigo (qualquer nível)
                    art_m = re.match(r"Art\.?\s*(\d+[º°]?(?:-[A-Z])?)", section.title, re.I)
                    if art_m:
                        art_id = re.sub(r"[º°]", "", art_m.group(1)).lower()
                        lines += ["", f"{'#' * level} {section.title} {{#art-{art_id}}}", ""]
                    else:
                        lines += ["", f"{'#' * level} {section.title}", ""]
                else:
                    lines += ["", f"**{section.title}**", ""]

            if section.content:
                lines += section.content.split("\n")
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
    return bool(re.match(r"^\s*Art\.?\s*\d+[º°]?", text, re.I))


def _split_article_head(text: str) -> Tuple[str, str]:
    m = re.match(r"^(Art\.?\s*\d+[º°]?(?:-[A-Z])?\.?)\s*(.*)", text, re.DOTALL)
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
    if re.match(r"^\s*Art\.?\s*\d+[º°]?", text, re.I):
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
