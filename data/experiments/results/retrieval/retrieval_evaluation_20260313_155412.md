# Avaliação de Retrieval

**Data**: 13/03/2026 15:54:13

**Dataset**: 9 configurações testadas


## Resumo de Configurações

| Método | K | Latência (ms) | Chunks | Top Score | Avg Score |

|--------|---|---------------|--------|-----------|----------|

| bm25 | 10 | 7.8±17.3 | 10.0 | 28.8484 | 21.8001 |

| bm25 | 3 | 7.8±16.1 | 3.0 | 28.8484 | 25.8381 |

| bm25 | 5 | 7.6±18.4 | 5.0 | 28.8484 | 24.1467 |

| dense | 10 | 570.5±324.1 | 10.0 | 0.7364 | 0.7082 |

| dense | 3 | 549.3±581.4 | 3.0 | 0.7364 | 0.7235 |

| dense | 5 | 572.0±421.9 | 5.0 | 0.7364 | 0.7172 |

| hybrid | 10 | 403.6±78.2 | 10.0 | 0.0160 | 0.0137 |

| hybrid | 3 | 425.0±662.8 | 3.0 | 0.0160 | 0.0157 |

| hybrid | 5 | 418.2±684.6 | 5.0 | 0.0160 | 0.0151 |


## Melhores Configurações


⚡ **Mais rápido**: bm25_k5 (7.6ms)

🏆 **Melhor Top Score**: bm25_k3 (28.8484)

📊 **Melhor Avg Score**: bm25_k3 (25.8381)

📦 **Mais chunks**: dense_k10 (10.0)
