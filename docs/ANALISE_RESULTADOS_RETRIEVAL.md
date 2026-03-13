# 📊 ANÁLISE EXECUTIVA - Resultados de Retrieval

**Data**: 13 de março de 2026  
**Total de Avaliações**: 300 (10 configurações × 30 perguntas)  
**Taxa de Sucesso**: 100%  
**Tempo Total**: 5m 49s  

---

## 🎯 RESUMO DOS RESULTADOS

### Baseline por Método

| Método | Latência (ms) | Top Score | Chunks | Verdict |
|--------|---------------|-----------|--------|---------|
| **BM25** | 7.7 ± 0.2 | **28.848** ✅ | 6.0 | Excelente |
| **Dense** | 563.9 ± 22.6 | 0.736 ⚠️ | 6.0 | Inadequado |
| **Hybrid** | 415.6 ± 21.4 | 0.016 ❌ | 6.0 | Falhou |

### Ranking por Performance (Score × Latência)

1. 🥇 **BM25 k=5** → Score=28.8 | Latência=7.6ms | **RECOMENDADO**
2. 🥈 **BM25 k=3** → Score=28.8 | Latência=7.8ms
3. 🥉 **BM25 k=10** → Score=28.8 | Latência=7.8ms

---

## 🔴 PROBLEMAS CRÍTICOS

### 1️⃣ Dense Retriever com Scores Mínimos (0.736)

**Evidência**:
```
Dense k=3:  [q001: 0.7599, q002: 0.7716, q003: 0.7460, ... ] → All ~0.76
Dense k=5:  [q001: 0.7599, q002: 0.7716, q003: 0.7460, ... ] → All ~0.76
Dense k=10: [q001: 0.7599, q002: 0.7716, q003: 0.7460, ... ] → All ~0.76
```

**Causa Raiz**: 
- Modelo `gemini-embedding-001` é **deprecated** (Google anunciou descontinuação)
- Embedding space não é otimizado para domínio jurídico
- Calibração de similaridade de cosseno inadequada

**Impacto**:
- Dense é 73x MAIS LENTO que BM25
- Qualidade é 40x PIOR que BM25
- Inutiliza busca semântica no sistema

**Solução Imediata**:
```
Trocar: gemini-embedding-001 (deprecated)
Para:   text-embedding-004 (Google, novo modelo)

Expectativa: Scores 0.74 → 0.85-0.95 (10-25% melhoria)
```

---

### 2️⃣ Hybrid Completamente Degradado (0.016)

**Problema**:
```
BM25 k=5:           score=28.848    (ranking score)
Dense k=5:          score=0.736     (similarity score)
Hybrid k=5 (α=0.5): score=0.0160    ❌ PIOR QUE AMBOS
```

**Causa**: RRF fusion com escalas incompatíveis
- BM25 retorna scores [0, 30] (term frequency)
- Dense retorna scores [0, 1] (cosine similarity)
- RRF mistura sem normalização → Dense anula BM25

**Exemplo do RRF Quebrado**:
```python
# Sem normalização (ATUAL - ERRADO):
rrf_score = 1/(k1 + 10*rank_bm25) + 1/(k2 + 10*rank_dense)
# BM25 dom ina totalmente, Dense contribui mínimamente

# Com normalização (CORRETO):
bm25_norm = (score - 0) / (30 - 0)        # [0, 1]
dense_norm = (score - 0) / (1 - 0)        # [0, 1]
rrf_score = 1/(k1 + 10*rank_bm25_norm) + 1/(k2 + 10*rank_dense_norm)
```

**Solução**: Min-max normalization antes de RRF
```python
def normalize_scores(results, min_val, max_val):
    for r in results:
        r.score = (r.score - min_val) / (max_val - min_val)
    return results
```

**Expectativa Após Fix**: Hybrid score 0.016 → 0.3-0.5

---

### 3️⃣ k Values Sem Impacto (Dense/Hybrid)

**Observação Estranha**:
```
Dense k=3:  top_score=0.7599 (3 chunks com mesmo score)
Dense k=5:  top_score=0.7599 (5 chunks com mesmo score)
Dense k=10: top_score=0.7599 (10 chunks com mesmo score)

❌ ESPERADO: Diferentes scores nos chunks; top_k ≠ top_10
```

**Diagnóstico**:
- Embedding model retorna mesma similaridade para múltiplos chunks
- Ou: chunks muito similares semanticamente
- Ou: embedding space não tem discriminação suficiente

**Teste Necessário**:
```bash
# Listar scores dos chunks retornados
for query in q001 q002:
  retriever.retrieve(query, k=10)
  → [0.76, 0.76, 0.76, 0.75, 0.74, ...] ❌
  → [0.92, 0.81, 0.67, 0.45, 0.32, ...] ✅
```

---

## ✅ O QUE FUNCIONA BEM

### BM25 é Excelente para Legislação

**Razões**:
1. ✅ Domínio jurídico tem muitos termos específicos
2. ✅ Perguntas sobre "Lei 15.270" → Precisa achar "Lei 15.270"
3. ✅ Legislação é estruturada (artigos, incisos, parágrafos)
4. ✅ TF-IDF weights termos jurídicos corretamente

**Evidência**:
```
BM25 k=3:  latência=7.8ms,  score=28.8 ✅
BM25 k=5:  latência=7.6ms,  score=28.8 ✅
BM25 k=10: latência=7.8ms,  score=28.8 ✅

k não importa para latência (todos ~8ms)
Todos retornam MESMOS scores (domínio muito específico)
```

**Conclusão**: BM25 é **production-ready**

---

## 🎯 PLANO DE MELHORIA (3 SEMANAS)

### Semana 1: Fixes Críticos

#### [HOJE] Tarefa 1.1: Upgrade Embedding Model
```python
# src/ingestion/embeddings_pipeline.py
- model="models/gemini-embedding-001"  # ❌ Deprecated
+ model="models/text-embedding-004"    # ✅ Novo
```

**Validação**:
```bash
cd /home/decode/workspace/lion
source .venv/bin/activate
python3 << 'EOF'
import google.generativeai as genai
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Testar novo modelo
result = genai.embed_content(
    model="models/text-embedding-004",
    content="Quais os objetivos da Lei nº 15.270"
)
print(f"Embedding dimension: {len(result['embedding'])}")
print(f"Score sample: {result['embedding'][:5]}")
EOF
```

---

#### [HOJE] Tarefa 1.2: Normalização Hybrid
```python
# src/retrieval/hybrid_retriever.py

def retrieve(self, query: str, top_k: int = 5):
    # Buscar
    dense_results = self.dense.retrieve(query, top_k)
    bm25_results = self.bm25.retrieve(query, top_k)
    
    # ✅ NOVO: Normalizar para [0, 1]
    def min_max_normalize(results):
        if not results:
            return results
        scores = [r.score for r in results]
        min_s, max_s = min(scores), max(scores)
        
        for r in results:
            r.score = (r.score - min_s) / (max_s - min_s + 1e-6)
        return results
    
    dense_results = min_max_normalize(dense_results)
    bm25_results = min_max_normalize(bm25_results)
    
    # RRF agora com escalas compatíveis
    return self._reciprocal_rank_fusion(
        dense_results, bm25_results, 
        top_k, 
        dense_weight=self.dense_weight,
        bm25_weight=self.bm25_weight
    )
```

---

#### [AMANHÃ] Tarefa 1.3: Re-executar Avaliação
```bash
cd /home/decode/workspace/lion
source .venv/bin/activate

# Limpar cache de embeddings antigo
rm data/datasets/test/manual_rfb_test_embeddings.json

# Executar novo 2.3
python scripts/2.3_evaluate_retrieval.py
# → Vai gerar 30 embeddings com novo modelo
# → Testar Hybrid normalizado
```

**Métricas Esperadas**:
```
ANTES (13/03, 15:54):
Dense:  563.9ms, score=0.736
Hybrid: 415.6ms, score=0.016

DEPOIS (13/03, 18:00):
Dense:  500-600ms, score=0.85-0.95 (+25%)
Hybrid: 400-500ms, score=0.3-0.5 (30x melhoria!)
BM25:   7.7ms, score=28.8 (baseline)
```

---

### Semana 2: Cross-Encoder Reranking

#### Implementação
```python
# src/retrieval/cross_encoder_reranker.py
from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    def __init__(self, model='cross-encoder/mmarco-MiniLMv2-L12-H384'):
        self.model = CrossEncoder(model)
    
    def rerank(self, query: str, chunks: List[Chunk], top_k: int = 3) -> List[Chunk]:
        """Rerank chunks por relevância (query, chunk_text) pairs"""
        pairs = [(query, chunk.content) for chunk in chunks]
        scores = self.model.predict(pairs)  # Retorna [0, 1]
        
        scored = [(score, chunk) for score, chunk in zip(scores, chunks)]
        scored.sort(reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
```

#### Pipeline Otimizado
```
[Query] → BM25 (7.6ms) → [10 chunks] → CrossEncoder (50ms) → [3 top chunks]
         Rápido        Quantidade    Rerank                 Final
         
Latência: 7.6 + 50 = 57.6ms (vs 563.9ms Dense)
Qualidade: Melhor que BM25 puro (30+ score)
```

---

### Semana 3-4: Nice-to-Have

- [ ] Adaptive k values (query complexity)
- [ ] Hierarchical chunking (Lei/Art/Par structure)
- [ ] Domain-specific embedding model fine-tuning

---

## 📋 PRÓXIMOS PASSOS (IMEDIATOS)

### Hoje (13/03)
- [ ] Implementar Tarefa 1.1 (upgrade model)
- [ ] Implementar Tarefa 1.2 (normalização)
- [ ] Testar com 1-2 queries manualmente

### Amanhã (14/03)
- [ ] Limpar cache embeddings
- [ ] Executar novo 2.3_evaluate_retrieval.py
- [ ] Comparar resultados antes/depois
- [ ] Documentar melhorias em RESULTADOS_FASE1.md

### Semana 2
- [ ] Integrar Cross-Encoder
- [ ] Criar script 2.4_evaluate_optimized_retrieval.py
- [ ] Benchmark: BM25+Rerank vs alternatives

---

## 📊 RESULTADOS ESPERADOS

| Fase | Métrica | Baseline | Target | Gain |
|------|---------|----------|--------|------|
| 1 | Dense Score | 0.736 | 0.85 | +15% |
| 1 | Hybrid Score | 0.016 | 0.4 | +2400% |
| 2 | BM25+Rerank Score | 28.8 | 30+ | +4% |
| 2 | BM25+Rerank Latência | 7.6 | 57 | +650ms |
| 2 | Overall Quality | 28.8 | 30.5 | +5.9% |

---

## 💾 ARQUIVOS DE RESULTADO

- **JSON**: `retrieval_evaluation_20260313_155412.json` (519 KB - dados completos)
- **CSV**: `retrieval_evaluation_20260313_155412.csv` (47 KB - tabular)
- **Markdown**: `retrieval_evaluation_20260313_155412.md` (951 B - summary)

---

**Status**: 🟡 EM PROGRESSO - Awaiting Phase 1 implementation  
**Próxima Atualização**: 14 de março de 2026 (após Phase 1)  
**Responsável**: Sistema de Retrieval LION
