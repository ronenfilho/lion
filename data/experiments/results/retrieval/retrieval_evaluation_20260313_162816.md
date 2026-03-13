# Avaliação de Retrieval

**Data**: 13/03/2026 16:28:16

**Dataset**: 9 configurações testadas


## Resumo de Configurações

| Método | K | Latência (ms) | Chunks | Top Score | Avg Score |

|--------|---|---------------|--------|-----------|----------|

| bm25 | 10 | 8.5±15.4 | 10.0 | 28.8484 | 21.8001 |

| bm25 | 3 | 7.5±10.3 | 3.0 | 28.8484 | 25.8381 |

| bm25 | 5 | 7.9±12.5 | 5.0 | 28.8484 | 24.1467 |

| dense | 10 | 516.7±335.6 | 10.0 | 0.7364 | 0.7082 |

| dense | 3 | 592.0±1071.1 | 3.0 | 0.7364 | 0.7235 |

| dense | 5 | 606.0±1153.2 | 5.0 | 0.7364 | 0.7172 |

| hybrid | 10 | 404.7±127.0 | 10.0 | 0.0160 | 0.0137 |

| hybrid | 3 | 398.6±48.9 | 3.0 | 0.0160 | 0.0157 |

| hybrid | 5 | 402.9±90.1 | 5.0 | 0.0160 | 0.0151 |


## Melhores Configurações


⚡ **Mais rápido**: bm25_k3 (7.5ms)

🏆 **Melhor Top Score**: bm25_k3 (28.8484)

📊 **Melhor Avg Score**: bm25_k3 (25.8381)

📦 **Mais chunks**: dense_k10 (10.0)
