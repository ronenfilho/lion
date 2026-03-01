"""
Script 6: Auditoria dos Documentos Processados
===============================================
Analisa todos os .md em data/processed/markdown/legislation/ e gera:
  - experiments/results/analysis/audit_processed_docs_<timestamp>.csv
  - experiments/results/analysis/audit_processed_docs_<timestamp>.md

Tabela principal (estilo referência acadêmica):
  · Reference count  — quantas vezes o doc foi recuperado nos experimentos RAG
  · Word count       — total de palavras do documento processado
  + linha de total com percentual de cobertura do corpus indexado

Métricas secundárias por arquivo:
  · Metadados do cabeçalho (padrão, encoding, data de processamento)
  · Estrutura hierárquica: total de headings H1-H6
  · Artigos: total com heading, no índice, com âncora, quebrados
  · Elementos legais: parágrafos (§), incisos, alíneas
  · Qualidade: links quebrados, mojibake residual, linhas em branco
  · Tamanho: chars, palavras, linhas, linhas de corpo, KB
  · Hash SHA-256 para rastreabilidade

Uso:
    python scripts/6_audit_processed_docs.py
    python scripts/6_audit_processed_docs.py --input-dir data/processed/markdown/legislation
    python scripts/6_audit_processed_docs.py --experiments-dir data/experiments/results/raw
    python scripts/6_audit_processed_docs.py --no-md     # só CSV
"""

import argparse
import csv
import hashlib
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

DEFAULT_INPUT_DIR  = BASE_DIR / "data" / "processed" / "markdown" / "legislation"
DEFAULT_OUTPUT_DIR = BASE_DIR / "experiments" / "results" / "analysis"
DEFAULT_EXP_DIR    = BASE_DIR / "data" / "experiments" / "results" / "raw"

# Mapa: stem do arquivo → nome canônico para exibição na tabela principal
DOC_DISPLAY_NAMES: dict[str, str] = {
    "D9580":               "Decreto nº 9.580, de 22 de novembro de 2018",
    "IN RFB nº 1500_2014": "Instrução Normativa RFB nº 1500, de 29 de outubro de 2014",
    "IN RFB nº 2178-2024": "Instrução Normativa RFB nº 2178, de 05 de março de 2024",
    "IN RFB nº 2178_2024": "Instrução Normativa RFB nº 2178, de 05 de março de 2024",
    "L15270":              "Lei nº 15.270, de 26 de novembro de 2025",
    "L7713compilada":      "Lei nº 7.713, de 22 de dezembro de 1988",
    "L9250compilado":      "Lei nº 9.250, de 26 de dezembro de 1995",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"{_ts}_audit_processed_docs.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex compilados
# ---------------------------------------------------------------------------
RE_META_PATTERN  = re.compile(r"\*\*Padrão detectado\*\*:\s*(.+)")
RE_META_ENCODING = re.compile(r"\*\*encoding_detected\*\*:\s*(.+)")
RE_META_DATE     = re.compile(r"\*\*Processado em\*\*:\s*(.+)")
RE_META_SOURCE   = re.compile(r"\*\*Arquivo\*\*:\s*`(.+?)`")
RE_ANCHOR        = re.compile(r"\{#art-([^}]+)\}")
RE_INDEX_LINK    = re.compile(r"\[Art\.\s*[^\]]+\]\(#art-([^)]+)\)")
RE_HEADING       = re.compile(r"^(#{1,6})\s+")
RE_HEADING_ART   = re.compile(r"^#{1,6}\s+Art\.")
RE_BOLD_SECTION  = re.compile(r"^\*\*(?:§|Parágrafo)")
RE_INCISO        = re.compile(r"^-\s+[IVX]+\s+-")
RE_ALINEA        = re.compile(r"^\s{2}-\s+[a-z]\)")


# ---------------------------------------------------------------------------
# Contagem de referências nos experimentos RAG
# ---------------------------------------------------------------------------

def count_experiment_references(exp_dir: Path) -> tuple[dict[str, int], int]:
    """
    Percorre JSONs de resultados em exp_dir e conta, por documento,
    quantas perguntas recuperaram ao menos um chunk daquele documento.
    Retorna (dict[filename → count], total_json_files).
    """
    ref_counts: dict[str, int] = defaultdict(int)
    json_files = [
        f for f in exp_dir.glob("*.json")
        if "summary" not in f.name and "chunk_count" not in f.name
    ]
    if not json_files:
        logger.warning(f"Nenhum JSON de experimento em {exp_dir}")
        return {}, 0

    logger.info(f"Lendo {len(json_files)} arquivo(s) de experimento em {exp_dir}")
    for jpath in sorted(json_files):
        try:
            with open(jpath, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            logger.warning(f"Não foi possível ler {jpath.name}: {exc}")
            continue
        for result in data.get("individual_results", []):
            seen: set[str] = set()
            for chunk in result.get("chunks", []):
                fname = chunk.get("metadata", {}).get("filename", "")
                if fname and fname not in seen:
                    ref_counts[fname] += 1
                    seen.add(fname)
    return dict(ref_counts), len(json_files)


# ---------------------------------------------------------------------------
# Análise de um arquivo .md
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def detect_mojibake(text: str) -> list[str]:
    patterns = [
        r"Ã[§çÃÂÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]",
        r"n[Ãâ][°º]",
        r"seÃ",
        r"aÃ",
    ]
    hits: list[str] = []
    for pat in patterns:
        hits.extend(re.findall(pat, text)[:3])
    return hits


def analyze_md(path: Path, ref_count: int = 0) -> dict[str, Any]:
    """Extrai todas as métricas de um arquivo .md processado."""
    text  = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # --- Metadados do cabeçalho ---
    def _meta(rx: re.Pattern) -> str:
        m = rx.search(text)
        return m.group(1).strip() if m else "N/A"

    meta_pattern  = _meta(RE_META_PATTERN)
    meta_encoding = _meta(RE_META_ENCODING)
    meta_date     = _meta(RE_META_DATE)
    meta_source   = _meta(RE_META_SOURCE) if RE_META_SOURCE.search(text) else path.name

    # --- Nome de exibição ---
    stem         = path.stem.replace("_processed", "")
    display_name = DOC_DISPLAY_NAMES.get(stem, stem)

    # --- Estrutura de headings ---
    heading_counts = {i: 0 for i in range(1, 7)}
    art_headings = bold_sections = incisos = alineas = body_lines = 0

    for line in lines:
        m = RE_HEADING.match(line)
        if m:
            level = len(m.group(1))
            heading_counts[level] += 1
            if RE_HEADING_ART.match(line):
                art_headings += 1
        elif RE_BOLD_SECTION.match(line):
            bold_sections += 1
        elif RE_INCISO.match(line):
            incisos += 1
        elif RE_ALINEA.match(line):
            alineas += 1
        elif line.strip() and not line.startswith("<") and not line.startswith("|"):
            body_lines += 1

    # --- Âncoras e índice ---
    anchors      = set(RE_ANCHOR.findall(text))
    index_links  = list(dict.fromkeys(RE_INDEX_LINK.findall(text)))
    broken_links = [lk for lk in index_links if lk not in anchors]

    # --- Qualidade ---
    mojibake_samples = detect_mojibake(text)
    max_consec = cur = 0
    for line in lines:
        cur = cur + 1 if not line.strip() else 0
        max_consec = max(max_consec, cur)
    blank_blocks_3x = len(re.findall(r"\n{4,}", text))

    return {
        # identificação
        "arquivo_md":          path.name,
        "arquivo_fonte":       meta_source,
        "nome_documento":      display_name,
        "padrao_detectado":    meta_pattern,
        "encoding_detectado":  meta_encoding,
        "processado_em":       meta_date,
        # referências nos experimentos RAG
        "reference_count":     ref_count,
        # estrutura hierárquica
        "h1_total":            heading_counts[1],
        "h2_total":            heading_counts[2],
        "h3_total":            heading_counts[3],
        "h4_total":            heading_counts[4],
        "h5_total":            heading_counts[5],
        "h6_total":            heading_counts[6],
        "headings_total":      sum(heading_counts.values()),
        # artigos
        "artigos_com_heading": art_headings,
        "artigos_no_indice":   len(index_links),
        "ancoras_no_texto":    len(anchors),
        "links_quebrados":     len(broken_links),
        "links_quebrados_ids": "; ".join(broken_links),
        # elementos legais
        "paragrafos_bold":     bold_sections,
        "incisos":             incisos,
        "alineas":             alineas,
        # qualidade
        "mojibake_residual":   bool(mojibake_samples),
        "mojibake_amostras":   "; ".join(mojibake_samples[:5]),
        "blocos_em_branco_3x": blank_blocks_3x,
        "max_linhas_brancas":  max_consec,
        # tamanho
        "total_chars":         len(text),
        "total_palavras":      len(text.split()),
        "total_linhas":        len(lines),
        "linhas_corpo":        body_lines,
        "tamanho_kb":          round(path.stat().st_size / 1024, 2),
        # rastreabilidade
        "sha256":              sha256_file(path),
    }


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "arquivo_md", "arquivo_fonte", "nome_documento",
    "padrao_detectado", "encoding_detectado", "processado_em",
    "reference_count",
    "h1_total", "h2_total", "h3_total", "h4_total", "h5_total", "h6_total",
    "headings_total",
    "artigos_com_heading", "artigos_no_indice", "ancoras_no_texto",
    "links_quebrados", "links_quebrados_ids",
    "paragrafos_bold", "incisos", "alineas",
    "mojibake_residual", "mojibake_amostras",
    "blocos_em_branco_3x", "max_linhas_brancas",
    "total_chars", "total_palavras", "total_linhas", "linhas_corpo",
    "tamanho_kb", "sha256",
]


def write_csv(rows: list[dict], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"CSV salvo em: {output_path}")


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _quality_badge(row: dict) -> str:
    issues = []
    if row["links_quebrados"] > 0:
        issues.append(f"{row['links_quebrados']} link(s) quebrado(s)")
    if row["mojibake_residual"]:
        issues.append("mojibake")
    if row["blocos_em_branco_3x"] > 5:
        issues.append(f"{row['blocos_em_branco_3x']}× blank")
    return "✅" if not issues else "⚠️ " + " | ".join(issues)


def _bar(value: int, max_val: int, width: int = 15) -> str:
    if max_val == 0:
        return "░" * width
    filled = round((value / max_val) * width)
    return "█" * filled + "░" * (width - filled)


def _ref_bar(value: int, total: int, width: int = 20) -> str:
    if total == 0:
        return "░" * width
    filled = round((value / total) * width)
    return "█" * filled + "░" * (width - filled)


def write_md(
    rows: list[dict],
    output_path: Path,
    generated_at: str,
    total_exp_files: int,
) -> None:
    # Totais
    total_ref    = sum(r["reference_count"] for r in rows)
    total_words  = sum(r["total_palavras"] for r in rows)
    total_chars  = sum(r["total_chars"] for r in rows)
    total_arts   = sum(r["artigos_com_heading"] for r in rows)
    total_broken = sum(r["links_quebrados"] for r in rows)
    ok_files     = sum(1 for r in rows if not r["links_quebrados"] and not r["mojibake_residual"])
    n_indexed    = sum(1 for r in rows if r["reference_count"] > 0)
    indexed_wc   = sum(r["total_palavras"] for r in rows if r["reference_count"] > 0)
    pct_indexed  = indexed_wc / total_words * 100 if total_words else 0

    rows_sorted = sorted(rows, key=lambda r: -r["reference_count"])
    max_ref   = max((r["reference_count"] for r in rows), default=1) or 1
    max_words = max((r["total_palavras"] for r in rows), default=1) or 1
    max_arts  = max((r["artigos_com_heading"] for r in rows), default=1) or 1
    max_chars = max((r["total_chars"] for r in rows), default=1) or 1

    L: list[str] = []

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    L += [
        "# Corpus de Documentos Processados — Auditoria",
        "",
        f"> **Gerado em:** {generated_at}  ",
        f"> **Experimentos RAG analisados:** {total_exp_files} arquivo(s) JSON  ",
        f"> **Diretório de entrada:** `data/processed/markdown/legislation/`",
        "",
        "---",
        "",
    ]

    # ── Tabela Principal estilo acadêmico ────────────────────────────────────
    L += [
        "## Corpus Overview",
        "",
        "Tabela ordenada por **Reference count** — número de perguntas nos experimentos "
        "RAG que recuperaram ao menos um chunk do documento.",
        "",
        "| Reference count | Document | Word count |",
        "|----------------:|----------|----------:|",
    ]
    for r in rows_sorted:
        L.append(
            f"| {r['reference_count']:,} "
            f"| {r['nome_documento']} "
            f"| {r['total_palavras']:,} |"
        )
    # Linha de total
    L += [
        f"| **Total {total_ref:,}** "
        f"| _{n_indexed} documento(s) indexado(s) de {len(rows)} processado(s)_ "
        f"| **{total_words:,}** |",
        "",
        f"> **Cobertura do corpus indexado:** {pct_indexed:.2f}% "
        f"({indexed_wc:,} de {total_words:,} palavras)",
        "",
        "---",
        "",
    ]

    # ── Visão geral de qualidade ─────────────────────────────────────────────
    L += [
        "## Visão Geral — Qualidade e Estrutura",
        "",
        "| Arquivo | Padrão | Artigos | Âncoras | Quebrados | Palavras | Status |",
        "|---------|--------|--------:|--------:|----------:|---------:|--------|",
    ]
    for r in rows_sorted:
        stem = r["arquivo_md"].replace("_processed.md", "")
        L.append(
            f"| `{stem}` "
            f"| `{r['padrao_detectado']}` "
            f"| {r['artigos_com_heading']} "
            f"| {r['ancoras_no_texto']} "
            f"| {r['links_quebrados']} "
            f"| {r['total_palavras']:,} "
            f"| {_quality_badge(r)} |"
        )
    L += ["", "---", ""]

    # ── Resumo executivo ─────────────────────────────────────────────────────
    L += [
        "## Resumo Executivo",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| Documentos processados | {len(rows)} |",
        f"| Documentos indexados (com ref.) | {n_indexed} |",
        f"| Documentos sem problemas | {ok_files} / {len(rows)} |",
        f"| Total de artigos detectados | {total_arts:,} |",
        f"| Total de links quebrados | {total_broken} |",
        f"| Total de palavras no corpus | {total_words:,} |",
        f"| Total de caracteres | {total_chars:,} |",
        f"| Total de referências RAG | {total_ref:,} |",
        "",
        "---",
        "",
    ]

    # ── Distribuição de referências (barra visual) ───────────────────────────
    if total_ref > 0:
        L += [
            "## Distribuição de Referências RAG",
            "",
            "```",
            f"{'Documento':<50} {'Refs':>6}  {'%':>6}  Distribuição",
            "─" * 90,
        ]
        for r in rows_sorted:
            ref  = r["reference_count"]
            pct  = ref / total_ref * 100 if total_ref else 0
            stem = r["arquivo_md"].replace("_processed.md", "")[:48]
            L.append(f"  {stem:<50} {ref:>6}  {pct:>5.1f}%  {_ref_bar(ref, total_ref, 25)}")
        L += [
            f"  {'─'*50}  {'─'*6}  {'─'*6}",
            f"  {'TOTAL':<50} {total_ref:>6}  100.0%",
            "```",
            "",
            "---",
            "",
        ]

    # ── Detalhes por arquivo ─────────────────────────────────────────────────
    L += ["## Detalhes por Arquivo", ""]

    for r in rows_sorted:
        stem    = r["arquivo_md"].replace("_processed.md", "")
        ref     = r["reference_count"]
        ref_pct = f"{ref / total_ref * 100:.1f}%" if total_ref else "–"

        L += [
            f"### `{stem}`",
            "",
            f"**{r['nome_documento']}**  ",
            f"**Fonte:** `{r['arquivo_fonte']}` | "
            f"**Padrão:** `{r['padrao_detectado']}` | "
            f"**Encoding:** `{r['encoding_detectado']}` | "
            f"**Processado em:** {r['processado_em']}",
            "",
            "| Métrica | Valor | Proporção |",
            "|---------|------:|-----------|",
            f"| Reference count | {ref:,} | {ref_pct} do total RAG  {_ref_bar(ref, total_ref, 12)} |",
            f"| Word count | {r['total_palavras']:,} | {r['total_palavras']/total_words*100:.1f}% do corpus  {_bar(r['total_palavras'], max_words, 12)} |",
            f"| Artigos (headings) | {r['artigos_com_heading']} | {_bar(r['artigos_com_heading'], max_arts, 12)} |",
            f"| Caracteres | {r['total_chars']:,} | {_bar(r['total_chars'], max_chars, 12)} |",
            f"| Tamanho | {r['tamanho_kb']} KB | – |",
            "",
            "#### Estrutura Hierárquica",
            "",
            "| Nível | Contagem |",
            "|-------|----------|",
        ]
        for h in range(1, 7):
            cnt = r[f"h{h}_total"]
            if cnt:
                L.append(f"| H{h} | {cnt} |")
        L += [
            f"| **Total** | **{r['headings_total']}** |",
            "",
            "#### Artigos e Navegação",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| Headings de artigo | {r['artigos_com_heading']} |",
            f"| Links no índice | {r['artigos_no_indice']} |",
            f"| Âncoras no texto | {r['ancoras_no_texto']} |",
            f"| Links quebrados | {r['links_quebrados']} |",
        ]
        if r["links_quebrados_ids"]:
            L.append(f"| IDs quebrados | `{r['links_quebrados_ids']}` |")
        L += [
            "",
            "#### Elementos Legais",
            "",
            "| Elemento | Contagem |",
            "|----------|----------|",
            f"| Parágrafos (§) | {r['paragrafos_bold']} |",
            f"| Incisos | {r['incisos']} |",
            f"| Alíneas | {r['alineas']} |",
            "",
            "#### Qualidade",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| Mojibake residual | {'⚠️ Sim' if r['mojibake_residual'] else '✅ Não'} |",
            f"| Blocos em branco (≥3×) | {r['blocos_em_branco_3x']} |",
            f"| Máx. linhas brancas consecutivas | {r['max_linhas_brancas']} |",
        ]
        if r["mojibake_amostras"]:
            L.append(f"| Amostras mojibake | `{r['mojibake_amostras']}` |")
        L += [
            "",
            "#### Rastreabilidade",
            "",
            "```",
            f"SHA-256: {r['sha256']}",
            "```",
            "",
            "---",
            "",
        ]

    output_path.write_text("\n".join(L), encoding="utf-8")
    logger.info(f"Markdown salvo em: {output_path}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auditoria dos documentos .md processados → CSV + Markdown"
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT_DIR),
        help=f"Diretório com os .md processados (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Diretório de saída CSV/MD (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--experiments-dir",
        default=str(DEFAULT_EXP_DIR),
        help=f"Diretório com JSONs de experimentos RAG (default: {DEFAULT_EXP_DIR})",
    )
    parser.add_argument(
        "--no-md",
        action="store_true",
        help="Não gerar relatório Markdown (só CSV)",
    )
    args = parser.parse_args()

    input_dir  = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    exp_dir    = Path(args.experiments_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        logger.error(f"Diretório de entrada não encontrado: {input_dir}")
        sys.exit(1)

    md_files = sorted(input_dir.glob("*_processed.md"))
    if not md_files:
        logger.error(f"Nenhum *_processed.md em {input_dir}")
        sys.exit(1)

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- Referências nos experimentos RAG ---
    ref_counts, total_exp_files = count_experiment_references(exp_dir) \
        if exp_dir.exists() else ({}, 0)

    # --- Banner ---
    print("\n" + "=" * 70)
    print("🔎 AUDITORIA DOS DOCUMENTOS PROCESSADOS")
    print("=" * 70)
    print(f"   Entrada     : {input_dir}")
    print(f"   Experimentos: {exp_dir}  ({total_exp_files} JSON)")
    print(f"   Arquivos MD : {len(md_files)}")
    print(f"   Saída       : {output_dir}")
    print("=" * 70 + "\n")

    # --- Analisar cada MD ---
    rows: list[dict] = []
    for md_path in md_files:
        ref_count = ref_counts.get(md_path.name, 0)
        logger.info(f"Analisando: {md_path.name}  (refs={ref_count})")
        try:
            row = analyze_md(md_path, ref_count=ref_count)
            rows.append(row)
            print(
                f"  📄 {md_path.name:<50}  "
                f"refs={ref_count:>5}  "
                f"arts={row['artigos_com_heading']:>4}  "
                f"words={row['total_palavras']:>7,}  "
                f"{_quality_badge(row)}"
            )
        except Exception as exc:
            logger.error(f"Erro ao analisar {md_path.name}: {exc}", exc_info=True)

    # --- Salvar CSV ---
    csv_path = output_dir / f"audit_processed_docs_{timestamp}.csv"
    write_csv(rows, csv_path)

    # --- Salvar Markdown ---
    md_out = None
    if not args.no_md:
        md_out = output_dir / f"audit_processed_docs_{timestamp}.md"
        write_md(rows, md_out, generated_at, total_exp_files)

    # --- Sumário final ---
    total_ref    = sum(r["reference_count"] for r in rows)
    total_words  = sum(r["total_palavras"] for r in rows)
    total_arts   = sum(r["artigos_com_heading"] for r in rows)
    total_broken = sum(r["links_quebrados"] for r in rows)
    ok_files     = sum(1 for r in rows if not r["links_quebrados"] and not r["mojibake_residual"])

    print("\n" + "=" * 70)
    print("📊 SUMÁRIO FINAL")
    print("=" * 70)
    print(f"   Arquivos analisados    : {len(rows)}")
    print(f"   Arquivos sem problemas : {ok_files} / {len(rows)}")
    print(f"   Total de artigos       : {total_arts:,}")
    print(f"   Total de palavras      : {total_words:,}")
    print(f"   Total de referências   : {total_ref:,}")
    print(f"   Links quebrados        : {total_broken}")
    print(f"   CSV  → {csv_path}")
    if md_out:
        print(f"   MD   → {md_out}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
