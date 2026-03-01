# Relatório de Análise: model_comparison

**Data:** 16/02/2026 22:49:54

**Experimentos Analisados:** 16


**Total de Questões Testadas:** 3

**Configurações Comparadas:** 16

**Total de Execuções:** 30

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



### Bertscore Precision

| experiment                                      | config              |     mean |       std |      min |      max |   median |
|:------------------------------------------------|:--------------------|---------:|----------:|---------:|---------:|---------:|
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 | 0.640215 | 0         | 0.640215 | 0.640215 | 0.640215 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          | 0.616256 | 0         | 0.616256 | 0.616256 | 0.616256 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          | 0.600401 | 0         | 0.600401 | 0.600401 | 0.600401 |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  | 0.588216 | 0         | 0.588216 | 0.588216 | 0.588216 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  | 0.582642 | 0.0295114 | 0.547197 | 0.619446 | 0.581283 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         | 0.581502 | 0.0182715 | 0.560444 | 0.605    | 0.579061 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           | 0.580993 | 0.0523831 | 0.510229 | 0.635356 | 0.597395 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  | 0.574949 | 0.0384219 | 0.520871 | 0.60658  | 0.597395 |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          | 0.572489 | 0.024344  | 0.53873  | 0.595216 | 0.583521 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  | 0.571236 | 0         | 0.571236 | 0.571236 | 0.571236 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           | 0.56229  | 0.0294899 | 0.532674 | 0.602527 | 0.551667 |
| model_comparison_tinyllama                      | dense, k=3          | 0.560815 | 0         | 0.560815 | 0.560815 | 0.560815 |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 | 0.554835 | 0         | 0.554835 | 0.554835 | 0.554835 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          | 0.551883 | 0.0182425 | 0.527166 | 0.570643 | 0.557839 |
| model_comparison_tinyllama_few_shot             | dense, k=3          | 0.540314 | 0         | 0.540314 | 0.540314 | 0.540314 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | 0.530026 | 0         | 0.530026 | 0.530026 | 0.530026 |



### Bertscore Recall

| experiment                                      | config              |     mean |       std |      min |      max |   median |
|:------------------------------------------------|:--------------------|---------:|----------:|---------:|---------:|---------:|
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 | 0.651605 | 0         | 0.651605 | 0.651605 | 0.651605 |
| model_comparison_tinyllama                      | dense, k=3          | 0.648878 | 0         | 0.648878 | 0.648878 | 0.648878 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          | 0.644791 | 0         | 0.644791 | 0.644791 | 0.644791 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          | 0.632101 | 0         | 0.632101 | 0.632101 | 0.632101 |
| model_comparison_tinyllama_few_shot             | dense, k=3          | 0.618732 | 0         | 0.618732 | 0.618732 | 0.618732 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  | 0.613522 | 0         | 0.613522 | 0.613522 | 0.613522 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  | 0.611795 | 0.0450969 | 0.548067 | 0.645808 | 0.641511 |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 | 0.60606  | 0         | 0.60606  | 0.60606  | 0.60606  |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  | 0.602314 | 0         | 0.602314 | 0.602314 | 0.602314 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | 0.60052  | 0         | 0.60052  | 0.60052  | 0.60052  |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           | 0.59875  | 0.0402542 | 0.548067 | 0.646542 | 0.60164  |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         | 0.589228 | 0.0656243 | 0.506494 | 0.667011 | 0.594179 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           | 0.580851 | 0.0585509 | 0.499118 | 0.63321  | 0.610226 |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          | 0.573915 | 0.0498629 | 0.504256 | 0.618242 | 0.599246 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  | 0.557904 | 0.111782  | 0.399978 | 0.642977 | 0.630757 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          | 0.547738 | 0.0555009 | 0.469485 | 0.592148 | 0.58158  |



### Answer Relevancy

| experiment                                      | config              |       mean |          std |        min |        max |     median |
|:------------------------------------------------|:--------------------|-----------:|-------------:|-----------:|-----------:|-----------:|
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |   0.897363 |   0          |   0.897363 |   0.897363 |   0.897363 |
| model_comparison_tinyllama_few_shot             | dense, k=3          |   0.897363 |   0          |   0.897363 |   0.897363 |   0.897363 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |   0.897363 |   0          |   0.897363 |   0.897363 |   0.897363 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          |   0.897363 |   0          |   0.897363 |   0.897363 |   0.897363 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |   0.88778  |   0.00616651 |   0.880815 |   0.895807 |   0.886716 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |   0.873748 |   0.0210592  |   0.851654 |   0.90209  |   0.867498 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |   0.871891 |   0          |   0.871891 |   0.871891 |   0.871891 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |   0.867547 |   0.00400186 |   0.862653 |   0.872455 |   0.867532 |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 |   0.865001 |   0          |   0.865001 |   0.865001 |   0.865001 |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 |   0.865001 |   0          |   0.865001 |   0.865001 |   0.865001 |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |   0.860062 |   0.00994606 |   0.84633  |   0.869566 |   0.864289 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |   0.844028 |   0.0181893  |   0.828585 |   0.869566 |   0.833934 |
| model_comparison_tinyllama                      | dense, k=3          |   0.839745 |   0          |   0.839745 |   0.839745 |   0.839745 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |   0.830797 |   0.0644306  |   0.740645 |   0.887336 |   0.86441  |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |   0.528922 |   0.379142   |   0        |   0.869566 |   0.7172   |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | nan        | nan          | nan        | nan        | nan        |



### Faithfulness

| experiment                                      | config              |       mean |         std |        min |        max |     median |
|:------------------------------------------------|:--------------------|-----------:|------------:|-----------:|-----------:|-----------:|
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 |   1        |   0         |   1        |   1        |   1        |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |   1        |   0         |   1        |   1        |   1        |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |   1        |   0         |   1        |   1        |   1        |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 |   1        |   0         |   1        |   1        |   1        |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          |   1        |   0         |   1        |   1        |   1        |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |   0.944444 |   0.0785674 |   0.833333 |   1        |   1        |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |   0.933333 |   0.0942809 |   0.8      |   1        |   1        |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |   0.918561 |   0.0754254 |   0.818182 |   1        |   0.9375   |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |   0.909091 |   0         |   0.909091 |   0.909091 |   0.909091 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |   0.9      |   0         |   0.9      |   0.9      |   0.9      |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |   0.891975 |   0.104847  |   0.75     |   1        |   0.925926 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |   0.858333 |   0.12304   |   0.7      |   1        |   0.875    |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |   0.826797 |   0.144162  |   0.647059 |   1        |   0.833333 |
| model_comparison_tinyllama                      | dense, k=3          |   0.346154 |   0         |   0.346154 |   0.346154 |   0.346154 |
| model_comparison_tinyllama_few_shot             | dense, k=3          |   0.05     |   0         |   0.05     |   0.05     |   0.05     |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | nan        | nan         | nan        | nan        | nan        |



### Context Precision

| experiment                                      | config              |       mean |        std |        min |        max |     median |
|:------------------------------------------------|:--------------------|-----------:|-----------:|-----------:|-----------:|-----------:|
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |   1        |   0        |   1        |   1        |   1        |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |   1        |   0        |   1        |   1        |   1        |
| model_comparison_tinyllama_few_shot             | dense, k=3          |   1        |   0        |   1        |   1        |   1        |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |   1        |   0        |   1        |   1        |   1        |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |   1        |   0        |   1        |   1        |   1        |
| model_comparison_tinyllama                      | dense, k=3          |   1        |   0        |   1        |   1        |   1        |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |   0.833333 |   0.235702 |   0.5      |   1        |   1        |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |   0.833333 |   0.235702 |   0.5      |   1        |   1        |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |   0.833333 |   0.235702 |   0.5      |   1        |   1        |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |   0.833333 |   0.235702 |   0.5      |   1        |   1        |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |   0.8      |   0.141421 |   0.7      |   1        |   0.7      |
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 |   0.611111 |   0        |   0.611111 |   0.611111 |   0.611111 |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 |   0.611111 |   0        |   0.611111 |   0.611111 |   0.611111 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          |   0.611111 |   0        |   0.611111 |   0.611111 |   0.611111 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |   0.577778 |   0.328107 |   0.2      |   1        |   0.533333 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | nan        | nan        | nan        | nan        | nan        |



### Context Recall

| experiment                                      | config              |       mean |        std |        min |        max |     median |
|:------------------------------------------------|:--------------------|-----------:|-----------:|-----------:|-----------:|-----------:|
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 |   0.333333 |   0        |   0.333333 |   0.333333 |   0.333333 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |   0.333333 |   0        |   0.333333 |   0.333333 |   0.333333 |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |   0.333333 |   0        |   0.333333 |   0.333333 |   0.333333 |
| model_comparison_tinyllama_few_shot             | dense, k=3          |   0.333333 |   0        |   0.333333 |   0.333333 |   0.333333 |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 |   0.333333 |   0        |   0.333333 |   0.333333 |   0.333333 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          |   0.333333 |   0        |   0.333333 |   0.333333 |   0.333333 |
| model_comparison_tinyllama                      | dense, k=3          |   0.333333 |   0        |   0.333333 |   0.333333 |   0.333333 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |   0.222222 |   0.157135 |   0        |   0.333333 |   0.333333 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |   0.222222 |   0.157135 |   0        |   0.333333 |   0.333333 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |   0.222222 |   0.157135 |   0        |   0.333333 |   0.333333 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |   0.111111 |   0.157135 |   0        |   0.333333 |   0        |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |   0.111111 |   0.157135 |   0        |   0.333333 |   0        |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |   0.111111 |   0.157135 |   0        |   0.333333 |   0        |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |   0.111111 |   0.157135 |   0        |   0.333333 |   0        |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |   0        |   0        |   0        |   0        |   0        |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              | nan        | nan        | nan        | nan        | nan        |



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



### Num Chunks

| experiment                                      | config              |     mean |      std |   min |   max |   median |
|:------------------------------------------------|:--------------------|---------:|---------:|------:|------:|---------:|
| model_comparison_groq_k10_hybrid_70_30_few_shot | hybrid, k=10, α=0.7 | 10       | 0        |    10 |    10 |       10 |
| model_comparison_groq_k10_hybrid_50_50_few_shot | hybrid, k=10, α=0.5 | 10       | 0        |    10 |    10 |       10 |
| model_comparison_groq_k10_bm25_few_shot         | bm25, k=10          | 10       | 0        |    10 |    10 |       10 |
| model_comparison_groq_k5_hybrid_50_50_few_shot  | hybrid, k=5, α=0.5  |  5       | 0        |     5 |     5 |        5 |
| model_comparison_groq_k5_hybrid_70_30_few_shot  | hybrid, k=5, α=0.7  |  5       | 0        |     5 |     5 |        5 |
| model_comparison_groq_k5_bm25_few_shot          | bm25, k=5           |  5       | 0        |     5 |     5 |        5 |
| model_comparison_groq_k3_hybrid_70_30_few_shot  | hybrid, k=3, α=0.7  |  3       | 0        |     3 |     3 |        3 |
| model_comparison_groq_k3_hybrid_50_50_few_shot  | hybrid, k=3, α=0.5  |  3       | 0        |     3 |     3 |        3 |
| model_comparison_groq_k3_bm25_few_shot          | bm25, k=3           |  3       | 0        |     3 |     3 |        3 |
| model_comparison_groq_k5_dense_few_shot         | dense, k=5          |  1.33333 | 0.471405 |     1 |     2 |        1 |
| model_comparison_groq_k3_dense_few_shot         | dense, k=3          |  1.33333 | 0.471405 |     1 |     2 |        1 |
| model_comparison_groq_k10_dense_few_shot        | dense, k=10         |  1.33333 | 0.471405 |     1 |     2 |        1 |
| model_comparison_groq_llama_3.1_8b              | dense, k=3          |  1       | 0        |     1 |     1 |        1 |
| model_comparison_tinyllama_few_shot             | dense, k=3          |  1       | 0        |     1 |     1 |        1 |
| model_comparison_tinyllama                      | dense, k=3          |  1       | 0        |     1 |     1 |        1 |
| model_comparison_groq_llama_3.1_8b_baseline     | No RAG              |  0       | 0        |     0 |     0 |        0 |



## 3. Análise Detalhada por Configuração


### model_comparison_groq_k5_dense_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: dense

- k: 5

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5476 (±0.0245)

- bertscore_precision: 0.5519 (±0.0182)

- bertscore_recall: 0.5477 (±0.0555)


*RAGAS:*

- answer_relevancy: 0.5289 (±0.3791)

- faithfulness: 0.8583 (±0.1230)

- context_precision: 0.8333 (±0.2357)

- context_recall: 0.1111 (±0.1571)


*Performance:*

- latency_ms: 966.94 (±67.61)

- tokens_used: 829.00 (±17.68)

- num_chunks: 1.33 (±0.47)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       2 |            0.56376  |          0.0107219 |           0.553038 |           0.574482 |          1011.64  |          29.3539 |          982.286 |         1040.99  |              841.5 |               0.5 |               841 |               842 |              0.7875 |             0.0875 |                0.7 |              0.875 |                0.434783 |               0.434783 |                 0      |               0.869566 |
| prazo      |       1 |            0.515145 |          0         |           0.515145 |           0.515145 |           877.537 |           0      |          877.537 |          877.537 |              804   |               0   |               804 |               804 |              1      |             0      |                1   |              1     |                0.7172   |               0        |                 0.7172 |               0.7172   |



### model_comparison_groq_k5_hybrid_50_50_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: hybrid

- k: 5

- dense_weight: 0.5

- bm25_weight: 0.5

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5608 (±0.0531)

- bertscore_precision: 0.5826 (±0.0295)

- bertscore_recall: 0.5579 (±0.1118)


*RAGAS:*

- answer_relevancy: 0.8308 (±0.0644)

- faithfulness: 0.9186 (±0.0754)

- context_precision: 0.5778 (±0.3281)

- context_recall: 0.2222 (±0.1571)


*Performance:*

- latency_ms: 1090.61 (±191.33)

- tokens_used: 1867.67 (±198.47)

- num_chunks: 5.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       2 |            0.598122 |         0.00688869 |           0.591233 |           0.60501  |          1225.65  |          14.2404 |         1211.41  |         1239.89  |             2006.5 |              35.5 |              1971 |              2042 |            0.877841 |          0.0596591 |           0.818182 |             0.9375 |                0.875873 |              0.0114627 |               0.86441  |               0.887336 |
| prazo      |       1 |            0.486088 |         0          |           0.486088 |           0.486088 |           820.534 |           0      |          820.534 |          820.534 |             1590   |               0   |              1590 |              1590 |            1        |          0         |           1        |             1      |                0.740645 |              0         |               0.740645 |               0.740645 |



### model_comparison_groq_k10_hybrid_70_30_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: hybrid

- k: 10

- dense_weight: 0.7

- bm25_weight: 0.3

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5793 (±0.0000)

- bertscore_precision: 0.5548 (±0.0000)

- bertscore_recall: 0.6061 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8650 (±0.0000)

- faithfulness: 1.0000 (±0.0000)

- context_precision: 0.6111 (±0.0000)

- context_recall: 0.3333 (±0.0000)


*Performance:*

- latency_ms: 1179.64 (±0.00)

- tokens_used: 3661.00 (±0.00)

- num_chunks: 10.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |            0.579317 |                  0 |           0.579317 |           0.579317 |           1179.64 |                0 |          1179.64 |          1179.64 |               3661 |                 0 |              3661 |              3661 |                   1 |                  0 |                  1 |                  1 |                0.865001 |                      0 |               0.865001 |               0.865001 |



### model_comparison_groq_llama_3.1_8b


**Configuração:**

- use_rag: True

- retrieval_method: dense

- k: 3

- llm: groq:llama-3.1-8b-instant

- use_few_shot: N/A


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.6302 (±0.0000)

- bertscore_precision: 0.6163 (±0.0000)

- bertscore_recall: 0.6448 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8719 (±0.0000)

- faithfulness: 0.9000 (±0.0000)

- context_precision: 1.0000 (±0.0000)

- context_recall: 0.3333 (±0.0000)


*Performance:*

- latency_ms: 976.92 (±0.00)

- tokens_used: 708.00 (±0.00)

- num_chunks: 1.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |            0.630201 |                  0 |           0.630201 |           0.630201 |           976.918 |                0 |          976.918 |          976.918 |                708 |                 0 |               708 |               708 |                 0.9 |                  0 |                0.9 |                0.9 |                0.871891 |                      0 |               0.871891 |               0.871891 |



### model_comparison_groq_llama_3.1_8b_baseline


**Configuração:**

- use_rag: False

- llm: groq:llama-3.1-8b-instant

- use_few_shot: False


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5631 (±0.0000)

- bertscore_precision: 0.5300 (±0.0000)

- bertscore_recall: 0.6005 (±0.0000)


*RAGAS:*


*Performance:*

- latency_ms: 701.26 (±0.00)

- tokens_used: 347.00 (±0.00)

- num_chunks: 0.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|
| outros     |       1 |            0.563075 |                  0 |           0.563075 |           0.563075 |           701.259 |                0 |          701.259 |          701.259 |                347 |                 0 |               347 |               347 |



### model_comparison_groq_k3_hybrid_70_30_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: hybrid

- k: 3

- dense_weight: 0.7

- bm25_weight: 0.3

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5952 (±0.0000)

- bertscore_precision: 0.5882 (±0.0000)

- bertscore_recall: 0.6023 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8974 (±0.0000)

- faithfulness: 1.0000 (±0.0000)

- context_precision: 1.0000 (±0.0000)

- context_recall: 0.3333 (±0.0000)


*Performance:*

- latency_ms: 1045.88 (±0.00)

- tokens_used: 1801.00 (±0.00)

- num_chunks: 3.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |            0.595182 |                  0 |           0.595182 |           0.595182 |           1045.88 |                0 |          1045.88 |          1045.88 |               1801 |                 0 |              1801 |              1801 |                   1 |                  0 |                  1 |                  1 |                0.897363 |                      0 |               0.897363 |               0.897363 |



### model_comparison_tinyllama_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: dense

- k: 3

- llm: local:tinyllama

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5769 (±0.0000)

- bertscore_precision: 0.5403 (±0.0000)

- bertscore_recall: 0.6187 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8974 (±0.0000)

- faithfulness: 0.0500 (±0.0000)

- context_precision: 1.0000 (±0.0000)

- context_recall: 0.3333 (±0.0000)


*Performance:*

- latency_ms: 376441.33 (±0.00)

- tokens_used: 1880.00 (±0.00)

- num_chunks: 1.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |             0.57687 |                  0 |            0.57687 |            0.57687 |            376441 |                0 |           376441 |           376441 |               1880 |                 0 |              1880 |              1880 |                0.05 |                  0 |               0.05 |               0.05 |                0.897363 |                      0 |               0.897363 |               0.897363 |



### model_comparison_groq_k3_hybrid_50_50_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: hybrid

- k: 3

- dense_weight: 0.5

- bm25_weight: 0.5

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5907 (±0.0247)

- bertscore_precision: 0.5749 (±0.0384)

- bertscore_recall: 0.6118 (±0.0451)


*RAGAS:*

- answer_relevancy: 0.8675 (±0.0040)

- faithfulness: 0.8920 (±0.1048)

- context_precision: 0.8333 (±0.2357)

- context_recall: 0.2222 (±0.1571)


*Performance:*

- latency_ms: 1091.19 (±164.23)

- tokens_used: 1320.33 (±222.87)

- num_chunks: 3.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       2 |            0.600255 |          0.0253245 |           0.574931 |           0.62558  |           1168.08 |           150.73 |          1017.35 |          1318.81 |               1452 |               150 |              1302 |              1602 |            0.962963 |           0.037037 |           0.925926 |               1    |                0.867554 |             0.00490124 |               0.862653 |               0.872455 |
| prazo      |       1 |            0.571669 |          0         |           0.571669 |           0.571669 |            937.41 |             0    |           937.41 |           937.41 |               1057 |                 0 |              1057 |              1057 |            0.75     |           0        |           0.75     |               0.75 |                0.867532 |             0          |               0.867532 |               0.867532 |



### model_comparison_groq_k3_dense_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: dense

- k: 3

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5712 (±0.0224)

- bertscore_precision: 0.5725 (±0.0243)

- bertscore_recall: 0.5739 (±0.0499)


*RAGAS:*

- answer_relevancy: 0.8601 (±0.0099)

- faithfulness: 1.0000 (±0.0000)

- context_precision: 0.8333 (±0.2357)

- context_recall: 0.1111 (±0.1571)


*Performance:*

- latency_ms: 1003.98 (±105.63)

- tokens_used: 818.67 (±21.48)

- num_chunks: 1.33 (±0.47)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       2 |            0.58388  |          0.0165006 |           0.567379 |           0.60038  |          1075.66  |          36.3805 |         1039.28  |         1112.04  |                821 |                26 |               795 |               847 |                   1 |                  0 |                  1 |                  1 |                0.857948 |              0.0116181 |               0.84633  |               0.869566 |
| prazo      |       1 |            0.545973 |          0         |           0.545973 |           0.545973 |           860.628 |           0      |          860.628 |          860.628 |                814 |                 0 |               814 |               814 |                   1 |                  0 |                  1 |                  1 |                0.864289 |              0         |               0.864289 |               0.864289 |



### model_comparison_groq_k3_bm25_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: bm25

- k: 3

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5882 (±0.0381)

- bertscore_precision: 0.5810 (±0.0524)

- bertscore_recall: 0.5987 (±0.0403)


*RAGAS:*

- answer_relevancy: 0.8737 (±0.0211)

- faithfulness: 0.9444 (±0.0786)

- context_precision: 1.0000 (±0.0000)

- context_recall: 0.1111 (±0.1571)


*Performance:*

- latency_ms: 620.04 (±179.54)

- tokens_used: 1260.67 (±201.44)

- num_chunks: 3.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       2 |            0.596538 |          0.0443617 |           0.552177 |           0.6409   |           684.85  |          189.078 |          495.771 |          873.928 |             1362.5 |             172.5 |              1190 |              1535 |            0.916667 |          0.0833333 |           0.833333 |                  1 |                0.876872 |               0.025218 |               0.851654 |               0.90209  |
| prazo      |       1 |            0.571669 |          0         |           0.571669 |           0.571669 |           490.429 |            0     |          490.429 |          490.429 |             1057   |               0   |              1057 |              1057 |            1        |          0         |           1        |                  1 |                0.867498 |               0        |               0.867498 |               0.867498 |



### model_comparison_groq_k10_hybrid_50_50_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: hybrid

- k: 10

- dense_weight: 0.5

- bm25_weight: 0.5

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.6459 (±0.0000)

- bertscore_precision: 0.6402 (±0.0000)

- bertscore_recall: 0.6516 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8650 (±0.0000)

- faithfulness: 1.0000 (±0.0000)

- context_precision: 0.6111 (±0.0000)

- context_recall: 0.3333 (±0.0000)


*Performance:*

- latency_ms: 1578.25 (±0.00)

- tokens_used: 3539.00 (±0.00)

- num_chunks: 10.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |            0.645859 |                  0 |           0.645859 |           0.645859 |           1578.25 |                0 |          1578.25 |          1578.25 |               3539 |                 0 |              3539 |              3539 |                   1 |                  0 |                  1 |                  1 |                0.865001 |                      0 |               0.865001 |               0.865001 |



### model_comparison_groq_k5_hybrid_70_30_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: hybrid

- k: 5

- dense_weight: 0.7

- bm25_weight: 0.3

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5916 (±0.0000)

- bertscore_precision: 0.5712 (±0.0000)

- bertscore_recall: 0.6135 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8974 (±0.0000)

- faithfulness: 0.9091 (±0.0000)

- context_precision: 1.0000 (±0.0000)

- context_recall: 0.0000 (±0.0000)


*Performance:*

- latency_ms: 1086.94 (±0.00)

- tokens_used: 2453.00 (±0.00)

- num_chunks: 5.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |            0.591624 |                  0 |           0.591624 |           0.591624 |           1086.94 |                0 |          1086.94 |          1086.94 |               2453 |                 0 |              2453 |              2453 |            0.909091 |                  0 |           0.909091 |           0.909091 |                0.897363 |                      0 |               0.897363 |               0.897363 |



### model_comparison_groq_k10_dense_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: dense

- k: 10

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5839 (±0.0388)

- bertscore_precision: 0.5815 (±0.0183)

- bertscore_recall: 0.5892 (±0.0656)


*RAGAS:*

- answer_relevancy: 0.8440 (±0.0182)

- faithfulness: 0.9333 (±0.0943)

- context_precision: 0.8333 (±0.2357)

- context_recall: 0.2222 (±0.1571)


*Performance:*

- latency_ms: 947.13 (±90.18)

- tokens_used: 814.67 (±30.44)

- num_chunks: 1.33 (±0.47)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       2 |            0.605656 |          0.0288375 |           0.576819 |           0.634494 |          1010.81  |          5.62263 |         1005.19  |         1016.44  |                812 |                37 |               775 |               849 |                 0.9 |                0.1 |                0.8 |                  1 |                0.85175  |              0.0178158 |               0.833934 |               0.869566 |
| prazo      |       1 |            0.540352 |          0         |           0.540352 |           0.540352 |           819.766 |          0       |          819.766 |          819.766 |                820 |                 0 |               820 |               820 |                 1   |                0   |                1   |                  1 |                0.828585 |              0         |               0.828585 |               0.828585 |



### model_comparison_groq_k10_bm25_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: bm25

- k: 10

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.6158 (±0.0000)

- bertscore_precision: 0.6004 (±0.0000)

- bertscore_recall: 0.6321 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8974 (±0.0000)

- faithfulness: 1.0000 (±0.0000)

- context_precision: 0.6111 (±0.0000)

- context_recall: 0.3333 (±0.0000)


*Performance:*

- latency_ms: 756.68 (±0.00)

- tokens_used: 3606.00 (±0.00)

- num_chunks: 10.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |            0.615843 |                  0 |           0.615843 |           0.615843 |           756.678 |                0 |          756.678 |          756.678 |               3606 |                 0 |              3606 |              3606 |                   1 |                  0 |                  1 |                  1 |                0.897363 |                      0 |               0.897363 |               0.897363 |



### model_comparison_groq_k5_bm25_few_shot


**Configuração:**

- use_rag: True

- retrieval_method: bm25

- k: 5

- llm: groq:llama-3.1-8b-instant

- use_few_shot: True


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.5680 (±0.0156)

- bertscore_precision: 0.5623 (±0.0295)

- bertscore_recall: 0.5809 (±0.0586)


*RAGAS:*

- answer_relevancy: 0.8878 (±0.0062)

- faithfulness: 0.8268 (±0.1442)

- context_precision: 0.8000 (±0.1414)

- context_recall: 0.1111 (±0.1571)


*Performance:*

- latency_ms: 712.74 (±145.62)

- tokens_used: 1928.00 (±218.84)

- num_chunks: 5.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       2 |            0.579039 |        0.000431776 |           0.578607 |           0.579471 |           814.083 |          31.5961 |          782.487 |          845.679 |             2080.5 |              45.5 |              2035 |              2126 |            0.740196 |          0.0931373 |           0.647059 |           0.833333 |                0.888311 |             0.00749605 |               0.880815 |               0.895807 |
| prazo      |       1 |            0.545969 |        0           |           0.545969 |           0.545969 |           510.069 |           0      |          510.069 |          510.069 |             1623   |               0   |              1623 |              1623 |            1        |          0         |           1        |           1        |                0.886716 |             0          |               0.886716 |               0.886716 |



### model_comparison_tinyllama


**Configuração:**

- use_rag: True

- retrieval_method: dense

- k: 3

- llm: local:tinyllama

- use_few_shot: N/A


**Métricas Agregadas:**


*BERTScore:*

- bertscore_f1: 0.6016 (±0.0000)

- bertscore_precision: 0.5608 (±0.0000)

- bertscore_recall: 0.6489 (±0.0000)


*RAGAS:*

- answer_relevancy: 0.8397 (±0.0000)

- faithfulness: 0.3462 (±0.0000)

- context_precision: 1.0000 (±0.0000)

- context_recall: 0.3333 (±0.0000)


*Performance:*

- latency_ms: 236604.20 (±0.00)

- tokens_used: 1028.00 (±0.00)

- num_chunks: 1.00 (±0.00)



**Por Categoria:**

| category   |   count |   bertscore_f1_mean |   bertscore_f1_std |   bertscore_f1_min |   bertscore_f1_max |   latency_ms_mean |   latency_ms_std |   latency_ms_min |   latency_ms_max |   tokens_used_mean |   tokens_used_std |   tokens_used_min |   tokens_used_max |   faithfulness_mean |   faithfulness_std |   faithfulness_min |   faithfulness_max |   answer_relevancy_mean |   answer_relevancy_std |   answer_relevancy_min |   answer_relevancy_max |
|:-----------|--------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------:|-----------------:|-----------------:|-----------------:|-------------------:|------------------:|------------------:|------------------:|--------------------:|-------------------:|-------------------:|-------------------:|------------------------:|-----------------------:|-----------------------:|-----------------------:|
| outros     |       1 |            0.601641 |                  0 |           0.601641 |           0.601641 |            236604 |                0 |           236604 |           236604 |               1028 |                 0 |              1028 |              1028 |            0.346154 |                  0 |           0.346154 |           0.346154 |                0.839745 |                      0 |               0.839745 |               0.839745 |



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


✅ **Melhor BERTScore F1:** model_comparison_groq_k10_hybrid_50_50_few_shot
   - Valor: 0.6459
 (±0.0000)

🎯 **Melhor Faithfulness (Anti-Alucinação):** model_comparison_groq_k10_hybrid_70_30_few_shot
   - Valor: 1.0000
 (±0.0000)

📊 **Melhor Answer Relevancy:** model_comparison_groq_k3_hybrid_70_30_few_shot
   - Valor: 0.8974
 (±0.0000)

🔍 **Melhor Context Precision:** model_comparison_groq_llama_3.1_8b
   - Valor: 1.0000
 (±0.0000)

⚡ **Melhor Latência:** model_comparison_groq_k3_bm25_few_shot
   - Valor: 620.0427
 (±179.5371)

💰 **Melhor Tokens (Custo):** model_comparison_groq_llama_3.1_8b_baseline
   - Valor: 347.0000
 (±0.0000)


### Ranking Geral (Score Normalizado)


Combinação de todas as métricas com pesos iguais:


🥇 **model_comparison_groq_llama_3.1_8b_baseline** - Score: 2.5843

🥈 **model_comparison_groq_llama_3.1_8b** - Score: 1.2084

🥉 **model_comparison_groq_k10_dense_few_shot** - Score: 1.1176

4. **model_comparison_groq_k3_dense_few_shot** - Score: 1.1173

5. **model_comparison_groq_k3_bm25_few_shot** - Score: 1.1009

6. **model_comparison_groq_k5_dense_few_shot** - Score: 1.0358

7. **model_comparison_groq_k3_hybrid_50_50_few_shot** - Score: 0.9358

8. **model_comparison_groq_k3_hybrid_70_30_few_shot** - Score: 0.9265

9. **model_comparison_groq_k5_bm25_few_shot** - Score: 0.9205

10. **model_comparison_groq_k5_hybrid_70_30_few_shot** - Score: 0.8556

11. **model_comparison_groq_k10_bm25_few_shot** - Score: 0.8334

12. **model_comparison_groq_k5_hybrid_50_50_few_shot** - Score: 0.8126

13. **model_comparison_tinyllama** - Score: 0.7895

14. **model_comparison_groq_k10_hybrid_70_30_few_shot** - Score: 0.7416

15. **model_comparison_groq_k10_hybrid_50_50_few_shot** - Score: 0.7201

16. **model_comparison_tinyllama_few_shot** - Score: 0.5985


### Recomendações


1. **Produção**: Usar configuração com melhor equilíbrio entre F1 e latência

2. **Desenvolvimento**: Analisar qualitativamente os piores casos

3. **Pesquisa**: Testar configurações híbridas adicionais

4. **Otimização**: Considerar cache para queries similares (reduz latência)


### Informações de Execução


- Total de configurações testadas: 16

- Total de questões por configuração: 3

- Total de avaliações: 30

- Taxa de sucesso: 62.5%


---


*Relatório gerado automaticamente em 16/02/2026 às 22:49:54*