# Relatório de Análise: retrieval_strategy

**Data:** 16/02/2026 12:40:02

**Experimentos Analisados:** 4

---

## 1. Sumário Executivo


### Bertscore F1

| experiment                      | config             |     mean |   std |      min |      max |   median |
|:--------------------------------|:-------------------|---------:|------:|---------:|---------:|---------:|
| retrieval_strategy_bm25_only    | bm25, k=5          | 0.621383 |     0 | 0.621383 | 0.621383 | 0.621383 |
| retrieval_strategy_hybrid_70_30 | hybrid, k=5, α=0.7 | 0.613395 |     0 | 0.613395 | 0.613395 | 0.613395 |
| retrieval_strategy_dense_only   | dense, k=5         | 0.612047 |     0 | 0.612047 | 0.612047 | 0.612047 |
| retrieval_strategy_hybrid_50_50 | hybrid, k=5, α=0.5 | 0.592336 |     0 | 0.592336 | 0.592336 | 0.592336 |



### Latency Ms

| experiment                      | config             |    mean |   std |     min |     max |   median |
|:--------------------------------|:-------------------|--------:|------:|--------:|--------:|---------:|
| retrieval_strategy_hybrid_70_30 | hybrid, k=5, α=0.7 | 4834.14 |     0 | 4834.14 | 4834.14 |  4834.14 |
| retrieval_strategy_bm25_only    | bm25, k=5          | 3721.86 |     0 | 3721.86 | 3721.86 |  3721.86 |
| retrieval_strategy_hybrid_50_50 | hybrid, k=5, α=0.5 | 3448.03 |     0 | 3448.03 | 3448.03 |  3448.03 |
| retrieval_strategy_dense_only   | dense, k=5         | 2799.73 |     0 | 2799.73 | 2799.73 |  2799.73 |



### Tokens Used

| experiment                      | config             |   mean |   std |   min |   max |   median |
|:--------------------------------|:-------------------|-------:|------:|------:|------:|---------:|
| retrieval_strategy_hybrid_70_30 | hybrid, k=5, α=0.7 |    252 |     0 |   252 |   252 |      252 |
| retrieval_strategy_hybrid_50_50 | hybrid, k=5, α=0.5 |    214 |     0 |   214 |   214 |      214 |
| retrieval_strategy_bm25_only    | bm25, k=5          |    178 |     0 |   178 |   178 |      178 |
| retrieval_strategy_dense_only   | dense, k=5         |    170 |     0 |   170 |   170 |      170 |



## 3. Análise por Categoria


### retrieval_strategy_dense_only

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.612047 |           2799.73 |                170 |



### retrieval_strategy_hybrid_50_50

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.592336 |           3448.03 |                214 |



### retrieval_strategy_bm25_only

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.621383 |           3721.86 |                178 |



### retrieval_strategy_hybrid_70_30

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.613395 |           4834.14 |                252 |



## 4. Análise de Retrieval


### retrieval_strategy_dense_only

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 | 0.612047 |                0.7 |                       1 |



### retrieval_strategy_hybrid_50_50

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.592336 |                  1 |                       1 |



### retrieval_strategy_bm25_only

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.621383 |              0.875 |                       1 |



### retrieval_strategy_hybrid_70_30

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.613395 |                  1 |                       1 |



## 5. Melhores e Piores Casos


### retrieval_strategy_dense_only


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.6120
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 1


**⚠️ Top 3 Piores:**


1. **Qq001** (outros)
   - Score: 0.6120
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 1


### retrieval_strategy_hybrid_50_50


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.5923
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


**⚠️ Top 3 Piores:**


1. **Qq001** (outros)
   - Score: 0.5923
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


## 6. Testes Estatísticos


**Comparação:** retrieval_strategy_dense_only vs retrieval_strategy_hybrid_50_50

- Métrica: bertscore_f1
- Média 1: 0.6120 (±0.0000)
- Média 2: 0.5923 (±0.0000)
- t-statistic: nan
- p-value: nan
- **Significativo (p<0.05):** ❌ Não
- Cohen's d: nan (large)



## 7. Conclusões e Recomendações


### Principais Achados


✅ **Melhor BERTScore F1:** retrieval_strategy_bm25_only (F1=0.6214)

⚡ **Menor Latência:** retrieval_strategy_dense_only (2800ms)

💰 **Mais Eficiente (tokens):** retrieval_strategy_dense_only (170 tokens)


### Recomendações


1. Considerar trade-off entre qualidade (F1) e eficiência (tokens/latência)

2. Analisar qualitativamente os piores casos para identificar padrões de erro

3. Testar configurações adicionais baseadas nos insights deste relatório


---


*Relatório gerado automaticamente em 16/02/2026 às 12:40:02*