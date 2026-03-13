# 📋 Plano de Melhoria - Sistema de Retrieval

**Data**: 13 de março de 2026  
**Status**: Diagnóstico completo realizado  
**Baseline**: BM25 (28.8 score, 7.6ms latência)

---

## 📊 DIAGNÓSTICO ATUAL

### Resultados Observados

```
┌─────────────┬──────────────┬────────────┬──────────┐
│ Método      │ Latência (ms)│ Top Score  │ Chunks   │
├─────────────┼──────────────┼────────────┼──────────┤
│ BM25        │ 7.7ms        │ 28.848 ✅  │ 6.0      │
│ Dense       │ 563.9ms      │ 0.736 ⚠️  │ 6.0      │
│ Hybrid      │ 415.6ms      │ 0.016 ❌   │ 6.0      │
└─────────────┴──────────────┴────────────┴──────────┘
```

### 🔴 Problemas Críticos

1. **Dense Retriever com scores mínimos** (0.736)
   - **Causa**: Embedding model `gemini-embedding-001` é deprecated
   - **Impacto**: Inutiliza busca semântica
   - **Evidência**: Todos os 30 queries retornam MESMO score

2. **Hybrid degradado** (0.016 score)
   - **Causa**: RRF fusion com escalas diferentes (BM25: 28.8 vs Dense: 0.7)
   - **Impacto**: Dense não contribui, BM25 marginalizado
   - **Solução**: Normalização min-max antes de RRF

3. **k values sem impacto**
   - **Problema**: Dense retorna 10 chunks com scores idênticos
   - **Esperado**: Diferença de relevância ao variar k
   - **Causa raiz**: Modelo de embedding inadequado

---

## 🎯 PLANO DE AÇÃO (3 FASES)

### **FASE 1: Correções Críticas (Semana 1)**

#### ✅ Tarefa 1.1: Upgrade do Modelo de Embedding
**Prioridade**: 🔴 CRÍTICA  
**Esforço**: 2-3 horas  

**Objetivo**: Substituir `gemini-embedding-001` (deprecated) por modelo adequado

**Opções Avaliadas**:
```
┌────────────────────────┬───────┬──────────┬─────────┐
│ Modelo                 │ Custo │ Latência │ Domínio │
├────────────────────────┼───────┼──────────┼─────────┤
│ text-embedding-3-small │ $0.02 │ 500-600ms│ Genérico│
│ text-embedding-004     │ $0.02 │ 400-500ms│ Novo ✅ │
│ nomic-embed-text       │ Free  │ 300-400ms│ Geral   │
│ e5-large-v2            │ Free  │ 200-300ms│ Denso   │
└────────────────────────┴───────┴──────────┴─────────┘
```

**Recomendação**: `text-embedding-004` (Google, mais recente)

**Implementação**:
```python
# src/ingestion/embeddings_pipeline.py
- Trocar: genai.embed_content(model="models/gemini-embedding-001")
+ Trocar: genai.embed_content(model="models/text-embedding-004")
```

**Validação**:
- Gerar embeddings para 5 perguntas de teste
- Comparar distribuição de scores (expectativa: 0.1-0.9 vs 0.7-0.74)
- Re-executar 2.3_evaluate_retrieval.py

---

#### ✅ Tarefa 1.2: Normalização do Hybrid Retriever
**Prioridade**: 🔴 CRÍTICA  
**Esforço**: 1-2 horas  

**Problema**: RRF com escalas incompatíveis

**Solução**: Min-max normalization antes de fusão

```python
# src/retrieval/hybrid_retriever.py

def retrieve(self, query: str, top_k: int = 5):
    # Buscar com ambos métodos
    dense_results = self.dense.retrieve(query, top_k)
    bm25_results = self.bm25.retrieve(query, top_k)
    
    # ✅ NOVO: Normalizar scores
    def normalize_scores(results, method_type):
        if not results:
            return []
        scores = [r.score for r in results]
        min_score, max_score = min(scores), max(scores)
        
        for r in results:
            if max_score - min_score > 0:
                r.score = (r.score - min_score) / (max_score - min_score)
            else:
                r.score = 0.5
        return results
    
    dense_results = normalize_scores(dense_results, 'dense')
    bm25_results = normalize_scores(bm25_results, 'bm25')
    
    # RRF com scores normalizados [0, 1]
    return self._reciprocal_rank_fusion(dense_results, bm25_results, top_k)
```

**Teste**:
- Executar 2.3 novamente
- Expectativa: Hybrid scores > 0.5 (vs 0.016 atual)

---

#### ✅ Tarefa 1.3: Verificação de k Values
**Prioridade**: 🟡 IMPORTANTE  
**Esforço**: 1 hora  

**Diagnóstico**: Por que `k=3`, `k=5`, `k=10` retornam mesmo score?

**Teste**:
```python
# scripts/debug_k_values.py
for config in RETRIEVAL_CONFIGS:
    retriever = create_retriever(config)
    results = retriever.retrieve(question, top_k=config['k'])
    
    # Debug: imprimir scores de cada chunk
    for i, chunk in enumerate(results, 1):
        print(f"  k={config['k']}, rank={i}: score={chunk.score:.4f}")
```

**Esperado**:
- k=3: [0.85, 0.72, 0.68]
- k=5: [0.85, 0.72, 0.68, 0.55, 0.42]
- k=10: [0.85, 0.72, 0.68, 0.55, 0.42, 0.38, 0.32, 0.28, 0.22, 0.15]

---

### **FASE 2: Implementação de Cross-Encoder (Semana 2)**

#### ✅ Tarefa 2.1: Integração de Cross-Encoder
**Prioridade**: 🔴 CRÍTICA  
**Esforço**: 4-6 horas  

**Objetivo**: Adicionar reranking pós-retrieval

**Arquitetura**:
```
Query → BM25 (7.6ms) → [10 chunks] → CrossEncoder Rerank (50ms) → [3 top chunks]
                                                                   ↑
                                                        +15ms latência total
                                                         67.6ms (vs 550ms Dense)
```

**Implementação**:
```python
# src/retrieval/cross_encoder_reranker.py
from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    def __init__(self, model_name='cross-encoder/mmarco-MiniLMv2-L12-H384'):
        self.model = CrossEncoder(model_name)
    
    def rerank(self, query: str, chunks: List[Chunk], top_k: int = 3) -> List[Chunk]:
        """Rerank chunks usando cross-encoder
        
        Args:
            query: Query string
            chunks: Chunks retrievados (tipicamente k=10)
            top_k: Retornar apenas top_k após reranking
        
        Returns:
            Chunks ordenados por relevância
        """
        # Cross-encoder espera pares (query, chunk_text)
        pairs = [(query, chunk.content) for chunk in chunks]
        
        # Obter scores [0, 1]
        scores = self.model.predict(pairs, batch_size=32)
        
        # Reordenar
        scored_chunks = [(score, chunk) for score, chunk in zip(scores, chunks)]
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Retornar top_k
        return [chunk for _, chunk in scored_chunks[:top_k]]
```

**Pipeline Otimizado**:
```python
# src/retrieval/optimized_retriever.py
class OptimizedRetriever:
    def __init__(self):
        self.bm25 = BM25Retriever(...)
        self.reranker = CrossEncoderReranker()
    
    def retrieve(self, query: str, top_k: int = 3):
        # 1. BM25 rápido (7.6ms)
        bm25_results = self.bm25.retrieve(query, top_k=10)
        
        # 2. Rerank com cross-encoder (50ms)
        if len(bm25_results) > top_k:
            final_results = self.reranker.rerank(query, bm25_results, top_k)
        else:
            final_results = bm25_results
        
        return final_results
```

**Novo Script de Avaliação**:
```python
# scripts/2.4_evaluate_optimized_retrieval.py
configs = [
    {'method': 'bm25', 'k': 5},
    {'method': 'bm25+rerank', 'k': 10, 'rerank_k': 3},
    {'method': 'dense', 'k': 5},
    {'method': 'hybrid', 'k': 5},
]
# Comparecer latência e qualidade
```

---

#### ✅ Tarefa 2.2: Avaliação de Cross-Encoder
**Prioridade**: 🟡 IMPORTANTE  
**Esforço**: 2-3 horas  

**Teste**: Executar script 2.4 para comparar:
- Latência: BM25 vs BM25+Rerank
- Qualidade: Usar mock evaluation (manual rating de top 5 queries)
- Trade-off: Latência +50ms vs melhoria de qualidade

**Métrica de Sucesso**:
```
BM25 (baseline):         7.6ms, score=28.8
BM25 + Rerank (otimizado): 57.6ms, score=29.5+ (4% melhoria aceitável)
```

---

### **FASE 3: Otimizações Avançadas (Semana 3-4)**

#### ✅ Tarefa 3.1: Adaptive k Values
**Prioridade**: 🟢 NICE-TO-HAVE  
**Esforço**: 3-4 horas  

**Objetivo**: Ajustar k dinamicamente baseado em complexidade da query

```python
# src/retrieval/query_complexity.py
def estimate_query_complexity(query: str) -> int:
    """
    Retorna k dinâmico (3, 5, ou 10)
    
    Heurísticas:
    - Palavras < 3: k=3 (query específica, ex: "Lei 15.270")
    - Palavras 3-5: k=5 (normal, ex: "IRRF lucros dividendos")
    - Palavras > 5: k=10 (complexa, ex: "como calcular IRRF para dividendos...")
    """
    word_count = len(query.split())
    
    if word_count < 3:
        return 3
    elif word_count < 6:
        return 5
    else:
        return 10
```

#### ✅ Tarefa 3.2: Chunking Hierarchical
**Prioridade**: 🟢 NICE-TO-HAVE  
**Esforço**: 5-6 horas  

**Objetivo**: Melhorar relevância com contexto hierárquico

**Estratégia**:
```
Lei 15.270
  └─ Art. 1º
      ├─ Parágrafo 1
      ├─ Parágrafo 2
      └─ Inciso I

Chunks atuais: Texto livre (1292 chunks)
Chunks melhorados: Estrutura Lei/Art/Par (com metadata)
```

**Benefícios**:
- Retrieval sabe qual Lei/Art o chunk pertence
- Melhor filtragem por tipo de legislação
- Contexto hierárquico para geração

---

## 📈 ROADMAP VISUAL

```
Semana 1 (CRÍTICO)
├─ 1.1: Upgrade embedding model → Dense scores 0.7 → 0.85
├─ 1.2: Normalização Hybrid → scores 0.016 → 0.5+
└─ 1.3: Debug k values

Semana 2 (IMPORTANTE)
├─ 2.1: Cross-Encoder Reranker → latência +50ms, qualidade +10%
└─ 2.2: Avaliação 2.4

Semana 3-4 (NICE-TO-HAVE)
├─ 3.1: Adaptive k values
└─ 3.2: Hierarchical chunking
```

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Latência BM25 | 7.6ms | 5-10ms | ✅ |
| Dense Score | 0.74 | 0.85+ | ⏳ Fase 1 |
| Hybrid Score | 0.016 | 0.5+ | ⏳ Fase 1 |
| BM25+Rerank Latência | - | <60ms | ⏳ Fase 2 |
| Overall Quality | 28.8 | 30+ | ⏳ Fase 2 |

---

## 🔧 TECNOLOGIAS A USAR

### Fase 1
- Google Gemini API (novo modelo embedding)
- ChromaDB (já integrado)

### Fase 2
- `sentence-transformers[cross-encoder]`
- Modelo: `cross-encoder/mmarco-MiniLMv2-L12-H384`

### Fase 3
- `nomic-embed-text` (optional, domínio-específico)
- Improved chunking logic

---

## 💡 PRÓXIMOS PASSOS IMEDIATOS

1. **[HOJE]** Atualizar embedding model para `text-embedding-004`
2. **[HOJE]** Implementar normalização no Hybrid
3. **[AMANHÃ]** Executar novo 2.3_evaluate_retrieval.py
4. **[AMANHÃ]** Validar melhoria em Dense e Hybrid scores
5. **[SEMANA 2]** Integrar cross-encoder reranking

---

## 📋 CHECKLIST

- [ ] Tarefa 1.1: Upgrade embedding model
- [ ] Tarefa 1.2: Normalização Hybrid
- [ ] Tarefa 1.3: Debug k values
- [ ] Executar novo 2.3 com melhorias
- [ ] Tarefa 2.1: Cross-Encoder implementation
- [ ] Tarefa 2.2: Avaliação 2.4
- [ ] Documentar resultados em RESULTADOS_FASE1.md

---

**Última atualização**: 13 de março de 2026, 15:54  
**Próxima review**: 20 de março de 2026
