# 🎯 Recomendações Técnicas - LION

## Decisões Arquiteturais e Trade-offs

Este documento detalha recomendações específicas baseadas em experiência prática com sistemas RAG em produção.

---

## 🔍 1. Escolha de Embedding Model

### Recomendação: **text-embedding-3-large** (OpenAI)

**Justificativa:**
- ✅ Melhor performance em benchmarks multilingual
- ✅ 3072 dimensões (alta capacidade de representação)
- ✅ Ótimo para português
- ✅ API estável e confiável

**Alternativa para produção:** **BGE-m3** (self-hosted)
- Reduz custo em ~80%
- Performance ~95% do text-embedding-3-large
- Requer GPU para embeddings em tempo real

### Implementação

```python
# Produção: usar em batch para reduzir latência
from openai import OpenAI

client = OpenAI()

def embed_batch(texts: List[str], batch_size: int = 100):
    """Embeddings em lote para eficiência"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=batch
        )
        embeddings.extend([e.embedding for e in response.data])
    return embeddings
```

---

## 🗄️ 2. Escolha de Vector Store

### Para Experimentos: **ChromaDB**
- ✅ Setup em 5 minutos
- ✅ Persistência local
- ✅ Sem infraestrutura adicional

### Para Produção: **Qdrant** (recomendado)

**Por quê Qdrant?**
- ✅ Filtros complexos com metadados
- ✅ Performance superior (HNSW otimizado)
- ✅ Self-hosted ou cloud
- ✅ Suporte a payload rico
- ✅ Backup e replicação nativos

### Comparação

| Feature | ChromaDB | Qdrant | Pinecone | Weaviate |
|---------|----------|---------|----------|----------|
| Setup | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Performance | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Filtros | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Custo | FREE | FREE (self) | $$$ | $$ |
| Escala | <1M | <10M | >100M | >10M |

**Decisão:** 
- ChromaDB para MVP/Experimentos
- Migrar para Qdrant quando escalar

---

## 🤖 3. Escolha de LLM

### Para Experimentos (Comparação)

| Modelo | Use Case | Custo/1M tokens | Pros | Cons |
|--------|----------|-----------------|------|------|
| **GPT-4 Turbo** | Baseline premium | $30 | Melhor raciocínio | Caro |
| **Claude 3.5 Sonnet** | Melhor seguimento | $15 | Ótimo com instruções | Context window |
| **Gemini 1.5 Pro** | Contexto longo | $7 | 1M tokens, barato | Performance variável |
| **Llama 3.1 8B (Q4)** | Self-hosted | ~$0 | Zero custo | Setup complexo |

### Recomendação para Produção

**Hybrid Approach:**

```python
class SmartLLMRouter:
    """Roteamento inteligente baseado na complexidade da query"""
    
    def route(self, query: str, chunks: List[dict]) -> str:
        complexity = self.assess_complexity(query, chunks)
        
        if complexity == "high":
            # Queries complexas → modelo grande
            return "gpt-4-turbo"
        elif complexity == "medium":
            # Queries normais → modelo médio
            return "gpt-3.5-turbo"
        else:
            # Queries simples → modelo local
            return "llama-3-8b-local"
    
    def assess_complexity(self, query: str, chunks: List[dict]) -> str:
        """
        Complexidade baseada em:
        - Número de chunks necessários
        - Presença de cálculos
        - Múltiplas fontes normativas
        """
        if len(chunks) > 7:
            return "high"
        if any(keyword in query.lower() for keyword in ["calcular", "quanto", "valor"]):
            return "high"
        if len(chunks) > 3:
            return "medium"
        return "simple"
```

**Benefício:** Reduz custo em 60-70% sem perda significativa de qualidade.

---

## 🔧 4. Parâmetros de Geração Otimizados

### Para Domínio Legal (IRPF)

```python
GENERATION_CONFIG = {
    "temperature": 0.2,           # CRÍTICO: baixa aleatoriedade
    "top_p": 0.9,                 # Nucleus sampling
    "max_tokens": 800,            # Respostas concisas
    "presence_penalty": 0.1,      # Evita repetição
    "frequency_penalty": 0.1,     # Promove diversidade léxica
    "stop_sequences": [           # Evita continuar além da resposta
        "\n\nContexto:",
        "\n\n---",
        "###"
    ]
}
```

### Por que esses valores?

- **Temperature 0.2**: Domínio legal requer determinismo
- **max_tokens 800**: Respostas maiores tendem a alucinar
- **stop_sequences**: Evita que LLM "invente" chunks extras

---

## 🎯 5. Estratégia de Chunking

### Recomendação: **Híbrida** (Structure-aware + Q&A)

```python
class HybridChunker:
    """Estratégia diferenciada por tipo de documento"""
    
    def chunk_document(self, document: dict) -> List[dict]:
        doc_type = document['metadata']['type']
        
        if doc_type == "instrucao_normativa":
            # Respeitar estrutura legal
            return StructuralChunker().chunk(document)
        
        elif doc_type == "perguntao":
            # Cada Q&A é uma unidade
            return QAChunker().chunk(document)
        
        elif doc_type == "lei":
            # Artigos com contexto
            return LegalChunker().chunk(document)
        
        else:
            # Fallback para sliding window
            return FixedChunker(size=800, overlap=0.2).chunk(document)
```

### Parâmetros Recomendados

| Tipo de Documento | Estratégia | Tamanho Médio | Overlap |
|-------------------|-----------|---------------|---------|
| Instrução Normativa | Structural | ~600 tokens | 0% |
| Perguntão (Q&A) | Atomic | ~400 tokens | 0% |
| Lei | Hierarchical | ~800 tokens | 10% |
| Manual | Sliding Window | ~800 tokens | 20% |

---

## 🔍 6. Retrieval: Quando usar cada estratégia

### Dense Only (Embeddings)
✅ Use quando:
- Queries semânticas amplas
- Sinônimos e paráfrases
- Conceitos abstratos

❌ Evite quando:
- Queries com códigos exatos (ex: "Art. 12")
- Termos técnicos muito específicos
- Datas e números

### Hybrid (Dense + Sparse)
✅ Use quando:
- Domínio técnico/legal
- Mistura de conceitos e termos exatos
- Precisa de recall alto

**Implementação recomendada:**

```python
# Pesos otimizados para domínio legal
HYBRID_CONFIG = {
    "dense_weight": 0.6,    # Conceitos semânticos
    "sparse_weight": 0.4,   # Termos exatos
    "rrf_k": 60             # Parâmetro de RRF
}
```

### Com Re-ranking
✅ **SEMPRE** use re-ranking quando:
- Latência < 3s é aceitável
- Precisão é crítica
- Custo de erro é alto (domínio legal)

**Custo-benefício:**
- Adiciona ~500ms de latência
- Melhora Precision@5 em 15-25%
- **Vale a pena para IRPF**

---

## 💾 7. Caching Strategy

### Três Camadas Recomendadas

```python
class MultiLayerCache:
    """Cache em 3 níveis"""
    
    def __init__(self):
        # L1: In-memory (ultra rápido, pequeno)
        self.l1_cache = SemanticCache(
            max_size=100,
            similarity_threshold=0.98
        )
        
        # L2: Redis (rápido, médio)
        self.l2_cache = RedisCache(
            ttl=3600,  # 1 hora
            max_size=10000
        )
        
        # L3: Disk (lento, grande)
        self.l3_cache = DiskCache(
            path="./cache",
            ttl=86400  # 24 horas
        )
    
    def get(self, query_embedding):
        # Tentar L1
        result = self.l1_cache.get(query_embedding)
        if result:
            return result, "L1"
        
        # Tentar L2
        result = self.l2_cache.get(query_embedding)
        if result:
            self.l1_cache.set(query_embedding, result)  # Promover
            return result, "L2"
        
        # Tentar L3
        result = self.l3_cache.get(query_embedding)
        if result:
            self.l2_cache.set(query_embedding, result)  # Promover
            return result, "L3"
        
        return None, "MISS"
```

### Cache Hit Rate Esperado

| Cenário | Hit Rate Esperado |
|---------|-------------------|
| Perguntas frequentes | 70-80% |
| Queries únicas | 20-30% |
| Produção típica | 40-50% |

**Impacto:**
- 40% hit rate = 40% redução de custo
- Latência reduz de ~2s para ~100ms

---

## 🛡️ 8. Guardrails: O que é Crítico

### Prioridade ALTA (Obrigatório)

1. **Citation Validation** - Evita alucinação de artigos
2. **PII Detection** - Compliance com LGPD
3. **Query Length Limits** - Previne DoS
4. **Output Length Validation** - Detecta respostas truncadas

### Prioridade MÉDIA

1. Intent Classification
2. Query Normalization
3. Prompt Injection Detection

### Prioridade BAIXA (Nice to have)

1. Toxicity Detection
2. Language Detection
3. Domain Relevance Scoring

---

## 📊 9. Métricas: O que Monitorar

### Em Experimentos

```python
EXPERIMENT_METRICS = {
    "retrieval": ["precision@k", "recall@k", "mrr"],
    "generation": ["bertscore_f1", "faithfulness", "answer_relevancy"],
    "custom": ["citation_accuracy", "normative_coverage"]
}
```

### Em Produção

```python
PRODUCTION_METRICS = {
    "performance": {
        "latency_p50": target < 1.5s,
        "latency_p95": target < 3.0s,
        "latency_p99": target < 5.0s
    },
    "quality": {
        "user_satisfaction": target > 4.0/5,
        "thumbs_up_rate": target > 70%
    },
    "efficiency": {
        "cache_hit_rate": target > 40%,
        "cost_per_query": target < $0.05
    },
    "reliability": {
        "error_rate": target < 1%,
        "uptime": target > 99.5%
    }
}
```

---

## 🚨 10. Erros Comuns a Evitar

### ❌ Erro #1: Chunks muito grandes
**Problema:** LLM perde foco em contextos longos  
**Solução:** Max 800 tokens por chunk

### ❌ Erro #2: Não usar metadados
**Problema:** Retrieval impreciso  
**Solução:** Metadados ricos (tipo, artigo, fonte, ano)

### ❌ Erro #3: Temperature alta
**Problema:** Alucinações em domínio legal  
**Solução:** Temperature 0.2-0.3 (máximo)

### ❌ Erro #4: Ignorar edge cases
**Problema:** Queries fora do escopo quebram o sistema  
**Solução:** Intent classification + fallback response

### ❌ Erro #5: Não validar citações
**Problema:** LLM inventa artigos  
**Solução:** Output guardrails obrigatórios

### ❌ Erro #6: Busca apenas vetorial
**Problema:** Perde termos técnicos exatos  
**Solução:** Hybrid search (dense + sparse)

### ❌ Erro #7: Sem cache
**Problema:** Custo e latência altos  
**Solução:** Semantic cache desde MVP

### ❌ Erro #8: Prompt genérico
**Problema:** Respostas sem fundamentação  
**Solução:** Prompt engineering específico para legal

### ❌ Erro #9: Não logar propriamente
**Problema:** Impossível debugar ou otimizar  
**Solução:** Logging estruturado desde dia 1

### ❌ Erro #10: Otimização prematura
**Problema:** Complexidade desnecessária  
**Solução:** Start simple, medir, depois otimizar

---

## ✅ Checklist de Validação Pré-Produção

```markdown
## Qualidade
- [ ] BERTScore F1 > 0.85 em dataset de teste
- [ ] Faithfulness > 0.90
- [ ] Citation Accuracy = 100% (zero alucinações de artigos)
- [ ] User testing com 20+ usuários reais

## Performance
- [ ] Latência p95 < 3s
- [ ] Cache hit rate > 30%
- [ ] Throughput > 10 queries/segundo

## Segurança
- [ ] Guardrails testados com adversarial examples
- [ ] Rate limiting configurado
- [ ] PII detection validado
- [ ] Logs não contêm dados sensíveis

## Confiabilidade
- [ ] Error handling completo
- [ ] Fallbacks definidos
- [ ] Health checks implementados
- [ ] Backup e recovery testados

## Observabilidade
- [ ] Dashboards configurados
- [ ] Alertas críticos definidos
- [ ] Logs estruturados e buscáveis
- [ ] Tracing end-to-end

## Compliance
- [ ] Disclaimers em todas respostas
- [ ] Fontes sempre citadas
- [ ] Termos de uso definidos
- [ ] Auditoria de logs possível
```

---

## 📚 Referências e Leituras Recomendadas

### Papers
1. **RAG**: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
2. **Lost in the Middle**: Como LLMs usam contextos longos (Liu et al., 2023)
3. **RAGAS**: Framework de avaliação para RAG (Es et al., 2023)

### Blog Posts
- Pinecone: "Hybrid Search Explained"
- LangChain: "Advanced RAG Techniques"
- Anthropic: "Constitutional AI" (para guardrails)

### Repositórios
- `langchain-ai/langchain` - Framework RAG
- `qdrant/qdrant` - Vector database
- `explodinggradients/ragas` - Evaluation

---

## 🎯 Resumo Executivo de Decisões

| Componente | Escolha Recomendada | Justificativa |
|------------|---------------------|---------------|
| **Embedding** | text-embedding-3-large | Melhor performance PT |
| **Vector Store** | Qdrant (produção) | Performance + features |
| **LLM** | Hybrid routing | Custo-benefício |
| **Chunking** | Structure-aware | Preserva semântica legal |
| **Retrieval** | Hybrid + Re-rank | +15% precisão |
| **Temperature** | 0.2 | Determinismo legal |
| **Cache** | Multi-layer | 40% redução custo |
| **Guardrails** | Output validation | Zero alucinações |

---

**Última revisão:** 14/02/2026  
**Baseado em:** Experiência prática com RAG em produção  
**Domínio:** Legal/Tributário (high-stakes)
