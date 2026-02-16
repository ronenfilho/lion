# Melhorias na Conversão HTML para Markdown

## Resumo

Implementadas melhorias significativas no `HTMLExtractor` para gerar documentos Markdown profissionais a partir de HTML legal.

## Funcionalidades Implementadas

### 1. Conversão de Tabelas HTML → Markdown

**Antes:**
- Tabelas eram convertidas apenas para texto plano
- Perda da estrutura tabular
- Difícil leitura dos dados estruturados

**Depois:**
```markdown
| RENDIMENTOS TRIBUTÁVEIS | REDUÇÃO DO IMPOSTO |
| --- | --- |
| até R$ 5.000,00 | até R$ 312,89 |
| de R$ 5.000,01 até R$ 7.350,00 | R$ 978,62 - (0,133145 x...) |
```

**Implementação:**
- Método `_table_to_markdown()`: converte elementos `<table>` para formato pipe
- Detecção automática de cabeçalhos (primeira linha)
- Normalização de colunas (preenche células faltantes)
- Escape de pipes internos com `\|`

### 2. Melhoria no Tratamento de Encoding

**Antes:**
- Caracteres portugueses apareciam como `�`
- Uso de `errors='replace'` degradava o texto

**Depois:**
- Tentativa sequencial de encodings: `utf-8`, `cp1252`, `latin-1`, `iso-8859-1`
- Preservação correta de: `ã`, `ç`, `í`, `ó`, `ú`, `ê`, etc.
- Documento final em UTF-8

### 3. Estruturação Melhorada de Parágrafos

**Antes:**
- Texto corrido sem quebras apropriadas
- Difícil identificar estruturas (§, incisos, alíneas)

**Depois:**
- Parágrafos (`§`) formatados em **negrito**
- Incisos (I, II, III) como listas com `-`
- Alíneas (a, b, c) como listas aninhadas com `  -`
- Quebra de sentenças longas (>300 caracteres)

### 4. Processamento Direto do DOM HTML

**Implementação:**
- Método `_process_html_to_markdown()`: processa DOM mantendo ordem e estrutura
- Detecção inteligente de:
  - Artigos (`Art. 1º`)
  - Parágrafos (`§ único`, `§ 1º`)
  - Capítulos/Seções
  - Incisos romanos (I, II, III, IV, V, etc.)
  - Alíneas (a), b), c))
  - Tabelas (processadas separadamente)

### 5. Prevenção de Duplicação de Conteúdo

**Implementação:**
- `_is_inside_table()`: evita processar elementos dentro de tabelas duas vezes
- `_has_descendant_table()`: previne processar parágrafos que contêm tabelas

## Exemplo de Saída

### Estrutura Geral
```markdown
# Lei nº 15.270

> **Fonte**: L15270.html  
> **Processado em**: 15/02/2026 21:07:47

---

## 📑 Índice

- [Artigo 1º](#artigo-1)
- [Artigo 2º](#artigo-2)
...

---

<details>
<summary>📋 Metadados do Documento</summary>

- **GENERATOR**: Microsoft FrontPage 6.0

</details>

---

## 📖 Texto Completo

### Artigo 1 {#artigo-1}

Esta Lei altera a Lei nº 9.250...

**§ 1º O valor da redução de que trata o caput...**

- I - os ganhos de capital...
- II - os rendimentos recebidos...
  - a) Letra Hipotecária...
  - b) Letra de Crédito Imobiliário...
```

## Arquivos Modificados

- `src/ingestion/extractors/html_extractor.py`
  - `_save_to_markdown()`: reescrito para usar processamento direto do DOM
  - `_process_html_to_markdown()`: novo método para processar HTML sequencialmente
  - `_table_to_markdown()`: novo método para converter tabelas HTML → Markdown
  - `_is_inside_table()`: helper para detectar contexto de tabela
  - `_has_descendant_table()`: helper para detectar tabelas aninhadas

## Resultado

✅ Tabelas convertidas para formato Markdown  
✅ Encoding correto (UTF-8, português brasileiro)  
✅ Quebras de linha apropriadas  
✅ Estrutura legal preservada (§, incisos, alíneas)  
✅ Índice clicável com âncoras  
✅ Formatação profissional e legível

## Testado Com

- **Documento**: `data/raw/L15270.html` (Lei nº 15.270/2025)
- **Resultado**: `data/processed/L15270_processed.md`
- **Tabelas processadas**: 4 tabelas de impostos
- **Artigos**: 18 artigos identificados e indexados
