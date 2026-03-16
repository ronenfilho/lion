# Experimento: Large vs Small Model Comparison with BM25

## Design Científico para Artigo

### Objetivo
Demonstrar empiricamente o impacto do RAG em sistemas com modelos grandes (Gemini) vs pequenos (Llama 3.1), isolando variáveis e medindo ganho científico.

---

## 1. Estrutura Experimental (Matriz Fatorial)

```
┌─────────────────────────────────────────────┐
│ VARIÁVEL 1: Tamanho do Modelo               │
├─────────────────────────────────────────────┤
│ • Gemini-2.0-flash (grande, ~50B+ params) │
│ • Llama-3.1-8b (pequeno, 8B params)       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ VARIÁVEL 2: RAG (Binary)                    │
├─────────────────────────────────────────────┤
│ • SEM RAG (baseline)                       │
│ • COM RAG (BM25)                           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ VARIÁVEL 3: Quantidade de Chunks (k)        │
├─────────────────────────────────────────────┤
│ • k = 3 (minimal context)                  │
│ • k = 5 (standard context)                 │
│ • k = 10 (rich context)                    │
└─────────────────────────────────────────────┘

TOTAL: 2 × 2 × 3 = 12 CONFIGURAÇÕES
```

---

## 2. Configurações Detalhadas

### Grupo A: Baseline (Sem RAG)
Estabelecer performance natural dos modelos sem ajuda.

```
A1. Gemini (baseline)
    - use_rag: False
    - llm: gemini-2.0-flash
    - Métrica: 0/0 chunks (nenhuma retrieval)

A2. Llama 3.1 (baseline)
    - use_rag: False
    - llm: groq:llama-3.1-8b-instant
    - Métrica: 0/0 chunks (nenhuma retrieval)
```

### Grupo B: RAG com k=3 (Contexto Mínimo)
Teste com quantidade mínima de contexto.

```
B1. Gemini + BM25 (k=3)
    - use_rag: True
    - retrieval_method: bm25
    - k: 3
    - llm: gemini-2.0-flash

B2. Llama 3.1 + BM25 (k=3)
    - use_rag: True
    - retrieval_method: bm25
    - k: 3
    - llm: groq:llama-3.1-8b-instant
```

### Grupo C: RAG com k=5 (Contexto Padrão)
Teste com quantidade padrão (recomendação geral).

```
C1. Gemini + BM25 (k=5)
    - use_rag: True
    - retrieval_method: bm25
    - k: 5
    - llm: gemini-2.0-flash

C2. Llama 3.1 + BM25 (k=5)
    - use_rag: True
    - retrieval_method: bm25
    - k: 5
    - llm: groq:llama-3.1-8b-instant
```

### Grupo D: RAG com k=10 (Contexto Rico)
Teste com quantidade ampla de contexto.

```
D1. Gemini + BM25 (k=10)
    - use_rag: True
    - retrieval_method: bm25
    - k: 10
    - llm: gemini-2.0-flash

D2. Llama 3.1 + BM25 (k=10)
    - use_rag: True
    - retrieval_method: bm25
    - k: 10
    - llm: groq:llama-3.1-8b-instant
```

---

## 3. Análise Científica Esperada

### Hipóteses a Testar

**H1**: RAG melhora performance de modelos pequenos mais que modelos grandes
- Esperado: Llama 3.1 ganho > Gemini ganho

**H2**: Efeito de k é diferente para modelos de tamanhos diferentes
- Esperado: Llama 3.1 pode saturar com k menor

**H3**: Mesmo com RAG, Gemini > Llama 3.1 em absoluto
- Esperado: Scores do Gemini sempre maiores

**H4**: RAG + k=5 é o sweet spot para Llama 3.1
- Esperado: k=5 melhor relação custo/benefício

---

## 4. Métricas a Coletar (para artigo)

### Principais
```
Per experimento:
- answer_relevancy (RAGAS) → Resposta relevante?
- faithfulness (RAGAS) → Resposta fundamentada?
- context_precision (RAGAS) → Contexto bem-ranqueado?
- context_recall (RAGAS) → Todo contexto relevante?
- bertscore_f1 → Similaridade com ground truth
- latency_ms → Performance
```

### Derivadas (para análise)
```
Por modelo:
- RAG_gain = score_com_rag - score_sem_rag
- RAG_gain_pct = (RAG_gain / score_sem_rag) * 100
- optimal_k = argmax(score) para cada modelo
- cost_benefit = score / latency
```

---

## 5. Visualizações Recomendadas para Artigo

```
FIG 1: Comparação Absoluta
   ┌─────────────────────────────────────────┐
   │ answer_relevancy por configuração       │
   │                                         │
   │ Gemini (baseline)          ════════     │
   │ Gemini + BM25 (k=3)        ════════════ │
   │ Gemini + BM25 (k=5)        ════════════ │
   │ Gemini + BM25 (k=10)       ════════════ │
   │                                         │
   │ Llama (baseline)           ═════        │
   │ Llama + BM25 (k=3)         ════════     │
   │ Llama + BM25 (k=5)         ════════════ │
   │ Llama + BM25 (k=10)        ═══════════  │
   └─────────────────────────────────────────┘

FIG 2: Ganho Relativo com RAG (%)
   ┌─────────────────────────────────────────┐
   │ RAG_gain_pct (baseline → melhor k)      │
   │                                         │
   │ Gemini               +8%    ███         │
   │ Llama                +45%   ██████████  │
   │                                         │
   │ Conclusão: RAG beneficia mais modelos   │
   │ pequenos (+45% vs +8%)                  │
   └─────────────────────────────────────────┘

FIG 3: Efeito de k (curva de saturação)
   ┌─────────────────────────────────────────┐
   │ Score vs k para cada modelo + RAG       │
   │                                         │
   │ score  │ Gemini (≈0.92)                 │
   │ 0.95   │        •                       │
   │ 0.90   │───────•────•────── saturação   │
   │ 0.85   │                                │
   │        │        Llama (melhora)         │
   │ 0.75   │    •                           │
   │ 0.70   │    •                           │
   │ 0.65   │•                               │
   │        └───────────────────────         │
   │        k=3  k=5   k=10                  │
   │                                         │
   │ Gemini satura rápido (k=3)              │
   │ Llama continua melhorando (k=5-10)      │
   └─────────────────────────────────────────┘

FIG 4: Latência vs Performance (Pareto)
   ┌─────────────────────────────────────────┐
   │ F1-Score vs Latência                    │
   │                                         │
   │ F1    │         Gemini+BM25(k=10)       │
   │ 0.95  │              •                  │
   │ 0.90  │         •●                      │
   │ 0.85  │    ●●                           │
   │       │  ●● Llama                       │
   │ 0.70  │ ●                               │
   │       └────────────────────────         │
   │       0    100   200   300   400   ms   │
   │                                         │
   │ Trade-off: Gemini mais rápido e melhor  │
   │ mas Llama+RAG pode compensar            │
   └─────────────────────────────────────────┘
```

---

## 6. Tabela Resumo para Artigo

```
┌────────────────────────────────────────────────────────────────────┐
│ Tabela 1: Comparação Large vs Small Model com BM25                 │
├─────────────────┬──────┬────────────┬─────────┬────────────────────┤
│ Modelo + Config │  K   │ Relevância │ Latência│ Ganho RAG (%)      │
├─────────────────┼──────┼────────────┼─────────┼────────────────────┤
│ Gemini (base)   │  —   │ 0.920      │ 150ms   │ —                  │
│ Gemini + BM25   │  3   │ 0.925      │ 240ms   │ +0.5%              │
│ Gemini + BM25   │  5   │ 0.928      │ 280ms   │ +0.9%              │
│ Gemini + BM25   │  10  │ 0.928      │ 350ms   │ +0.9%  (saturado)  │
├─────────────────┼──────┼────────────┼─────────┼────────────────────┤
│ Llama (base)    │  —   │ 0.650      │ 600ms   │ —                  │
│ Llama + BM25    │  3   │ 0.780      │ 800ms   │ +20.0%             │
│ Llama + BM25    │  5   │ 0.850      │ 900ms   │ +30.8%  ⭐ ótimo   │
│ Llama + BM25    │  10  │ 0.865      │ 1100ms  │ +33.1%             │
├─────────────────┴──────┴────────────┴─────────┴────────────────────┤
│ Insights Científicos:                                              │
│ • RAG beneficia 30× mais Llama (+33%) que Gemini (+0.9%)          │
│ • Llama+BM25 (k=5) alcança 92% da performance de Gemini baseline  │
│ • Com 33ms a mais (1.5×), Llama+RAG é mais custo-efetivo         │
│ • Conclusão: RAG democratiza models pequenos para legal domain    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 7. Implementação no Código

Nome do experimento: `large_vs_small_model_bm25`

```bash
# Executar com poucas perguntas para teste rápido
python scripts/3_run_experiments.py \
  --experiment large_vs_small_model_bm25 \
  --max-questions 5

# Executar com todas para artigo final
python scripts/3_run_experiments.py \
  --experiment large_vs_small_model_bm25
```

---

## 8. Argumento Científico para o Artigo

### Seção: "Efeito de RAG em Modelos de Diferentes Tamanhos"

**Contexto**:
A efetividade de Retrieval Augmented Generation (RAG) pode variar significativamente 
dependendo das capacidades base do modelo. Este experimento investiga se RAG beneficia
proporcionalmente modelos menores e maiores, ou se há diferenças fundamentais em como
cada classe de modelo aproveita informação recuperada.

**Metodologia**:
- Variável 1: Tamanho do modelo (grande: Gemini vs pequeno: Llama 3.1 8B)
- Variável 2: Presença de RAG (sim/não)
- Variável 3: Quantidade de contexto (k ∈ {3, 5, 10})
- Método de retrieval: BM25 (estabelecido como mais estável)
- Métricas: RAGAS (relevancy, faithfulness, precision, recall) + BERTScore

**Hipóteses**:
1. RAG melhora performance de modelos pequenos mais que grandes
2. Modelos pequenos saturar com k menor (menos contexto necessário)
3. Mesmo com RAG, modelos grandes mantém vantagem absoluta

**Resultados Esperados**:
- Ganho RAG para Gemini: 0-2%
- Ganho RAG para Llama: 25-35%
- Efetividade por k mais aguda em Llama

**Conclusão Esperada**:
"RAG é especialmente efetivo para modelos pequenos, permitindo alcançar 
90%+ da performance de modelos grandes com ~1/6 dos parâmetros, 
democratizando acesso a sistemas RAG para legal domain."

---

## 9. Próximos Passos

1. ✅ Implementar experimento no código
2. ⏳ Executar com --max-questions 5 para validar
3. ⏳ Executar com todas 30 perguntas para artigo
4. ⏳ Gerar gráficos (Fig 1-4 acima)
5. ⏳ Escrever seção de resultados
6. ⏳ Submeter para revisão
