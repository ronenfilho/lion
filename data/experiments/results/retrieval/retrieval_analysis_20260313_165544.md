# Análise de Retrieval - 13/03/2026
## Resumo
- **Avaliações**: 300
- **Métodos**: bm25, dense, hybrid
- **Total de queries**: 30

## Resultados por Método

| Método | K | Latência (ms) | Chunks | Top Score | Std Dev |
|--------|---|---------------|--------|-----------|----------|
| bm25 | 3 | 8.8 | 3.0 | 28.8484 | 2.8488 |
| bm25 | 5 | 8.9 | 5.0 | 28.8484 | 3.2323 |
| bm25 | 10 | 10.7 | 10.0 | 28.8484 | 3.4014 |
| dense | 3 | 567.2 | 3.0 | 0.7364 | 0.0124 |
| dense | 5 | 581.3 | 5.0 | 0.7364 | 0.0127 |
| dense | 10 | 580.6 | 10.0 | 0.7364 | 0.0132 |
| hybrid | 3 | 434.5 | 3.0 | 0.0160 | 0.0004 |
| hybrid | 5 | 404.6 | 5.0 | 0.0160 | 0.0009 |
| hybrid | 10 | 395.7 | 10.0 | 0.0160 | 0.0019 |

## Destaques

⚡ **Mais rápido**: bm25 (k=5) - 2.26ms

🏆 **Melhor score**: bm25 (k=3) - 61.349162

