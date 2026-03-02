# Relatório de Análise: rag_vs_no_rag

**Data:** 16/02/2026 12:06:49

**Experimentos Analisados:** 3

---

## 1. Sumário Executivo


### Bertscore F1

| experiment                    | config             |     mean |       std |      min |      max |   median |
|:------------------------------|:-------------------|---------:|----------:|---------:|---------:|---------:|
| rag_vs_no_rag_rag_dense       | dense, k=5         | 0.579174 | 0.0531766 | 0.409179 | 0.648391 | 0.597525 |
| rag_vs_no_rag_rag_hybrid      | hybrid, k=5, α=0.7 | 0.577302 | 0.048265  | 0.416439 | 0.6448   | 0.581002 |
| rag_vs_no_rag_no_rag_baseline | No RAG             | 0.560411 | 0.052945  | 0.40297  | 0.677363 | 0.565569 |



### Latency Ms

| experiment                    | config             |    mean |     std |     min |     max |   median |
|:------------------------------|:-------------------|--------:|--------:|--------:|--------:|---------:|
| rag_vs_no_rag_no_rag_baseline | No RAG             | 9089.54 | 1100.23 | 6312.59 | 10608.7 |  9391.77 |
| rag_vs_no_rag_rag_hybrid      | hybrid, k=5, α=0.7 | 7326.2  | 2444.34 | 2725.09 | 10902.6 |  7952.2  |
| rag_vs_no_rag_rag_dense       | dense, k=5         | 7309.3  | 2680.45 | 2447.46 | 10806.3 |  8550.38 |



### Tokens Used

| experiment                    | config             |    mean |     std |   min |   max |   median |
|:------------------------------|:-------------------|--------:|--------:|------:|------:|---------:|
| rag_vs_no_rag_no_rag_baseline | No RAG             | 488.6   | 176.665 |    81 |   869 |      516 |
| rag_vs_no_rag_rag_hybrid      | hybrid, k=5, α=0.7 | 247.367 | 188.724 |    56 |   721 |      164 |
| rag_vs_no_rag_rag_dense       | dense, k=5         | 211.133 | 174.284 |    58 |   704 |      134 |



## 2. Comparação contra Baseline

| experiment               | config             |   bertscore_f1_improvement_% |   latency_ms_improvement_% |   tokens_used_improvement_% |
|:-------------------------|:-------------------|-----------------------------:|---------------------------:|----------------------------:|
| rag_vs_no_rag_rag_hybrid | hybrid, k=5, α=0.7 |                      3.01397 |                   -19.3996 |                    -49.3724 |
| rag_vs_no_rag_rag_dense  | dense, k=5         |                      3.34811 |                   -19.5855 |                    -56.7881 |



## 3. Análise por Categoria


### rag_vs_no_rag_no_rag_baseline

| category    |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:------------|--------:|--------------------:|------------------:|-------------------:|
| outros      |      17 |            0.579916 |           9017.71 |            475.059 |
| prazo       |       6 |            0.545547 |           9184.65 |            450.667 |
| rendimentos |       4 |            0.561246 |           9830.83 |            513.75  |
| aliquota    |       2 |            0.454003 |           8130.21 |            646.5   |
| dependentes |       1 |            0.527477 |           8693.33 |            530     |



### rag_vs_no_rag_rag_hybrid

| category    |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:------------|--------:|--------------------:|------------------:|-------------------:|
| outros      |      17 |            0.582746 |           6867.16 |            228.706 |
| prazo       |       6 |            0.579895 |           6882.09 |            292.667 |
| rendimentos |       4 |            0.599954 |           9796.07 |            196.25  |
| aliquota    |       2 |            0.499692 |           7267.82 |            275     |
| dependentes |       1 |            0.533791 |           8031.91 |            442     |



### rag_vs_no_rag_rag_dense

| category    |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:------------|--------:|--------------------:|------------------:|-------------------:|
| outros      |      17 |            0.585464 |           6998.11 |            237.941 |
| prazo       |       6 |            0.554337 |           6804.91 |            205.333 |
| rendimentos |       4 |            0.628007 |           8925.85 |            114.5   |
| aliquota    |       2 |            0.517077 |           7041.18 |            258.5   |
| dependentes |       1 |            0.550124 |           9696.05 |             82     |



## 4. Análise de Retrieval


### rag_vs_no_rag_rag_hybrid

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |      30 |          100 | 0.577302 |           0.719214 |                0.566852 |



### rag_vs_no_rag_rag_dense

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            0 |       1 |      3.33333 | 0.557315 |         nan        |              nan        |
|            1 |       3 |     10       | 0.614465 |           0.866667 |                0.666667 |
|            2 |       5 |     16.6667  | 0.569564 |           0.793333 |                0.7      |
|            3 |       2 |      6.66667 | 0.577874 |           0.833333 |                0.75     |
|            4 |       3 |     10       | 0.60973  |           0.644258 |                0.666667 |
|            5 |      16 |     53.3333  | 0.57136  |           0.796704 |                0.613194 |



## 5. Melhores e Piores Casos


### rag_vs_no_rag_no_rag_baseline


**🏆 Top 3 Melhores:**


1. **Qq008** (outros)
   - Score: 0.6774
   - Pergunta: Para que não haja a retenção do IRRF sobre os lucros e dividendos apurados até o ano-calendário de 2...
   - Chunks: 0


2. **Qq020** (outros)
   - Score: 0.6438
   - Pergunta: Para que não haja a tributação pelo IRRF sobre os lucros e dividendos apurados até o ano- calendário...
   - Chunks: 0


3. **Qq013** (rendimentos)
   - Score: 0.6212
   - Pergunta: A capitalização de lucros apurados até 31 de dezembro de 2025 deliberada e aprovada em 2025 é tribut...
   - Chunks: 0


**⚠️ Top 3 Piores:**


1. **Qq016** (aliquota)
   - Score: 0.4030
   - Pergunta: Qual a alíquota deve ser utilizada pela pessoa jurídica para efetuar a retenção do IRRF sobre os luc...
   - Chunks: 0


2. **Qq022** (outros)
   - Score: 0.4764
   - Pergunta: No caso de lucros ou dividendos distribuídos para não-residente a tributação do IRRF é afastada se o...
   - Chunks: 0


3. **Qq006** (prazo)
   - Score: 0.4863
   - Pergunta: Qual o prazo para recolhimento do IRRF devido pela pessoa jurídica sobre os lucros e dividendos dist...
   - Chunks: 0


### rag_vs_no_rag_rag_hybrid


**🏆 Top 3 Melhores:**


1. **Qq014** (prazo)
   - Score: 0.6448
   - Pergunta: Após a incorporação dos lucros apurados até 31 de dezembro de 2025 (deliberada e aprovada em 2025), ...
   - Chunks: 5


2. **Qq025** (rendimentos)
   - Score: 0.6413
   - Pergunta: A capitalização de lucros apurados até 31 de dezembro de 2025 deliberada e aprovada em 2025 é tribut...
   - Chunks: 5


3. **Qq009** (outros)
   - Score: 0.6296
   - Pergunta: Para que não haja a retenção do IRRF sobre os lucros e dividendos apurados no ano-calendário de 2025...
   - Chunks: 5


**⚠️ Top 3 Piores:**


1. **Qq016** (aliquota)
   - Score: 0.4164
   - Pergunta: Qual a alíquota deve ser utilizada pela pessoa jurídica para efetuar a retenção do IRRF sobre os luc...
   - Chunks: 5


2. **Qq022** (outros)
   - Score: 0.4867
   - Pergunta: No caso de lucros ou dividendos distribuídos para não-residente a tributação do IRRF é afastada se o...
   - Chunks: 5


3. **Qq006** (prazo)
   - Score: 0.5211
   - Pergunta: Qual o prazo para recolhimento do IRRF devido pela pessoa jurídica sobre os lucros e dividendos dist...
   - Chunks: 5


## 6. Testes Estatísticos


**Comparação:** rag_vs_no_rag_no_rag_baseline vs rag_vs_no_rag_rag_hybrid

- Métrica: bertscore_f1
- Média 1: 0.5604 (±0.0529)
- Média 2: 0.5773 (±0.0483)
- t-statistic: -1.2696
- p-value: 0.2093
- **Significativo (p<0.05):** ❌ Não
- Cohen's d: -0.3278 (small)



## 7. Conclusões e Recomendações


### Principais Achados


✅ **Melhor BERTScore F1:** rag_vs_no_rag_rag_dense (F1=0.5792)

⚡ **Menor Latência:** rag_vs_no_rag_rag_dense (7309ms)

💰 **Mais Eficiente (tokens):** rag_vs_no_rag_rag_dense (211 tokens)


### Recomendações


1. Considerar trade-off entre qualidade (F1) e eficiência (tokens/latência)

2. Analisar qualitativamente os piores casos para identificar padrões de erro

3. Testar configurações adicionais baseadas nos insights deste relatório


---


*Relatório gerado automaticamente em 16/02/2026 às 12:06:49*