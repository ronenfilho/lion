# Relatório de Análise: chunk_count

**Data:** 16/02/2026 12:40:11

**Experimentos Analisados:** 3

---

## 1. Sumário Executivo


### Bertscore F1

| experiment      | config              |     mean |   std |      min |      max |   median |
|:----------------|:--------------------|---------:|------:|---------:|---------:|---------:|
| chunk_count_k3  | hybrid, k=3, α=0.7  | 0.638682 |     0 | 0.638682 | 0.638682 | 0.638682 |
| chunk_count_k10 | hybrid, k=10, α=0.7 | 0.623986 |     0 | 0.623986 | 0.623986 | 0.623986 |
| chunk_count_k5  | hybrid, k=5, α=0.7  | 0.591164 |     0 | 0.591164 | 0.591164 | 0.591164 |



### Latency Ms

| experiment      | config              |    mean |   std |     min |     max |   median |
|:----------------|:--------------------|--------:|------:|--------:|--------:|---------:|
| chunk_count_k10 | hybrid, k=10, α=0.7 | 3606.69 |     0 | 3606.69 | 3606.69 |  3606.69 |
| chunk_count_k5  | hybrid, k=5, α=0.7  | 2731.71 |     0 | 2731.71 | 2731.71 |  2731.71 |
| chunk_count_k3  | hybrid, k=3, α=0.7  | 2449.65 |     0 | 2449.65 | 2449.65 |  2449.65 |



### Tokens Used

| experiment      | config              |   mean |   std |   min |   max |   median |
|:----------------|:--------------------|-------:|------:|------:|------:|---------:|
| chunk_count_k10 | hybrid, k=10, α=0.7 |    217 |     0 |   217 |   217 |      217 |
| chunk_count_k5  | hybrid, k=5, α=0.7  |    160 |     0 |   160 |   160 |      160 |
| chunk_count_k3  | hybrid, k=3, α=0.7  |    156 |     0 |   156 |   156 |      156 |



## 3. Análise por Categoria


### chunk_count_k3

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.638682 |           2449.65 |                156 |



### chunk_count_k5

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.591164 |           2731.71 |                160 |



### chunk_count_k10

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.623986 |           3606.69 |                217 |



## 4. Análise de Retrieval


### chunk_count_k3

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            3 |       1 |          100 | 0.638682 |                  1 |                       1 |



### chunk_count_k5

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.591164 |                  1 |                       1 |



### chunk_count_k10

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|           10 |       1 |          100 | 0.623986 |                0.9 |                0.611111 |



## 5. Melhores e Piores Casos


### chunk_count_k3


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.6387
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 3


**⚠️ Top 3 Piores:**


1. **Qq001** (outros)
   - Score: 0.6387
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 3


### chunk_count_k5


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.5912
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


**⚠️ Top 3 Piores:**


1. **Qq001** (outros)
   - Score: 0.5912
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


## 6. Testes Estatísticos


**Comparação:** chunk_count_k3 vs chunk_count_k5

- Métrica: bertscore_f1
- Média 1: 0.6387 (±0.0000)
- Média 2: 0.5912 (±0.0000)
- t-statistic: nan
- p-value: nan
- **Significativo (p<0.05):** ❌ Não
- Cohen's d: nan (large)



## 7. Conclusões e Recomendações


### Principais Achados


✅ **Melhor BERTScore F1:** chunk_count_k3 (F1=0.6387)

⚡ **Menor Latência:** chunk_count_k3 (2450ms)

💰 **Mais Eficiente (tokens):** chunk_count_k3 (156 tokens)


### Recomendações


1. Considerar trade-off entre qualidade (F1) e eficiência (tokens/latência)

2. Analisar qualitativamente os piores casos para identificar padrões de erro

3. Testar configurações adicionais baseadas nos insights deste relatório


---


*Relatório gerado automaticamente em 16/02/2026 às 12:40:11*