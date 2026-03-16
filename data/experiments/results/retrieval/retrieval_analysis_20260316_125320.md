# Análise de Retrieval - 16/03/2026
## Resumo
- **Avaliações**: 300
- **Métodos**: bm25, dense, hybrid
- **Total de queries**: 30
- **Normalização**: Min-Max [0,1] por pergunta (Abordagem A)

## Resultados por Método (Original)

| Método | K | Latência (ms) | Chunks | Top Score | Std Dev |
|--------|---|---------------|--------|-----------|----------|
| bm25 | 3 | 10.0 | 3.0 | 28.8483 | 2.8497 |
| bm25 | 5 | 10.3 | 5.0 | 28.8483 | 3.2317 |
| bm25 | 10 | 9.5 | 10.0 | 28.8483 | 3.4007 |
| dense | 3 | 507.9 | 3.0 | 0.7364 | 0.0124 |
| dense | 5 | 592.1 | 5.0 | 0.7364 | 0.0127 |
| dense | 10 | 507.8 | 10.0 | 0.7364 | 0.0132 |
| hybrid | 3 | 406.6 | 3.0 | 0.0015 | 0.0000 |
| hybrid | 5 | 424.2 | 5.0 | 0.0015 | 0.0000 |
| hybrid | 10 | 414.9 | 10.0 | 0.0015 | 0.0002 |

## Resultados Normalizados [0,1] (Comparáveis)

| Método | K | Rank | Score Norm | Latência (ms) |
|--------|---|------|------------|---------------|
| bm25 | 3 | #1 | 1.0000 | 10.0 |
| bm25 | 5 | #2 | 1.0000 | 10.3 |
| bm25 | 10 | #3 | 1.0000 | 9.5 |
| dense | 3 | #4 | 0.0414 | 507.9 |
| dense | 5 | #5 | 0.0414 | 592.1 |
| dense | 10 | #6 | 0.0414 | 507.8 |
| hybrid | 3 | #7 | 0.0000 | 406.6 |
| hybrid | 5 | #8 | 0.0000 | 424.2 |
| hybrid | 10 | #9 | 0.0000 | 414.9 |

## Destaques

⚡ **Mais rápido**: bm25 (k=10) - 2.75ms

🏆 **Melhor score normalizado**: bm25 (k=3) - 1.0000 [0,1]
   └─ Ranking: #1

## Resumo por Método (Normalizado)

**bm25**: score_norm=1.0000 | rank_médio=2.0 | latência=10ms
**dense**: score_norm=0.0292 | rank_médio=5.0 | latência=536ms
**hybrid**: score_norm=0.0000 | rank_médio=8.5 | latência=417ms
