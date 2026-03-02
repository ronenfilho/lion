# Relatório de Análise: model_comparison

**Data:** 16/02/2026 22:37:29

**Experimentos Analisados:** 16

---

## 1. Sumário Executivo


### Bertscore F1

| experiment                                      | config              |     mean |       std |      min |      max |   median |
|:------------------------------------------------|:--------------------|---------:|----------:|---------:|---------:|---------:|
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 | 0.645859 | 0         | 0.645859 | 0.645859 | 0.645859 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          | 0.630201 | 0         | 0.630201 | 0.630201 | 0.630201 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          | 0.615843 | 0         | 0.615843 | 0.615843 | 0.615843 |
| model_comparison_tinyllama                      | dense, k=3          | 0.601641 | 0         | 0.601641 | 0.601641 | 0.601641 |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  | 0.595182 | 0         | 0.595182 | 0.595182 | 0.595182 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  | 0.591624 | 0         | 0.591624 | 0.591624 | 0.591624 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  | 0.590726 | 0.024681  | 0.571669 | 0.62558  | 0.574931 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           | 0.588248 | 0.0380713 | 0.552177 | 0.6409   | 0.571669 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         | 0.583888 | 0.0387571 | 0.540352 | 0.634494 | 0.576819 |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 | 0.579317 | 0         | 0.579317 | 0.579317 | 0.579317 |
| model_comparison_tinyllama_few_shot             | dense, k=3          | 0.57687  | 0         | 0.57687  | 0.57687  | 0.57687  |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          | 0.571244 | 0.022379  | 0.545973 | 0.60038  | 0.567379 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           | 0.568016 | 0.0155933 | 0.545969 | 0.579471 | 0.578607 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | 0.563075 | 0         | 0.563075 | 0.563075 | 0.563075 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  | 0.560777 | 0.0531118 | 0.486088 | 0.60501  | 0.591233 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          | 0.547555 | 0.0245323 | 0.515145 | 0.574482 | 0.553038 |



### Latency Ms

| experiment                                      | config              |       mean |      std |        min |        max |     median |
|:------------------------------------------------|:--------------------|-----------:|---------:|-----------:|-----------:|-----------:|
| model_comparison_tinyllama_few_shot             | dense, k=3          | 376441     |   0      | 376441     | 376441     | 376441     |
| model_comparison_tinyllama                      | dense, k=3          | 236604     |   0      | 236604     | 236604     | 236604     |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 |   1578.25  |   0      |   1578.25  |   1578.25  |   1578.25  |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 |   1179.64  |   0      |   1179.64  |   1179.64  |   1179.64  |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |   1091.19  | 164.228  |    937.41  |   1318.81  |   1017.35  |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |   1090.61  | 191.327  |    820.534 |   1239.89  |   1211.41  |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |   1086.94  |   0      |   1086.94  |   1086.94  |   1086.94  |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |   1045.88  |   0      |   1045.88  |   1045.88  |   1045.88  |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |   1003.98  | 105.631  |    860.628 |   1112.04  |   1039.28  |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |    976.918 |   0      |    976.918 |    976.918 |    976.918 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |    966.939 |  67.6075 |    877.537 |   1040.99  |    982.286 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |    947.131 |  90.1771 |    819.766 |   1016.44  |   1005.19  |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          |    756.678 |   0      |    756.678 |    756.678 |    756.678 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |    712.745 | 145.617  |    510.069 |    845.679 |    782.487 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              |    701.259 |   0      |    701.259 |    701.259 |    701.259 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |    620.043 | 179.537  |    490.429 |    873.928 |    495.771 |



### Tokens Used

| experiment                                      | config              |     mean |      std |   min |   max |   median |
|:------------------------------------------------|:--------------------|---------:|---------:|------:|------:|---------:|
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 | 3661     |   0      |  3661 |  3661 |     3661 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          | 3606     |   0      |  3606 |  3606 |     3606 |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 | 3539     |   0      |  3539 |  3539 |     3539 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  | 2453     |   0      |  2453 |  2453 |     2453 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           | 1928     | 218.844  |  1623 |  2126 |     2035 |
| model_comparison_tinyllama_few_shot             | dense, k=3          | 1880     |   0      |  1880 |  1880 |     1880 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  | 1867.67  | 198.468  |  1590 |  2042 |     1971 |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  | 1801     |   0      |  1801 |  1801 |     1801 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  | 1320.33  | 222.873  |  1057 |  1602 |     1302 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           | 1260.67  | 201.439  |  1057 |  1535 |     1190 |
| model_comparison_tinyllama                      | dense, k=3          | 1028     |   0      |  1028 |  1028 |     1028 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |  829     |  17.6824 |   804 |   842 |      841 |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |  818.667 |  21.4838 |   795 |   847 |      814 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |  814.667 |  30.4448 |   775 |   849 |      820 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |  708     |   0      |   708 |   708 |      708 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              |  347     |   0      |   347 |   347 |      347 |



## 3. Análise por Categoria


### model_comparison_groq_k5_dense_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       2 |            0.56376  |          1011.64  |              841.5 |
| prazo      |       1 |            0.515145 |           877.537 |              804   |



### model_comparison_groq_k5_hybrid_50_50_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       2 |            0.598122 |          1225.65  |             2006.5 |
| prazo      |       1 |            0.486088 |           820.534 |             1590   |



### model_comparison_groq_k10_hybrid_70_30_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.579317 |           1179.64 |               3661 |



### model_comparison_groq_llama_3.1_8b

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.630201 |           976.918 |                708 |



### model_comparison_groq_llama_3.1_8b_baseline

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.563075 |           701.259 |                347 |



### model_comparison_groq_k3_hybrid_70_30_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.595182 |           1045.88 |               1801 |



### model_comparison_tinyllama_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |             0.57687 |            376441 |               1880 |



### model_comparison_groq_k3_hybrid_50_50_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       2 |            0.600255 |           1168.08 |               1452 |
| prazo      |       1 |            0.571669 |            937.41 |               1057 |



### model_comparison_groq_k3_dense_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       2 |            0.58388  |          1075.66  |                821 |
| prazo      |       1 |            0.545973 |           860.628 |                814 |



### model_comparison_groq_k3_bm25_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       2 |            0.596538 |           684.85  |             1362.5 |
| prazo      |       1 |            0.571669 |           490.429 |             1057   |



### model_comparison_groq_k10_hybrid_50_50_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.645859 |           1578.25 |               3539 |



### model_comparison_groq_k5_hybrid_70_30_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.591624 |           1086.94 |               2453 |



### model_comparison_groq_k10_dense_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       2 |            0.605656 |          1010.81  |                812 |
| prazo      |       1 |            0.540352 |           819.766 |                820 |



### model_comparison_groq_k10_bm25_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.615843 |           756.678 |               3606 |



### model_comparison_groq_k5_bm25_few_shot

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       2 |            0.579039 |           814.083 |             2080.5 |
| prazo      |       1 |            0.545969 |           510.069 |             1623   |



### model_comparison_tinyllama

| category   |   count |   bertscore_f1_mean |   latency_ms_mean |   tokens_used_mean |
|:-----------|--------:|--------------------:|------------------:|-------------------:|
| outros     |       1 |            0.601641 |            236604 |               1028 |



## 4. Análise de Retrieval


### model_comparison_groq_k5_dense_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       2 |      66.6667 | 0.56376  |             0.7875 |                     1   |
|            2 |       1 |      33.3333 | 0.515145 |             1      |                     0.5 |



### model_comparison_groq_k5_hybrid_50_50_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       3 |          100 | 0.560777 |           0.918561 |                0.577778 |



### model_comparison_groq_k10_hybrid_70_30_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|           10 |       1 |          100 | 0.579317 |                  1 |                0.611111 |



### model_comparison_groq_llama_3.1_8b

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 | 0.630201 |                0.9 |                       1 |



### model_comparison_groq_k3_hybrid_70_30_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            3 |       1 |          100 | 0.595182 |                  1 |                       1 |



### model_comparison_tinyllama_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 |  0.57687 |               0.05 |                       1 |



### model_comparison_groq_k3_hybrid_50_50_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            3 |       3 |          100 | 0.590726 |           0.891975 |                0.833333 |



### model_comparison_groq_k3_dense_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       2 |      66.6667 | 0.58388  |                  1 |                     1   |
|            2 |       1 |      33.3333 | 0.545973 |                  1 |                     0.5 |



### model_comparison_groq_k3_bm25_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            3 |       3 |          100 | 0.588248 |           0.944444 |                       1 |



### model_comparison_groq_k10_hybrid_50_50_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|           10 |       1 |          100 | 0.645859 |                  1 |                0.611111 |



### model_comparison_groq_k5_hybrid_70_30_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       1 |          100 | 0.591624 |           0.909091 |                       1 |



### model_comparison_groq_k10_dense_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       2 |      66.6667 | 0.605656 |                0.9 |                     1   |
|            2 |       1 |      33.3333 | 0.540352 |                1   |                     0.5 |



### model_comparison_groq_k10_bm25_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|           10 |       1 |          100 | 0.615843 |                  1 |                0.611111 |



### model_comparison_groq_k5_bm25_few_shot

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            5 |       3 |          100 | 0.568016 |           0.826797 |                     0.8 |



### model_comparison_tinyllama

|   num_chunks |   count |   percentage |   avg_f1 |   avg_faithfulness |   avg_context_precision |
|-------------:|--------:|-------------:|---------:|-------------------:|------------------------:|
|            1 |       1 |          100 | 0.601641 |           0.346154 |                       1 |



## 5. Melhores e Piores Casos


### model_comparison_groq_k5_dense_few_shot


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.5745
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 1


2. **Qq002** (outros)
   - Score: 0.5530
   - Pergunta: Quais os principais elementos contidos na Lei nº 15.270, de 2025?...
   - Chunks: 1


3. **Qq003** (prazo)
   - Score: 0.5151
   - Pergunta: A partir de qual data a Lei nº 15.270, de 2025, deve ser aplicada?...
   - Chunks: 2


**⚠️ Top 3 Piores:**


1. **Qq003** (prazo)
   - Score: 0.5151
   - Pergunta: A partir de qual data a Lei nº 15.270, de 2025, deve ser aplicada?...
   - Chunks: 2


2. **Qq002** (outros)
   - Score: 0.5530
   - Pergunta: Quais os principais elementos contidos na Lei nº 15.270, de 2025?...
   - Chunks: 1


3. **Qq001** (outros)
   - Score: 0.5745
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 1


### model_comparison_groq_k5_hybrid_50_50_few_shot


**🏆 Top 3 Melhores:**


1. **Qq001** (outros)
   - Score: 0.6050
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


2. **Qq002** (outros)
   - Score: 0.5912
   - Pergunta: Quais os principais elementos contidos na Lei nº 15.270, de 2025?...
   - Chunks: 5


3. **Qq003** (prazo)
   - Score: 0.4861
   - Pergunta: A partir de qual data a Lei nº 15.270, de 2025, deve ser aplicada?...
   - Chunks: 5


**⚠️ Top 3 Piores:**


1. **Qq003** (prazo)
   - Score: 0.4861
   - Pergunta: A partir de qual data a Lei nº 15.270, de 2025, deve ser aplicada?...
   - Chunks: 5


2. **Qq002** (outros)
   - Score: 0.5912
   - Pergunta: Quais os principais elementos contidos na Lei nº 15.270, de 2025?...
   - Chunks: 5


3. **Qq001** (outros)
   - Score: 0.6050
   - Pergunta: Quais os objetivos da Lei nº 15.270, de 2025?...
   - Chunks: 5


## 6. Testes Estatísticos


**Comparação:** model_comparison_groq_k5_dense_few_shot vs model_comparison_groq_k5_hybrid_50_50_few_shot

- Métrica: bertscore_f1
- Média 1: 0.5476 (±0.0245)
- Média 2: 0.5608 (±0.0531)
- t-statistic: -0.3196
- p-value: 0.7653
- **Significativo (p<0.05):** ❌ Não
- Cohen's d: -0.2610 (small)



## 7. Conclusões e Recomendações


### Principais Achados


✅ **Melhor BERTScore F1:** model_comparison_groq_k10_hybrid_50_50_few_shot (F1=0.6459)

⚡ **Menor Latência:** model_comparison_groq_k3_bm25_few_shot (620ms)

💰 **Mais Eficiente (tokens):** model_comparison_groq_llama_3.1_8b_baseline (347 tokens)


### Recomendações


1. Considerar trade-off entre qualidade (F1) e eficiência (tokens/latência)

2. Analisar qualitativamente os piores casos para identificar padrões de erro

3. Testar configurações adicionais baseadas nos insights deste relatório


---


*Relatório gerado automaticamente em 16/02/2026 às 22:37:29*