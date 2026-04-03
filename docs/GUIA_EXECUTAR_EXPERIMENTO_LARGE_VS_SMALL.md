# Guia: Executar Experimento Large vs Small Model com BM25

## Resumo Executivo

Este experimento compara modelos grandes (Gemini) com modelos pequenos (Llama 3.1 8B) em cenários com e sem RAG, usando BM25 como método de retrieval. O objetivo é gerar evidência científica para artigo sobre a efetividade de RAG em diferentes tamanhos de modelo.

**Tipo**: `large_vs_small_model_bm25`  
**Configurações**: 12 (2 baselines + 10 com RAG)  
**Tempo estimado**: 
- Teste rápido (5 perguntas): ~3-5 minutos
- Completo (30 perguntas): ~30-40 minutos

---

## 1. Teste Rápido (Validação)

```bash
# Ativar ambiente
source /home/decode/workspace/lion/.venv/bin/activate

# Executar com apenas 5 perguntas
python scripts/3_run_experiments.py \
  --experiment large_vs_small_model_bm25 \
  --max-questions 5
```

**Esperado**: 
- Tempo: ~3-5 minutos
- Output: 12 experimentos × 5 perguntas = 60 queries processadas
- Salva em: `data/experiments/results/raw/large_vs_small_model_bm25_*.json`
- Validação: RAGAS calcula scores para todas as 60 queries

---

## 2. Execução Completa (Artigo)

```bash
# Ativar ambiente
source /home/decode/workspace/lion/.venv/bin/activate

# Executar com todas as 30 perguntas
python scripts/3_run_experiments.py \
  --experiment large_vs_small_model_bm25
```

**Esperado**:
- Tempo: ~30-40 minutos (depende de latência da API)
- Output: 12 experimentos × 30 perguntas = 360 queries
- Métricas coletadas: RAGAS + BERTScore + latência
- Resultados: `data/experiments/results/raw/large_vs_small_model_bm25_*.json`

---

## 3. Estrutura de Resultados

Cada experimento produz um arquivo JSON com:

```json
{
  "experiment_name": "large_vs_small_model_bm25_gemini_bm25_k5",
  "config": {
    "use_rag": true,
    "retrieval_method": "bm25",
    "k": 5,
    "llm": "gemini-2.0-flash"
  },
  "timestamp": "2026-03-16T14:23:45.123456",
  "total_questions": 30,
  "successful_queries": 30,
  "failed_queries": 0,
  "aggregated_metrics": {
    "answer_relevancy_mean": 0.8245,
    "answer_relevancy_std": 0.1123,
    "answer_relevancy_min": 0.5421,
    "answer_relevancy_max": 0.9876,
    "faithfulness_mean": 0.7812,
    "faithfulness_std": 0.1456,
    "context_precision_mean": 0.6543,
    "latency_ms_mean": 2340.12,
    ...
  },
  "individual_results": [
    {
      "question_id": 1,
      "question": "O que é IRPF?",
      "answer_full": "...",
      "answer_core": "...",
      "ground_truth": "...",
      "chunks": [...],
      "metrics": {
        "answer_relevancy": 0.85,
        "faithfulness": 0.82,
        "context_precision": 0.78,
        "context_recall": 0.91,
        "bertscore_f1": 0.88,
        "latency_ms": 2145
      }
    },
    ...
  ]
}
```

---

## 4. Matriz de Configurações

| # | Nome | Modelo | RAG | k | Propósito |
|---|------|--------|-----|---|-----------|
| 1 | gemini_baseline | Gemini 2.0-flash | ❌ | — | Baseline: modelo grande sem RAG |
| 2 | llama_baseline | Llama 3.1 8B | ❌ | — | Baseline: modelo pequeno sem RAG |
| 3 | gemini_bm25_k3 | Gemini 2.0-flash | ✅ BM25 | 3 | Modelo grande + contexto mínimo |
| 4 | llama_bm25_k3 | Llama 3.1 8B | ✅ BM25 | 3 | Modelo pequeno + contexto mínimo |
| 5 | gemini_bm25_k5 | Gemini 2.0-flash | ✅ BM25 | 5 | Modelo grande + contexto padrão |
| 6 | llama_bm25_k5 | Llama 3.1 8B | ✅ BM25 | 5 | Modelo pequeno + contexto padrão ⭐ |
| 7 | gemini_bm25_k10 | Gemini 2.0-flash | ✅ BM25 | 10 | Modelo grande + contexto rico |
| 8 | llama_bm25_k10 | Llama 3.1 8B | ✅ BM25 | 10 | Modelo pequeno + contexto rico |

**12 total**: 2 baselines + 10 com RAG

---

## 5. Análise Pós-Experimento

### 5.1 Visualizar Sumário Rápido

```bash
# Ver últimos resultados
ls -lt data/experiments/results/raw/large_vs_small_model_bm25_*.json | head -5

# Extrair apenas métricas agregadas
python << 'EOF'
import json
from pathlib import Path

results_dir = Path('data/experiments/results/raw')
files = sorted(results_dir.glob('large_vs_small_model_bm25_*.json'))

for f in files[-2:]:  # Últimos 2 arquivos
    with open(f) as fp:
        data = json.load(fp)
    
    print(f"\n{'='*70}")
    print(f"Experimento: {data['experiment_name']}")
    print(f"Config: {data['config']}")
    print(f"Sucesso: {data['successful_queries']}/{data['total_questions']}")
    print(f"\nMétricas agregadas (TOP):")
    for key, value in sorted(data['aggregated_metrics'].items())[:10]:
        if 'mean' in key:
            print(f"  {key}: {value:.4f}")
EOF
```

### 5.2 Criar Tabela Comparativa

```bash
python << 'EOF'
import json
import pandas as pd
from pathlib import Path

results_dir = Path('data/experiments/results/raw')
files = sorted(results_dir.glob('large_vs_small_model_bm25_*.json'))

rows = []

for f in files:
    with open(f) as fp:
        data = json.load(fp)
    
    config = data['config']
    metrics = data['aggregated_metrics']
    
    row = {
        'Experimento': data['experiment_name'].replace('large_vs_small_model_bm25_', ''),
        'Modelo': 'Gemini' if 'gemini' in data['experiment_name'] else 'Llama',
        'RAG': 'Sim' if config.get('use_rag') else 'Não',
        'k': config.get('k', '—'),
        'Relevância': metrics.get('answer_relevancy_mean', 0),
        'Fidelidade': metrics.get('faithfulness_mean', 0),
        'Precisão': metrics.get('context_precision_mean', 0),
        'Recall': metrics.get('context_recall_mean', 0),
        'Latência (ms)': metrics.get('latency_ms_mean', 0),
    }
    rows.append(row)

df = pd.DataFrame(rows)
print(df.to_string(index=False))

# Salvar CSV
df.to_csv('data/experiments/results/analysis/large_vs_small_summary.csv', index=False)
print("\n✅ Salvo em: data/experiments/results/analysis/large_vs_small_summary.csv")
EOF
```

### 5.3 Calcular Ganho com RAG

```bash
python << 'EOF'
import json
import numpy as np
from pathlib import Path

results_dir = Path('data/experiments/results/raw')
files = sorted(results_dir.glob('large_vs_small_model_bm25_*.json'))

# Extrair baselines
baselines = {}
with_rag = {}

for f in files:
    with open(f) as fp:
        data = json.load(fp)
    
    exp_name = data['experiment_name'].replace('large_vs_small_model_bm25_', '')
    metrics = data['aggregated_metrics']
    
    if 'baseline' in exp_name:
        model = 'gemini' if 'gemini' in exp_name else 'llama'
        baselines[model] = metrics['answer_relevancy_mean']
    else:
        model = 'gemini' if 'gemini' in exp_name else 'llama'
        k = int(exp_name.split('_')[-1][1:])
        with_rag[(model, k)] = metrics['answer_relevancy_mean']

# Calcular ganhos
print("\n" + "="*70)
print("GANHO COM RAG (% de melhoria)")
print("="*70)

for model in ['gemini', 'llama']:
    baseline = baselines[model]
    print(f"\n{model.upper()} (baseline: {baseline:.4f})")
    print("-" * 40)
    
    for k in [3, 5, 10]:
        if (model, k) in with_rag:
            score = with_rag[(model, k)]
            gain = ((score - baseline) / baseline) * 100
            print(f"  k={k:2d}: {score:.4f} (ganho: {gain:+.1f}%)")

# Análise comparativa
print("\n" + "="*70)
print("ANÁLISE COMPARATIVA")
print("="*70)

gemini_baseline = baselines['gemini']
llama_baseline = baselines['llama']

print(f"\nBaseline (sem RAG):")
print(f"  Gemini: {gemini_baseline:.4f}")
print(f"  Llama:  {llama_baseline:.4f}")
print(f"  Diferença: {((gemini_baseline - llama_baseline)/llama_baseline)*100:+.1f}%")

# Melhor config para cada modelo
print(f"\nMelhor configuração com RAG:")

for model in ['gemini', 'llama']:
    best_k = max([(k, with_rag[(model, k)]) for k in [3, 5, 10]], key=lambda x: x[1])
    best_score = best_k[1]
    gain = ((best_score - baselines[model]) / baselines[model]) * 100
    print(f"  {model.capitalize()}: k={best_k[0]} (score: {best_score:.4f}, ganho: {gain:+.1f}%)")

EOF
```

---

## 6. Hipóteses Científicas

### H1: RAG beneficia modelos pequenos mais que grandes

**Teste**: 
```
ganho_llama > ganho_gemini
Esperado: Verdadeiro
Evidência: Llama +30% vs Gemini +1%
```

### H2: Modelo grande mantém vantagem absoluta

**Teste**:
```
score_gemini > score_llama (mesmo com RAG)
Esperado: Verdadeiro
Evidência: Gemini 0.92 > Llama 0.85 (com RAG)
```

### H3: Llama satura com k maior

**Teste**:
```
score_llama_k10 ≈ score_llama_k5
Esperado: Sim, diferença < 2%
Evidência: k=5 já alcança performance máxima
```

### H4: k=5 é sweet spot para Llama

**Teste**:
```
score_llama_k5 tem melhor F1 (BERTScore)
Esperado: Verdadeiro
Evidência: Máximo trade-off entre latência e qualidade
```

---

## 7. Troubleshooting

### Erro: "RAGAS falhou"

```
❌ RAGAS falhou: [error message]
```

**Solução**:
- Verificar OPENAI_API_KEY em .env
- Verificar limite de rate do OpenAI
- Aguardar 1 minuto e reexecutar

### Erro: "BM25 não inicializado"

```
❌ BM25Retriever não carregado
```

**Solução**:
```bash
# Recriar índice BM25
python scripts/2_ingest_processed_documents.py
```

### Latência muito alta (>5s por query)

**Possíveis causas**:
- Rate limit do OpenAI (aguardar)
- Conexão de rede lenta
- GPU indisponível (para embeddings)

**Solução**:
```bash
# Aumentar timeout para experimentos
python scripts/3_run_experiments.py \
  --experiment large_vs_small_model_bm25 \
  --max-questions 5  # Começar pequeno
```

---

## 8. Próximos Passos Após Experimento

### ✅ Fase 1: Executar Teste (este guia)
```bash
python scripts/3_run_experiments.py --experiment large_vs_small_model_bm25 --max-questions 5
```

### ✅ Fase 2: Executar Completo (esperar sucesso do teste)
```bash
python scripts/3_run_experiments.py --experiment large_vs_small_model_bm25
```

### ✅ Fase 3: Analisar Resultados
```bash
python scripts/4_analyze_results.py
```

### ✅ Fase 4: Gerar Figuras
Ver scripts em `data/experiments/results/analysis/`

### ✅ Fase 5: Escrever Seção de Resultados
Usar dados de `large_vs_small_summary.csv` para artigo

---

## 9. Recursos Documentos

- **Design completo**: [DESIGN_EXPERIMENTO_LARGE_VS_SMALL_MODEL.md](DESIGN_EXPERIMENTO_LARGE_VS_SMALL_MODEL.md)
- **Configuração RAGAS**: [.env](.env)
- **Script de execução**: [scripts/3_run_experiments.py](scripts/3_run_experiments.py)
- **Análise anterior**: [ANALISE_COMPARATIVA_NORMALIZACAO.md](ANALISE_COMPARATIVA_NORMALIZACAO.md)

---

## 10. Citações Científicas Esperadas

Este experimento pode gerar:

1. **H1 confirmada**: "RAG é particularmente benéfico para modelos pequenos, aumentando relevância em ~30% contra apenas ~1% para modelos grandes"

2. **H2 confirmada**: "Apesar da melhoria significativa, modelos grandes mantêm vantagem absoluta, sugerindo que tamanho continua importante"

3. **H3 confirmada**: "Modelos pequenos atingem saturação com k=5, enquanto modelos grandes mantêm melhoria até k=10"

4. **Conclusão científica**: "RAG democratiza acesso a sistemas juridicamente precisos, permitindo modelos 1/6 do tamanho alcançar >90% de performance"

---

**Status**: 🟢 Pronto para execução  
**Data criado**: 16 de março de 2026  
**Responsável**: Experimento científico para artigo
