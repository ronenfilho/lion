# Relatório de Análise: model_comparison

**Data:** 16/02/2026 18:00:14

**Experimentos Analisados:** 16

---

## 1. Sumário Executivo


### Bertscore F1

| experiment                                      | config              |     mean |   std |      min |      max |   median |
|:------------------------------------------------|:--------------------|---------:|------:|---------:|---------:|---------:|
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 | 0.645859 |     0 | 0.645859 | 0.645859 | 0.645859 |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          | 0.64548  |     0 | 0.64548  | 0.64548  | 0.64548  |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          | 0.630201 |     0 | 0.630201 | 0.630201 | 0.630201 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          | 0.615843 |     0 | 0.615843 | 0.615843 | 0.615843 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         | 0.61529  |     0 | 0.61529  | 0.61529  | 0.61529  |
| model_comparison_tinyllama                      | dense, k=3          | 0.601641 |     0 | 0.601641 | 0.601641 | 0.601641 |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  | 0.595182 |     0 | 0.595182 | 0.595182 | 0.595182 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  | 0.593792 |     0 | 0.593792 | 0.593792 | 0.593792 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  | 0.592232 |     0 | 0.592232 | 0.592232 | 0.592232 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  | 0.591624 |     0 | 0.591624 | 0.591624 | 0.591624 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           | 0.591568 |     0 | 0.591568 | 0.591568 | 0.591568 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           | 0.5894   |     0 | 0.5894   | 0.5894   | 0.5894   |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 | 0.579317 |     0 | 0.579317 | 0.579317 | 0.579317 |
| model_comparison_tinyllama_few_shot             | dense, k=3          | 0.57687  |     0 | 0.57687  | 0.57687  | 0.57687  |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          | 0.568715 |     0 | 0.568715 | 0.568715 | 0.568715 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | 0.563075 |     0 | 0.563075 | 0.563075 | 0.563075 |



### Latency Ms

| experiment                                      | config              |       mean |   std |        min |        max |     median |
|:------------------------------------------------|:--------------------|-----------:|------:|-----------:|-----------:|-----------:|
| model_comparison_tinyllama_few_shot             | dense, k=3          | 376441     |     0 | 376441     | 376441     | 376441     |
| model_comparison_tinyllama                      | dense, k=3          | 236604     |     0 | 236604     | 236604     | 236604     |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 |   1578.25  |     0 |   1578.25  |   1578.25  |   1578.25  |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |   1223.25  |     0 |   1223.25  |   1223.25  |   1223.25  |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |   1187.89  |     0 |   1187.89  |   1187.89  |   1187.89  |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 |   1179.64  |     0 |   1179.64  |   1179.64  |   1179.64  |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |   1086.94  |     0 |   1086.94  |   1086.94  |   1086.94  |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |   1060.34  |     0 |   1060.34  |   1060.34  |   1060.34  |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |   1045.88  |     0 |   1045.88  |   1045.88  |   1045.88  |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |   1036.71  |     0 |   1036.71  |   1036.71  |   1036.71  |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |    976.918 |     0 |    976.918 |    976.918 |    976.918 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |    960.541 |     0 |    960.541 |    960.541 |    960.541 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |    852.125 |     0 |    852.125 |    852.125 |    852.125 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |    826.928 |     0 |    826.928 |    826.928 |    826.928 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          |    756.678 |     0 |    756.678 |    756.678 |    756.678 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              |    701.259 |     0 |    701.259 |    701.259 |    701.259 |



### Tokens Used

| experiment                                      | config              |   mean |   std |   min |   max |   median |
|:------------------------------------------------|:--------------------|-------:|------:|------:|------:|---------:|
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 |   3661 |     0 |  3661 |  3661 |     3661 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          |   3606 |     0 |  3606 |  3606 |     3606 |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 |   3539 |     0 |  3539 |  3539 |     3539 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |   2459 |     0 |  2459 |  2459 |     2459 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |   2453 |     0 |  2453 |  2453 |     2453 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |   2453 |     0 |  2453 |  2453 |     2453 |
| model_comparison_tinyllama_few_shot             | dense, k=3          |   1880 |     0 |  1880 |  1880 |     1880 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |   1856 |     0 |  1856 |  1856 |     1856 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |   1804 |     0 |  1804 |  1804 |     1804 |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |   1801 |     0 |  1801 |  1801 |     1801 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |   1330 |     0 |  1330 |  1330 |     1330 |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |   1329 |     0 |  1329 |  1329 |     1329 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |   1287 |     0 |  1287 |  1287 |     1287 |
| model_comparison_tinyllama                      | dense, k=3          |   1028 |     0 |  1028 |  1028 |     1028 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |    708 |     0 |   708 |   708 |      708 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              |    347 |     0 |   347 |   347 |      347 |



## 3. Análise por Categoria


### model_comparison_groq_k5_dense_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.568715 |           960.541 |               1287 |



### model_comparison_groq_k5_hybrid_50_50_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.592232 |           1187.89 |               2453 |



### model_comparison_groq_llama_3.1_8b

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.630201 |           976.918 |                708 |



### model_comparison_tinyllama_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |             0.57687 |            376441 |               1880 |



### model_comparison_groq_k3_dense_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |             0.64548 |           1223.25 |               1329 |



### model_comparison_groq_k3_bm25_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |              0.5894 |           852.125 |               1856 |



### model_comparison_groq_k3_hybrid_50_50_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.593792 |           1060.34 |               1804 |



### model_comparison_groq_k3_hybrid_70_30_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.595182 |           1045.88 |               1801 |



### model_comparison_groq_k10_hybrid_70_30_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.579317 |           1179.64 |               3661 |



### model_comparison_groq_k10_hybrid_50_50_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.645859 |           1578.25 |               3539 |



### model_comparison_groq_llama_3.1_8b_baseline

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.563075 |           701.259 |                347 |



### model_comparison_groq_k10_dense_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |             0.61529 |           1036.71 |               1330 |



### model_comparison_groq_k5_bm25_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.591568 |           826.928 |               2459 |



### model_comparison_groq_k5_hybrid_70_30_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.591624 |           1086.94 |               2453 |



### model_comparison_tinyllama

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.601641 |            236604 |               1028 |



### model_comparison_groq_k10_bm25_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.615843 |           756.678 |               3606 |



## 4. Análise de Retrieval


### model_comparison_groq_k5_dense_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 | 0.568715 |                  1 |                       1 |



### model_comparison_groq_k5_hybrid_50_50_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.592232 |           0.818182 |                       1 |



### model_comparison_groq_llama_3.1_8b

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 | 0.630201 |                0.9 |                       1 |



### model_comparison_tinyllama_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 |  0.57687 |               0.05 |                       1 |



### model_comparison_groq_k3_dense_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 |  0.64548 |           0.636364 |                       1 |



### model_comparison_groq_k3_bm25_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            3 |       1 |          100 |   0.5894 |           0.833333 |                       1 |



### model_comparison_groq_k3_hybrid_50_50_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            3 |       1 |          100 | 0.593792 |           0.777778 |                       1 |



### model_comparison_groq_k3_hybrid_70_30_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            3 |       1 |          100 | 0.595182 |                  1 |                       1 |



### model_comparison_groq_k10_hybrid_70_30_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|           10 |       1 |          100 | 0.579317 |                  1 |                0.611111 |



### model_comparison_groq_k10_hybrid_50_50_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|           10 |       1 |          100 | 0.645859 |                  1 |                0.611111 |



### model_comparison_groq_k10_dense_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 |  0.61529 |                0.5 |                       1 |



### model_comparison_groq_k5_bm25_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.591568 |                0.9 |                       1 |



### model_comparison_groq_k5_hybrid_70_30_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.591624 |           0.909091 |                       1 |



### model_comparison_tinyllama

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 | 0.601641 |           0.346154 |                       1 |



### model_comparison_groq_k10_bm25_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|           10 |       1 |          100 | 0.615843 |                  1 |                0.611111 |



## 5. Melhores e Piores Casos


### model_comparison_groq_k5_dense_few_shot


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.5687
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 1


**⚠️ Top 3 Piores:**


1. **Qq001** (outros)
   - Score: 0.5687
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 1


### model_comparison_groq_k5_hybrid_50_50_few_shot


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.5922
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


**⚠️ Top 3 Piores:**


1. **Qq001** (outros)
   - Score: 0.5922
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


## 6. Testes Estatísticos


**Comparação:** model_comparison_groq_k5_dense_few_shot vs model_comparison_groq_k5_hybrid_50_50_few_shot

- Métrica: bertscore_f1
- Média 1: 0.5687 (±0.0000)
- Média 2: 0.5922 (±0.0000)
- t-statistic: nan
- p-value: nan
- **Significativo (p<0.05):** ❌ Não
- Cohen's d: nan (large)



## 7. Conclusões e Recomendações


### Principais Achados


✅ **Melhor BERTScore F1:** model_comparison_groq_k10_hybrid_50_50_few_shot (F1=0.6459)

⚡ **Menor Latência:** model_comparison_groq_llama_3.1_8b_baseline (701ms)

💰 **Mais Eficiente (tokens):** model_comparison_groq_llama_3.1_8b_baseline (347 tokens)


### Recomendações


1. Considerar trade-off entre qualidade (F1) e eficiência (tokens/latência)

2. Analisar qualitativamente os piores casos para identificar padrões de erro

3. Testar configurações adicionais baseadas nos insights deste relatório


---


*Relatório gerado automaticamente em 16/02/2026 às 18:00:14*