"""
BaseExtractor - LION
Classe base abstrata para todos os extractors do pipeline de ingestão.

Provê métodos compartilhados de:
  - Leitura de arquivos com detecção de encoding
  - Correção de mojibake (cp1252 lido como latin-1)
  - Persistência em Markdown estruturado
  - Heurísticas de estrutura para documentos jurídicos brasileiros
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Mapeamento de heurísticas legais para documentos sem CSS semântico
# ---------------------------------------------------------------------------
LEGAL_HEURISTICS: List[Tuple[re.Pattern, str, int]] = [
    # (padrão, prefixo_markdown, nível_numérico)
    (re.compile(r"^\s*(LIVRO\s+[IVXLCDM]+\b.*)$", re.I), "# ", 1),
    (re.compile(r"^\s*(TÍTULO\s+[IVXLCDM]+\b.*)$", re.I), "## ", 2),
    (re.compile(r"^\s*(CAPÍTULO\s+[IVXLCDM0-9]+[-\w]*\b.*)$", re.I), "### ", 3),
    (re.compile(r"^\s*(SEÇÃO\s+[IVXLCDM0-9]+[-\w]*\b.*)$", re.I), "#### ", 4),
    (re.compile(r"^\s*(SUBSEÇÃO\s+[IVXLCDM0-9]+[-\w]*\b.*)$", re.I), "##### ", 5),
    (re.compile(r"^\s*(Art\.\s*\d+[º°]?(?:-[A-Z])?\.?\s*.*)$"), "######-art ", 6),
    (re.compile(r"^\s*(§\s*(?:único|Único|\d+[º°]?)\.?\s*.*)$"), "**§** ", None),
]

INCISO_PATTERN = re.compile(r"^\s*([IVX]+)\s*[-–—]\s*")
ALINEA_PATTERN = re.compile(r"^\s*([a-z])\)\s*")
NUMERO_PATTERN = re.compile(r"^\s*(\d+)\.\s+")


class BaseExtractor(ABC):
    """
    Classe base para todos os extractors do LION.

    Subclasses devem implementar `extract(file_path) -> Dict[str, Any]`.
    O dict retornado deve conter pelo menos:
        - metadata: Dict com campos do documento
        - sections: List de seções (objetos dataclass com .title/.content/.level)
        - full_text: str com texto concatenado

    Métodos utilitários disponíveis para subclasses:
        - _read_with_encoding(path) → str
        - _fix_mojibake(text) → str
        - _apply_legal_heuristics(lines) → List[str]
        - save_to_markdown(source_path, result, output_dir) → Path
    """

    # Encodings tentados nesta ordem ao ler arquivos
    ENCODING_PRIORITY = ["utf-8", "cp1252", "latin-1", "iso-8859-1"]

    # ------------------------------------------------------------------
    # Interface pública obrigatória
    # ------------------------------------------------------------------

    @abstractmethod
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extrai conteúdo estruturado do arquivo informado."""
        ...

    # ------------------------------------------------------------------
    # Leitura de arquivos
    # ------------------------------------------------------------------

    def _read_with_encoding(self, path: Path) -> str:
        """
        Lê arquivo tentando encodings em ordem de prioridade.
        Nunca lança UnicodeDecodeError — usa 'replace' como fallback final.

        Args:
            path: Caminho do arquivo

        Returns:
            Conteúdo do arquivo como string
        """
        for enc in self.ENCODING_PRIORITY:
            try:
                return path.read_text(encoding=enc)
            except (UnicodeDecodeError, LookupError):
                continue
        # Fallback absoluto
        return path.read_text(encoding="latin-1", errors="replace")

    def _detect_encoding(self, path: Path) -> str:
        """
        Detecta o encoding mais provável para o arquivo.
        Retorna o primeiro encoding que consegue ler sem erros.
        """
        for enc in self.ENCODING_PRIORITY:
            try:
                path.read_text(encoding=enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue
        return "latin-1"

    # ------------------------------------------------------------------
    # Correção de texto
    # ------------------------------------------------------------------

    def _fix_mojibake(self, text: str) -> str:
        """
        Corrige mojibake típico de documentos brasileiros (cp1252 lido como latin-1).

        Situação: o HTML declara charset=utf-8, mas o arquivo está em cp1252.
        Ao ler com latin-1 os bytes ficam "mal mapeados" — ex. 'Ã§' em vez de 'ç'.

        A correção re-encode o texto como latin-1 e decodifica como cp1252.
        """
        try:
            return text.encode("latin-1").decode("cp1252")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text

    def _clean_text(self, text: str) -> str:
        """Limpeza básica: múltiplos espaços, espaços em torno de newlines."""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Heurísticas jurídicas
    # ------------------------------------------------------------------

    def _apply_legal_heuristics(self, lines: List[str]) -> List[str]:
        """
        Aplica heurísticas de estrutura para documentos jurídicos brasileiros.

        Transforma linhas de texto puro em Markdown hierárquico usando padrões
        como LIVRO, TÍTULO, CAPÍTULO, SEÇÃO, Art., §, incisos e alíneas.

        Args:
            lines: Lista de linhas de texto puro

        Returns:
            Lista de linhas com marcadores Markdown inseridos
        """
        result: List[str] = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                result.append("")
                continue

            matched = False

            # Testar heurísticas hierárquicas
            for pattern, prefix, level in LEGAL_HEURISTICS:
                m = pattern.match(line)
                if m:
                    if prefix == "######-art ":
                        # Artigos: headline com âncora
                        art_text = m.group(1)
                        art_num_m = re.search(r"(\d+[º°]?(?:-[A-Z])?)", art_text)
                        art_id = art_num_m.group(1).replace("º", "").replace("°", "").lower() if art_num_m else ""
                        result.append("")
                        result.append(f"###### {art_text} {{#art-{art_id}}}")
                        result.append("")
                    elif prefix == "**§** ":
                        # Parágrafos: negrito
                        result.append("")
                        result.append(f"**{m.group(1)}**")
                        result.append("")
                    else:
                        result.append("")
                        result.append(f"{prefix}{m.group(1)}")
                        result.append("")
                    matched = True
                    break

            if matched:
                continue

            # Incisos romanos
            if INCISO_PATTERN.match(line):
                result.append(f"- {line}")
                continue

            # Alíneas
            if ALINEA_PATTERN.match(line):
                result.append(f"  - {line}")
                continue

            # Numeração ordinal
            if NUMERO_PATTERN.match(line):
                result.append(f"  - {line}")
                continue

            # Texto normal
            result.append(line)

        return result

    # ------------------------------------------------------------------
    # Esquema hierárquico da legislação
    # ------------------------------------------------------------------

    def _build_esquema(
        self,
        sections: List,
        full_text: str,
        max_entries: int = 100,
    ) -> List[str]:
        """
        Constrói o Esquema hierárquico da legislação.

        Substitui o antigo Índice de Artigos por uma representação visual
        da estrutura jurídica completa, usando marcadores Markdown (#) cujo
        número é proporcional ao nível na hierarquia da Lei Complementar 95/98:

            #       → Livro / Parte          (nível 1)
            ##      → Título / Subtítulo     (nível 2)
            ###     → Capítulo               (nível 3)
            ####    → Seção                  (nível 4)
            #####   → Subseção               (nível 5)
            ######  → Artigo                 (nível 6)

        Para leis extensas (ex.: RIR com 676 artigos e 787 capítulos), a
        profundidade exibida é reduzida automaticamente de forma que o esquema
        não ultrapasse `max_entries` entradas, preservando sempre os níveis
        mais altos da hierarquia.

        Args:
            sections:    Seções estruturadas retornadas por extract().
            full_text:   Texto completo — usado como fallback de parsing
                         quando sections estiver vazio.
            max_entries: Número máximo de entradas a exibir no esquema.

        Returns:
            Lista de linhas Markdown prontas para inserção no documento.
        """
        # ── Nomes canônicos por nível ────────────────────────────────────────
        LEVEL_NAMES = {
            1: "Livro/Parte",
            2: "Título",
            3: "Capítulo",
            4: "Seção",
            5: "Subseção",
            6: "Artigo",
        }

        headings: List[Tuple[int, str]] = []

        # ── Fonte primária: seções estruturadas do extractor ────────────────
        if sections:
            for sec in sections:
                lvl: int = getattr(sec, "level", 0)
                title: str = (getattr(sec, "title", "") or "").strip()
                if lvl > 0 and title:
                    # Remover âncoras Markdown {#art-1}
                    title = re.sub(r"\s*\{#[^}]+\}", "", title).strip()
                    # Remover notas de vigência/alteração comuns em legislação
                    title = re.sub(
                        r"\s*\((?:Incluído|Redação|Revogado|Acrescido)[^)]*\)", "", title, flags=re.I
                    ).strip()
                    title = re.sub(r"\s+Produção de efeitos.*$", "", title).strip()
                    # Truncar títulos excessivamente longos (corpo de artigo como título)
                    if len(title) > 120:
                        title = title[:117] + "…"
                    if title:
                        headings.append((lvl, title))

        # ── Fallback: heurísticas sobre full_text ───────────────────────────
        if not headings and full_text:
            _SCHEME_PATTERNS: List[Tuple[re.Pattern, int]] = [
                (re.compile(r"^\s*((?:LIVRO|PARTE)\s+[IVXLCDM\d]+[-\w]*\b.*)", re.I), 1),
                (re.compile(r"^\s*(TÍTULO\s+[IVXLCDM\d]+[-\w]*\b.*)",             re.I), 2),
                (re.compile(r"^\s*(CAPÍTULO\s+[IVXLCDM\d]+[-\w]*\b.*)",           re.I), 3),
                (re.compile(r"^\s*(SEÇÃO\s+[IVXLCDM\d]+[-\w]*\b.*)",              re.I), 4),
                (re.compile(r"^\s*(SUBSEÇÃO\s+[IVXLCDM\d]+[-\w]*\b.*)",           re.I), 5),
                (re.compile(r"^\s*(Art\.\s*\d+[º°]?(?:-[A-Z])?\.?\s.*)"),          6),
            ]
            for line in full_text.splitlines():
                for pat, lvl in _SCHEME_PATTERNS:
                    m = pat.match(line)
                    if m:
                        headings.append((lvl, m.group(1).strip()))
                        break

        if not headings:
            return []

        # ── Determinar a profundidade máxima a exibir ────────────────────────
        # Incrementa o nível enquanto o total acumulado não ultrapassa max_entries.
        max_depth = 1
        for depth in range(1, 7):
            count = sum(1 for lvl, _ in headings if lvl <= depth)
            if count <= max_entries:
                max_depth = depth
            else:
                break

        filtered = [(lvl, t) for lvl, t in headings if lvl <= max_depth]

        # Truncar se ainda ultrapassar (edge case: nível único com muitas entradas)
        truncated = len(filtered) > max_entries
        if truncated:
            filtered = filtered[:max_entries]

        if not filtered:
            return []

        # ── Compor descrição do bloco colapsável ─────────────────────────────
        art_total = sum(1 for lvl, _ in headings if lvl == 6)
        depth_label = LEVEL_NAMES.get(max_depth, str(max_depth))

        if max_depth < 6 and art_total > 0:
            # Esquema estrutural sem artigos
            summary = (
                f"📋 Esquema da Legislação"
                f" — até {depth_label}"
                f" ({art_total} artigos não exibidos)"
            )
        else:
            summary = "📋 Esquema da Legislação"

        # ── Montar linhas Markdown ───────────────────────────────────────────
        out: List[str] = []
        out += ["<details>", f"<summary>{summary}</summary>", ""]

        for lvl, title in filtered:
            hashes = "#" * max(1, min(lvl, 6))
            out.append(f"{hashes} {title}")

        if truncated:
            omitted = len(headings) - max_entries
            out += ["", f"> *… {omitted:,} entrada(s) omitida(s)*"]

        out += ["", "</details>", "", "---", ""]
        return out

    # ------------------------------------------------------------------
    # Persistência em Markdown
    # ------------------------------------------------------------------

    def save_to_markdown(
        self,
        source_path: Path,
        result: Dict[str, Any],
        output_dir: Optional[Path] = None,
        suffix: str = "_processed",
    ) -> Path:
        """
        Salva o resultado da extração em arquivo Markdown estruturado.

        O arquivo gerado contém:
            - Cabeçalho YAML-like com metadados
            - Corpo com texto hierárquico em Markdown

        Args:
            source_path: Caminho do arquivo de origem
            result: Dict retornado por extract()
            output_dir: Pasta de saída (padrão: data/processed/markdown/legislation/)
            suffix: Sufixo adicionado ao nome do arquivo de saída

        Returns:
            Path do arquivo .md gerado
        """
        if output_dir is None:
            output_dir = Path("data/processed/markdown/legislation")
        output_dir.mkdir(parents=True, exist_ok=True)

        md_path = output_dir / f"{source_path.stem}{suffix}.md"
        metadata = result.get("metadata", {})
        full_text = result.get("full_text", "")
        sections = result.get("sections", [])

        lines: List[str] = []

        # ---- Título ----
        title = metadata.get("title") or source_path.stem
        lines += [f"# {title}", ""]

        # ---- Bloco de metadados ----
        lines += [
            "<details>",
            "<summary>📋 Metadados do Documento</summary>",
            "",
            f"- **Arquivo**: `{source_path.name}`",
            f"- **Processado em**: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ]
        for key, value in metadata.items():
            if value and key != "title":
                lines.append(f"- **{key}**: {value}")
        lines += ["", "</details>", "", "---", ""]

        # ---- Esquema hierárquico da legislação ----
        lines.extend(self._build_esquema(sections, full_text))

        # ---- Conteúdo ----
        if sections:
            for section in sections:
                prefix = "#" * max(1, min(section.level, 6))
                lines += [f"{prefix}# {section.title}", ""]
                if section.content:
                    lines += section.content.split("\n")
                    lines.append("")
        else:
            # Fallback: texto puro com heurísticas
            raw_lines = full_text.split("\n")
            processed = self._apply_legal_heuristics(raw_lines)
            lines.extend(processed)

        # ---- Rodapé ----
        lines += ["", "---", "", "*Processado automaticamente pelo LION RAG System*"]

        md_path.write_text("\n".join(lines), encoding="utf-8")
        return md_path
