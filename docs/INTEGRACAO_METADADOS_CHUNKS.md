---
title: "Integração de Metadados em Scripts de Chunking (1.2 e 1.2c)"
date: "17 de março de 2026"
status: "✅ Concluído"
---

# Integração de Metadados em Scripts de Chunking

## 📋 Resumo Executivo

Implementada integração completa do dicionário `document_metadata.py` nos scripts de chunking 1.2 (artigos) e 1.2c (janelas), garantindo consistência estrutural e enriquecimento de metadados para todo o pipeline de RAG.

## 🎯 Objetivo

Estruturar chunks de legislação com:
- **Prefixo de título completo** no content
- **Metadados centralizados** via `document_metadata.py`
- **Consistência** entre diferentes estratégias de chunking (artigos vs janelas)
- **Facilidade de manutenção** através de fonte única de verdade

## 📁 Arquivos Modificados

### 1. `scripts/document_metadata.py` (NOVO)
Dicionário centralizado com metadados estruturados para 8 documentos.

**Estrutura:**
```python
DOCUMENT_METADATA = {
    "pl-1087-25_Exm-0019-25-MF_doc": {
        "type": "Exposição de Motivos",
        "project_number": "PROJETO DE LEI Nº 1.087, DE 2025",
        "converted_to_law": "Lei nº 15.270, de 2025",
        "full_title": "PROJETO DE LEI Nº 1.087, DE 2025 - Convertido na Lei nº 15.270, de 2025 - Exposição de Motivos",
        "description": "Altera a legislação do IRPF...",
        "ministry": "Ministério da Fazenda",
    },
    "pl-1087-25_processed": {
        "type": "Lei",
        "law_number": "Lei nº 15.270",
        "law_date": "de 26 de novembro de 2025",
        "project_number": "PROJETO DE LEI Nº 1.087, DE 2025",
        "full_title": "Lei nº 15.270, de 26 de novembro de 2025 - Altera a legislação do Imposto sobre a Renda",
        "description": "...",
    },
    # ... mais 6 entradas
}
```

**Funções exportadas:**
- `get_document_metadata(doc_stem)` - Retorna dict com metadados
- `get_document_full_title(doc_stem)` - Retorna título completo
- `is_exposicao_de_motivos(doc_stem)` - Verifica tipo de documento

---

### 2. `scripts/1.2_create_article_chunks.py` (MODIFICADO)

#### Mudanças:
1. **Import de metadados:**
   ```python
   import sys
   sys.path.insert(0, str(Path(__file__).parent))
   from document_metadata import get_document_metadata
   ```

2. **Atualização da dataclass ArticleChunk:**
   ```python
   @dataclass
   class ArticleChunk:
       # ... campos existentes ...
       document_type: str              # Novo
       project_number: Optional[str]   # Novo
       law_number: Optional[str]       # Novo
       law_date: Optional[str]         # Novo
   ```

3. **Enriquecimento em process_document():**
   ```python
   doc_metadata = get_document_metadata(doc_stem)
   doc_type = doc_metadata.get('type', 'Documento')
   project_number = doc_metadata.get('project_number')
   law_number = doc_metadata.get('law_number')
   law_date = doc_metadata.get('law_date')
   ```

4. **Construção de prefixo em _extract_article_chunk():**
   ```python
   title_parts = []
   if project_number:
       title_parts.append(project_number)
   if law_number:
       title_parts.append(f"Convertido na {law_number}")
   title_parts.append(doc_type)
   
   full_title = " - ".join(title_parts)
   enriched_content = f"{full_title}\n\n{article_content}"
   ```

#### Resultado:
- **6 chunks** gerados para PL-1087
- **Exemplo de content:**
  ```
  PROJETO DE LEI Nº 1.087, DE 2025 - Convertido na Lei nº 15.270 - Lei
  
  * Art. 1º
  
  A Lei nº 9.250, de 26 de dezembro de 1995, passa a vigorar com as seguintes alterações...
  ```

---

### 3. `scripts/1.2c_create_window_chunks.py` (MODIFICADO)

#### Mudanças:
1. **Import de metadados** (idêntico ao 1.2)

2. **Integração em process_file():**
   ```python
   doc_metadata = get_document_metadata(doc_name)
   full_title = get_document_full_title(doc_name)
   enriched_content = f"{full_title}\n\n{window_text}"
   ```

3. **Campos enriquecidos em WindowChunk:**
   - `document_type`
   - `project_number`
   - `converted_to_law`

#### Resultado:
- **10 chunks de janela** (400 palavras cada)
- **Exemplo de content:**
  ```
  PROJETO DE LEI Nº 1.087, DE 2025 - Convertido na Lei nº 15.270, de 2025 - Exposição de Motivos
  
  que essa tributação mensal é uma mera antecipação, podendo o beneficiário...
  ```

---

### 4. `scripts/consolidate_chunks.py` (NOVO)

Script para unificar todos os chunks processados em arquivo único.

**Comando:**
```bash
python scripts/consolidate_chunks.py
```

**Saída:** `data/processed/json/legislation/CONSOLIDADO_chunks.json`

**Estatísticas:**
- 1.298 chunks de artigos
- 10 chunks de janelas
- **1.308 chunks totais**

---

## 🔄 Fluxo de Processamento

```
1. document_metadata.py (fonte de verdade)
   ├─ Define metadados centralizados
   └─ Oferece funções de acesso

2. 1.2_create_article_chunks.py
   ├─ Obtém metadados via get_document_metadata()
   ├─ Constrói prefixo com título completo
   ├─ Gera 6 chunks (artigos) com content enriquecido
   └─ Salva: pl-1087-25_processed.json

3. 1.2c_create_window_chunks.py
   ├─ Obtém metadados via get_document_metadata()
   ├─ Constrói prefixo com título completo
   ├─ Gera 10 chunks (janelas) com content enriquecido
   └─ Salva: pl-1087-25_Exm-0019-25-MF_doc_window.json

4. consolidate_chunks.py (opcional)
   ├─ Reúne todos os chunks processados
   └─ Salva: CONSOLIDADO_chunks.json (1.308 chunks)
```

---

## 📊 Exemplo de Chunk (Antes vs Depois)

### Antes (sem integração):
```json
{
  "chunk_id": "pl-1087-25_processed_preambulo_art_1",
  "content": "* Art. 1º\n\nA Lei nº 9.250...",
  "document_type": null,
  "project_number": null,
  "law_number": null
}
```

### Depois (com integração):
```json
{
  "chunk_id": "pl-1087-25_processed_preambulo_art_1",
  "content": "PROJETO DE LEI Nº 1.087, DE 2025 - Convertido na Lei nº 15.270 - Lei\n\n* Art. 1º\n\nA Lei nº 9.250...",
  "document_type": "Lei",
  "project_number": "PROJETO DE LEI Nº 1.087, DE 2025",
  "law_number": "Lei nº 15.270",
  "law_date": "de 26 de novembro de 2025"
}
```

---

## 🚀 Comandos de Execução

### Processar PL-1087 (artigos):
```bash
python scripts/1.2_create_article_chunks.py --file pl-1087-25_processed.md --force
```

### Processar Exposição de Motivos (janelas):
```bash
python scripts/1.2c_create_window_chunks.py --file pl-1087-25_Exm-0019-25-MF_doc.md --window-size 400 --overlap 80
```

### Processar todos os documentos:
```bash
python scripts/1.2_create_article_chunks.py --force
python scripts/1.2c_create_window_chunks.py
python scripts/consolidate_chunks.py
```

---

## ✅ Validação

### Estrutura Consistente (Artigos vs Janelas):
- ✓ Ambos integram metadados via `document_metadata.py`
- ✓ Ambos adicionam prefixo com título completo no content
- ✓ Ambos expõem campos: `document_type`, `project_number`, `law_number`/`converted_to_law`
- ✓ Ambos mantêm referências legais em campo separado

### Cobertura de Documentos:
- ✓ 8 documentos diferentes processados
- ✓ 1.298 chunks de artigos
- ✓ 10 chunks de janelas
- ✓ 100% dos metadados mapeados

---

## 📝 Próximas Etapas

1. **Scripts 1.2b (section-based chunking):** Integração similar de metadados
2. **RAG Pipeline:** Consumir chunks enriquecidos com prefixo
3. **Validação:** Testar impacto de prefixos em qualidade de recuperação
4. **Documentação:** Atualizar arquitetura com fluxo de enriquecimento

---

## 🔗 Referências

- `document_metadata.py` - Dicionário centralizado (7 funções, 8 entradas)
- `1.2_create_article_chunks.py` - 705 linhas (modificado: +50 linhas de integração)
- `1.2c_create_window_chunks.py` - 357 linhas (modificado: +30 linhas de integração)
- `consolidate_chunks.py` - 156 linhas (novo)

---

**Status:** ✅ Implementação Completa | **Data:** 17 de março de 2026
