# Estrutura de Resultados de Experimentos

## Novo Sistema de Organização (Run ID)

A partir da versão atualizada, todos os experimentos são organizados por **Run ID** (timestamp de execução), facilitando o agrupamento de experimentos da mesma rodada.

---

## Estrutura de Pastas

```
data/experiments/results/
├── raw/
│   ├── 20260316_133906/              ← RUN ID (timestamp da execução)
│   │   ├── large_vs_small_model_bm25_gemini_baseline.json
│   │   ├── large_vs_small_model_bm25_gemini_bm25_k3.json
│   │   ├── large_vs_small_model_bm25_gemini_bm25_k5.json
│   │   ├── large_vs_small_model_bm25_gemini_bm25_k10.json
│   │   ├── large_vs_small_model_bm25_llama_baseline.json
│   │   ├── large_vs_small_model_bm25_llama_bm25_k3.json
│   │   ├── large_vs_small_model_bm25_llama_bm25_k5.json
│   │   ├── large_vs_small_model_bm25_llama_bm25_k10.json
│   │   └── large_vs_small_model_bm25_summary.json  ← Sumário da rodada
│   │
│   └── 20260316_150230/              ← Outra rodada de experimentos
│       ├── large_vs_small_model_bm25_gemini_baseline.json
│       ├── large_vs_small_model_bm25_llama_baseline.json
│       └── ...
│
└── analysis/
    ├── comparacao_rodadas.csv
    ├── graficos/
    └── ...
```

---

## Formato de Run ID

**Formato**: `YYYYMMDD_HHMMSS`

**Exemplo**: `20260316_133906`

- **YYYYMMDD**: Data da execução (2026-03-16)
- **HHMMSS**: Hora da execução (13:39:06)

**Vantagem**: Cada rodada de experimentos tem seu próprio ID único que:
- ✅ Agrupa automaticamente todos os experimentos da mesma execução
- ✅ Permite executar múltiplos tipos de experimentos na mesma pasta
- ✅ Facilita comparação entre rodadas diferentes
- ✅ Simplifica versionamento e reprodutibilidade

---

## Conteúdo dos Arquivos

### 1. Arquivo Individual (ex: `large_vs_small_model_bm25_gemini_baseline.json`)

```json
{
  "experiment_name": "large_vs_small_model_bm25_gemini_baseline",
  "run_id": "20260316_133906",
  "config": {
    "use_rag": false,
    "llm": "gemini-2.5-flash-lite"
  },
  "timestamp": "2026-03-16T13:39:06.123456",
  "total_questions": 30,
  "successful_queries": 30,
  "failed_queries": 0,
  "aggregated_metrics": {
    "answer_relevancy_mean": 0.8245,
    "answer_relevancy_std": 0.1123,
    "faithfulness_mean": 0.7812,
    "latency_ms_mean": 1250.45,
    ...
  },
  "individual_results": [
    {
      "question_id": "q001",
      "question": "O que é IRPF?",
      "answer_core": "...",
      "metrics": {
        "answer_relevancy": 0.85,
        "faithfulness": 0.82,
        "bertscore_f1": 0.88,
        "latency_ms": 1200
      }
    },
    ...
  ]
}
```

### 2. Arquivo de Sumário (`large_vs_small_model_bm25_summary.json`)

```json
{
  "experiment_type": "large_vs_small_model_bm25",
  "run_id": "20260316_133906",
  "timestamp": "2026-03-16T13:39:45.654321",
  "total_experiments": 8,
  "experiments": [
    {
      "name": "large_vs_small_model_bm25_gemini_baseline",
      "config": {
        "use_rag": false,
        "llm": "gemini-2.5-flash-lite"
      },
      "metrics": {
        "answer_relevancy_mean": 0.8245,
        "latency_ms_mean": 1250.45
      }
    },
    ...
  ]
}
```

---

## Executar Experimentos

### Teste Rápido (1 pergunta)

```bash
python scripts/3_run_experiments.py --experiment large_vs_small_model_bm25 --max-questions 1
```

**Output**: Cria pasta com ID gerado automaticamente:
```
data/experiments/results/raw/20260316_133906/
```

### Execução Completa (30 perguntas)

```bash
python scripts/3_run_experiments.py --experiment large_vs_small_model_bm25
```

---

## Análise de Resultados

### Listar todas as rodadas

```bash
ls -lh data/experiments/results/raw/
```

**Output**:
```
drwxrwxr-x 2 decode decode 4096 mar 16 13:39 20260316_133906/
drwxrwxr-x 2 decode decode 4096 mar 16 15:02 20260316_150230/
```

### Ver arquivos de uma rodada específica

```bash
ls data/experiments/results/raw/20260316_133906/
```

### Comparar duas rodadas

```python
import json
from pathlib import Path

run1 = Path('data/experiments/results/raw/20260316_133906')
run2 = Path('data/experiments/results/raw/20260316_150230')

# Carregar sumários
with open(run1 / 'large_vs_small_model_bm25_summary.json') as f:
    summary1 = json.load(f)

with open(run2 / 'large_vs_small_model_bm25_summary.json') as f:
    summary2 = json.load(f)

# Comparar métricas
for exp1, exp2 in zip(summary1['experiments'], summary2['experiments']):
    print(f"{exp1['name']}")
    print(f"  Rodada 1: {exp1['metrics']['answer_relevancy_mean']:.4f}")
    print(f"  Rodada 2: {exp2['metrics']['answer_relevancy_mean']:.4f}")
    print()
```

---

## Vantagens da Nova Estrutura

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Organização | Nomes com timestamp duplicado | Run ID agrupa tudo |
| Nomes | `exp_20260316_133906.json` | `exp.json` (simples) |
| Comparação | Difícil comparar rodadas | Fácil (diretórios separados) |
| Escalabilidade | Centenas de arquivos | Organizado por rodada |
| Reprodutibilidade | Difícil rastrear | Run ID identifica tudo |

---

## Próximas Rodadas

Cada execução cria uma nova pasta com seu Run ID:

```
20260316_133906/  ← Primeira rodada (1 pergunta)
20260316_135000/  ← Segunda rodada (5 perguntas)
20260316_150000/  ← Terceira rodada (30 perguntas - completa)
```

Todos os arquivos dentro da mesma pasta pertencem à **mesma execução**.

---

**Data**: 16 de março de 2026  
**Status**: ✅ Implementado e testado
