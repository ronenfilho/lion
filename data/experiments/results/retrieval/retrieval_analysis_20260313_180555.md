# Análise de Retrieval - 13/03/2026
## Resumo
- **Avaliações**: 300
- **Métodos**: bm25, dense, hybrid
- **Total de queries**: 30
- **Normalização**: Min-Max [0,1] por pergunta (Abordagem A)

## Resultados por Método (Original)

| Método | K | Latência (ms) | Chunks | Top Score | Std Dev |
|--------|---|---------------|--------|-----------|----------|
| bm25 | 3 | 7.7 | 3.0 | 28.8484 | 2.8488 |
| bm25 | 5 | 8.4 | 5.0 | 28.8484 | 3.2323 |
| bm25 | 10 | 9.2 | 10.0 | 28.8484 | 3.4014 |
| dense | 3 | 539.2 | 3.0 | 0.7364 | 0.0124 |
| dense | 5 | 553.3 | 5.0 | 0.7364 | 0.0127 |
| dense | 10 | 587.0 | 10.0 | 0.7364 | 0.0132 |
| hybrid | 3 | 408.7 | 3.0 | 0.0015 | 0.0000 |
| hybrid | 5 | 412.0 | 5.0 | 0.0015 | 0.0000 |
| hybrid | 10 | 423.1 | 10.0 | 0.0015 | 0.0002 |

## Resultados Normalizados [0,1] (Comparáveis)

| Método | K | Rank | Score Norm | Latência (ms) |
|--------|---|------|------------|---------------|
| bm25 | 3 | #1 | 1.0000 | 7.7 |
| bm25 | 5 | #2 | 1.0000 | 8.4 |
| bm25 | 10 | #3 | 1.0000 | 9.2 |
| dense | 3 | #4 | 0.0414 | 539.2 |
| dense | 5 | #5 | 0.0414 | 553.3 |
| dense | 10 | #6 | 0.0414 | 587.0 |
| hybrid | 3 | #7 | 0.0000 | 408.7 |
| hybrid | 5 | #8 | 0.0000 | 412.0 |
| hybrid | 10 | #9 | 0.0000 | 423.1 |

## Destaques

⚡ **Mais rápido**: bm25 (k=10) - 2.26ms

🏆 **Melhor score normalizado**: bm25 (k=3) - 1.0000 [0,1]
   └─ Ranking: #1

## Resumo por Método (Normalizado)

**bm25**: score_norm=1.0000 | rank_médio=2.0 | latência=8ms
**dense**: score_norm=0.0292 | rank_médio=5.0 | latência=560ms
**hybrid**: score_norm=0.0000 | rank_médio=8.5 | latência=414ms
