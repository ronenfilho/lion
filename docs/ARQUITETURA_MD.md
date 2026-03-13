## Estrutura dos Documentos Markdown



### Hierarquia da Legislação Brasileira (LC 95/98)

Os documentos processados seguem **10 níveis hierárquicos** conforme Lei Complementar 95/98:

#### Estrutura de Headings (Níveis 1-6)

| Nível | Markdown | Elemento | Exemplo |
|-------|----------|----------|---------|
| 1 | `#` | **Título do Decreto/Lei** | `# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018` |
| 2 | `##` | **Preâmbulo/ANEXO** | `## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA` |
| 3 | `###` | **LIVRO** | `### LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS` |
| 4 | `####` | **TÍTULO** | `#### TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS` |
| 5 | `#####` | **CAPÍTULO** | `##### CAPÍTULO I - DOS CONTRIBUINTES` |
| 6 | `######` | **SEÇÃO** | `###### Seção I - Da incidência` |

#### Estrutura de Listas (Níveis 7-10)

| Nível | Markdown | Elemento | Exemplo |
|-------|----------|----------|---------|
| 7 | `*` | **Subtítulo/SUBSEÇÃO/ARTIGO** | `* Disposições gerais`<br>`* **Subseção única**`<br>`  * Art. 677.` |
| 8 | `  -` | **Parágrafo (§)** | `  - **§ 1º** São também contribuintes...` |
| 9 | `    -` | **Inciso** | `    - I - de qualquer um dos pais` |
| 10 | `      -` | **Alínea** | `      - a) rendimentos do trabalho` |

**⚠️ Observação importante**: Artigos aparecem no **nível 7** com indentação especial (`  * Art. X.`) para diferenciá-los de subtítulos (`* Subtítulo`). Subseções são renderizadas em negrito: `* **Subseção I**`.

#### Regras de Combinação de Títulos

O extrator combina automaticamente elementos estruturais vazios consecutivos:

```markdown
# Antes (HTML)
<p>LIVRO III</p>
<p>DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS</p>

# Depois (Markdown)
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
```

**Casos especiais de combinação:**
- `LIVRO/TÍTULO/CAPÍTULO X` + `DA/DO/DAS/DOS ...` → Combinados com hífen
- `Seção I` + `Da incidência` → `###### Seção I - Da incidência`
- `Disposições gerais` → Permanece como subtítulo separado (`* Disposições gerais`)

#### Exemplo Hierárquico Completo

```markdown
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE
##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA
###### Seção I - Da incidência
* Disposições gerais
  * Art. 677.

Os rendimentos de que trata este Capítulo ficam sujeitos à incidência...

  - **§ 1º** O imposto de que trata este artigo será calculado...

    - I - para o ano-calendário de 2010...
    
      - a) até R$ 1.499,15: isento
```

### Estrutura do Arquivo Markdown

Cada documento processado contém três seções principais:

#### 1. Metadados do Documento

Informações sobre o processamento:

```markdown
# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018

<details>
<summary>📋 Metadados do Documento</summary>

- **Arquivo**: `D9580.html`
- **Padrão detectado**: planalto
- **Processado em**: 02/03/2026 18:30
</details>
```

#### 2. Esquema Navegável (Collapsible)

Estrutura hierárquica completa para navegação rápida:

```markdown
<details>
<summary>📋 Esquema da Legislação</summary>

# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018
## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA
## Art. 1º
## Art. 2º
### LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS
#### TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS
##### CAPÍTULO I - DOS CONTRIBUINTES
  * Art. 3º
  * Art. 4º
...
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE
##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA
###### Seção I - Da incidência
* Disposições gerais
  * Art. 677
  * Art. 678
...
</details>
```

**Conteúdo do esquema:**
- ✅ Todos os elementos estruturais (LIVRO, TÍTULO, CAPÍTULO, SEÇÃO, SUBSEÇÃO)
- ✅ Todos os artigos (apenas cabeçalho: `Art. 677`)
- ✅ Subtítulos descritivos (`Disposições gerais`, `Adiantamentos de rendimentos`)
- ❌ Parágrafos (§), incisos e alíneas (aparecem apenas no corpo)

**Utilidade:**
- Navegação rápida da estrutura legislativa
- Identificação de artigos relevantes sem scroll
- Visualização da hierarquia completa em formato compacto

#### 3. Corpo do Documento (Texto Normativo)

Conteúdo completo com toda a hierarquia:

```markdown
---

## 📖 Texto Normativo

## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA

## Art. 1º

Este Decreto regulamenta a tributação...

## Art. 2º

Para fins do disposto neste Decreto...

### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS


#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE


##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA


###### Seção I - Da incidência


* Disposições gerais


  * Art. 677.

Os rendimentos de que trata este Capítulo ficam sujeitos à incidência do imposto sobre a renda na fonte calculado em reais, de acordo com as seguintes tabelas progressivas mensais (Lei nº 11.482, de 2007, art. 1º caput , incisos IV a VIII) :

      - I - para o ano-calendário de 2010 e para os meses de janeiro a março do ano-calendário de 2011:


      - II - para os meses de abril a dezembro do ano-calendário de 2011:


  - **§ 1º** O imposto de que trata este artigo será calculado sobre os rendimentos efetivamente recebidos em cada mês...

    - I - os rendimentos do trabalho assalariado, inclusive adiantamentos...
    
      - a) pagos por pessoa jurídica a outra pessoa jurídica;
```

**Conteúdo do corpo:**
- ✅ Estrutura hierárquica completa (10 níveis)
- ✅ Todo o texto normativo (artigos, parágrafos, incisos, alíneas)
- ✅ Formatação: parágrafos em negrito, indentação progressiva
- ✅ Referências cruzadas preservadas (ex: "art. 587")

### Regras de Renderização

#### Detecção Automática de Elementos

O extrator HTML (`src/ingestion/extractors/html_extractor.py`) aplica heurísticas para identificar elementos sem classe CSS:

```python
# Elementos com classe MsoNormal ou sem classe
if mapping is None or mapping == (0, "", "body"):
    if re.match(r"^\s*Art\.?\s*\d+", text):
        mapping = (6, "###### ", "article")  # Artigo
    elif re.match(r"^\s*LIVRO\s+", text):
        mapping = (1, "# ", "heading")       # LIVRO
    elif re.match(r"^\s*TÍTULO\s+", text):
        mapping = (2, "## ", "heading")      # TÍTULO
    elif re.match(r"^\s*CAPÍTULO\s+", text):
        mapping = (3, "### ", "heading")     # CAPÍTULO
    elif re.match(r"^\s*SEÇÃO\s+", text):
        mapping = (4, "#### ", "heading")    # SEÇÃO
    elif len(text) < 100 and text[0].isupper():
        mapping = (5, "##### ", "heading")   # Subtítulo descritivo
```

#### Combinação Inteligente de Títulos

Elementos estruturais vazios consecutivos são automaticamente combinados:

| Padrão | Resultado |
|--------|-----------|
| `LIVRO I` + `DA TRIBUTAÇÃO...` | `### LIVRO I - DA TRIBUTAÇÃO...` |
| `Seção I` + `Da incidência` | `###### Seção I - Da incidência` |
| `Seção I - Da incidência` + `Disposições gerais` | **Não combina** (mantém separados) |

**Lógica de combinação:**
1. Se `current.title` já contém " - ", só combina `next.title` se começar com `DA/DO/DAS/DOS`
2. Preserva o nível hierárquico do primeiro elemento (`current.level`)
3. Não combina textos descritivos curtos que devem ser subtítulos separados

### Exemplo Completo de Documento Processado

📄 **Arquivo de referência**: [D9580_processed.md](../data/processed/markdown/legislation/D9580_processed.md)

**Estatísticas:**
- **Tamanho**: 196.736 palavras, 24.530 linhas
- **Estrutura**: Decreto nº 9.580/2018 (Regulamento do Imposto de Renda - RIR)
- **Hierarquia**: 10 níveis completos
- **Elementos**: 
  - 3 Livros (LIVRO I, II, III)
  - 14 Títulos
  - 125+ Capítulos
  - 200+ Seções e Subseções
  - 1.500+ Artigos
  - Milhares de parágrafos, incisos e alíneas

**Navegação no esquema** (linhas 1-1400):
```markdown
<details>
<summary>📋 Esquema da Legislação</summary>

# DECRETO Nº 9.580, DE 22 DE NOVEMBRO DE 2018
## ANEXO - REGULAMENTO DO IMPOSTO SOBRE A RENDA
## Art. 1º
...
### LIVRO I - DA TRIBUTAÇÃO DAS PESSOAS FÍSICAS
#### TÍTULO I - DOS CONTRIBUINTES E RESPONSÁVEIS
##### CAPÍTULO I - DOS CONTRIBUINTES
  * Art. 3º
...
### LIVRO III - DA TRIBUTAÇÃO NA FONTE E SOBRE OPERAÇÕES FINANCEIRAS
#### TÍTULO I - DA TRIBUTAÇÃO NA FONTE
##### CAPÍTULO I - DOS RENDIMENTOS SUJEITOS À TABELA PROGRESSIVA
###### Seção I - Da incidência
* Disposições gerais
  * Art. 677
  * Art. 678
  * Art. 679
  * Art. 680
###### Seção II - Dos rendimentos do trabalho
* **Subseção I - Do trabalho assalariado**
* Pagos por pessoa física ou jurídica
  * Art. 681
...
</details>
```

**Corpo do documento** (linhas 1400+):
- Texto normativo completo com todos os 10 níveis hierárquicos
- Formatação preservada: parágrafos em negrito, indentação progressiva
- Referências cruzadas mantidas (ex: "conforme art. 587")
- Citações de leis e decretos preservadas
