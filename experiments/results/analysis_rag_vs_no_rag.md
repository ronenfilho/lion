# 📊 Análise dos Experimentos: RAG vs No-RAG

**Data:** 2026-02-15 23:18  
**Dataset:** 1 pergunta de teste (q001)  
**Pergunta:** "Quais os objetivos da Lei nº 15.270, de 2025?"

---

## 🎯 Resumo Executivo

### Comparação de Performance

| Métrica | Baseline (Sem RAG) | Dense RAG | Hybrid RAG | Melhor |
|---------|-------------------|-----------|------------|--------|
| **BERTScore F1** | 0.567 | **0.637** ✅ | 0.600 | Dense RAG (+12%) |
| **Latência (ms)** | 6767 | **3104** ✅ | **2669** ✅ | Hybrid RAG (-61%) |
| **Tokens Usados** | 220 | **148** ✅ | 169 | Dense RAG (-33%) |
| **Answer Relevancy** | N/A | 0.870 | **0.872** ✅ | Hybrid RAG |
| **Faithfulness** | N/A | 0.667 | **0.889** ✅ | Hybrid RAG |
| **Context Precision** | N/A | 1.000 | 1.000 | Empate |
| **Context Recall** | N/A | **0.333** ✅ | 0.000 ⚠️ | Dense RAG |

---

## 📈 Análise Detalhada por Experimento

### 1️⃣ Experimento: Baseline (Sem RAG)

**Configuração:**
```json
{
  "use_rag": false,
  "llm": "gemini-2.5-flash"
}
```

**Resposta Gerada:**
```
preciso informar que a **Lei nº 15.270, de 2025, não existe 
na legislação brasileira atual.**

As leis federais são numeradas sequencialmente dentro de cada ano...
```

**Análise:**
- ❌ **Problema Crítico**: LLM alucinou, afirmando que a lei não existe
- ❌ Sem contexto, o modelo usa conhecimento de corte (2024)
- ⏱️ **Latência alta**: 6.7 segundos
- 📝 **Resposta longa**: 220 tokens (explicação de por que a lei não existe)
- 📊 **BERTScore baixo**: F1=0.567 (baixa similaridade com ground truth)

**Conclusão:** Baseline falha completamente sem acesso ao documento.

---

### 2️⃣ Experimento: Dense Retrieval

**Configuração:**
```json
{
  "use_rag": true,
  "retrieval_method": "dense",
  "k": 5,
  "llm": "gemini-2.5-flash"
}
```

**Chunks Recuperados:** 1 chunk (de 5 solicitados)
```
Chunk: "## 📖 Texto Completo\n\nPresidência da República\nCasa Civil..."
Score: N/A (dense)
```

**Resposta Gerada:**
```
A Lei nº 15.270, de 26 de novembro de 2025, tem os seguintes objetivos:

*   Alterar a Lei nº 9.250, de 26 de dezembro de 1995, e 
    a Lei nº 9.249, de 26 de dezembro de 1995.
*   Instituir a redução do...
```

**Análise:**
- ✅ **Resposta correta**: Baseada no documento real
- ✅ **BERTScore melhor**: F1=0.637 (+12% vs baseline)
- ✅ **Mais eficiente**: 148 tokens (-33%)
- ✅ **Mais rápido**: 3.1s (-54% latência)
- ⚠️ **Poucos chunks**: Apenas 1 de 5 solicitados (possível problema no retrieval)
- 📊 **RAGAS:**
  - Faithfulness: 0.667 (resposta parcialmente fundamentada)
  - Context Recall: 0.333 (33% do contexto relevante recuperado)
  - Context Precision: 1.000 (contexto recuperado é relevante)

**Conclusão:** Dense funciona, mas recupera poucos chunks.

---

### 3️⃣ Experimento: Hybrid Retrieval (70% Dense + 30% BM25)

**Configuração:**
```json
{
  "use_rag": true,
  "retrieval_method": "hybrid",
  "k": 5,
  "dense_weight": 0.7,
  "bm25_weight": 0.3,
  "llm": "gemini-2.5-flash"
}
```

**Chunks Recuperados:** 5 chunks completos
```
1. Chunk e9a0fa0f (score: 0.0163): "Texto Completo\n\nPresidência..."
2. Chunk 6404eb1e (score: 0.0048): "Artigo 8º - Esta Lei entra em vigor..."
3. Chunk 4dfccce9 (score: 0.0047): "parcela do IRPF isenta..."
4. [+2 chunks adicionais]
```

**Resposta Gerada:**
```
A Lei nº 15.270, de 2025, tem como objetivos (Trecho 1):

*   Alterar a Lei nº 9.250, de 26 de dezembro de 1995...
*   Instituir a redução do imposto sobre a...
```

**Análise:**
- ✅ **Máxima eficiência**: 2.7s de latência (-61% vs baseline)
- ✅ **5 chunks completos**: Hybrid recupera todos os chunks solicitados
- ✅ **Melhor faithfulness**: 0.889 (resposta altamente fundamentada)
- ✅ **Alta relevância**: Answer Relevancy = 0.872
- ⚠️ **Context Recall baixo**: 0.000 (possível falso negativo ou ground truth incompleto)
- 📊 **BERTScore**: F1=0.600 (entre baseline e dense)

**Conclusão:** Hybrid é o mais rápido e recupera mais contexto, mas BERTScore intermediário.

---

## 🔍 Insights Importantes

### 1. **Problema: Dense Recupera Poucos Chunks**
- Dense solicitou k=5 mas retornou apenas 1 chunk
- **Possíveis causas:**
  - Threshold de similaridade muito alto
  - Vector store com poucos documentos (36 chunks total)
  - Query muito específica

### 2. **Context Recall = 0 no Hybrid**
- Pode ser:
  - Falso negativo (RAGAS não identificou contexto relevante)
  - Ground truth não corresponde exatamente aos chunks
  - Necessita investigação com mais queries

### 3. **Cortesias Removidas com Sucesso**
- `answer_full` (868 chars) vs `answer_core` (761 chars)
- Limpeza remove ~12% de conteúdo não técnico
- Métricas agora comparam conteúdo puro

### 4. **Max Tokens Corrigido**
- Baseline: 220 tokens (resposta completa)
- RAG: 148-169 tokens (respostas mais concisas)
- Finish reason: STOP (não MAX_TOKENS)

---

## 🎯 Recomendações para Experimento Completo

### ✅ Pontos Positivos (Confirmar com 30 perguntas)
1. RAG melhora BERTScore em ~12%
2. RAG reduz latência em ~50-60%
3. RAG reduz tokens usados em ~25-30%
4. Hybrid recupera mais chunks (5 vs 1)

### ⚠️ Pontos de Atenção
1. **Dense retrieval**: Investigar por que retorna poucos chunks
   - Considerar ajustar `similarity_threshold`
   - Verificar se k=5 é apropriado para dataset pequeno (36 chunks)

2. **Context Recall = 0**: 
   - Pode ser problema específico desta query
   - Avaliar com mais perguntas no experimento completo

3. **BERTScore Hybrid < Dense**:
   - Hybrid recupera mais contexto mas score é menor
   - Pode indicar que mais contexto introduz ruído
   - Ou que chunks adicionais não são tão relevantes

### 🚀 Ações Antes do Experimento Completo

**Opção A: Executar experimento completo como está**
- Pros: Validar tendências com 30 perguntas
- Cons: Dense pode continuar retornando poucos chunks

**Opção B: Ajustar configurações primeiro**
- Ajustar `similarity_threshold` do DenseRetriever
- Testar com k=3 para ver se melhora precisão
- Depois rodar experimento completo

---

## 📊 Métricas Finais (1 query de teste)

### Performance
| Métrica | Baseline | Dense | Hybrid | Variação |
|---------|----------|-------|---------|----------|
| Latência média (ms) | 6767 | 3104 | 2669 | **-61%** ✅ |
| Tokens usados | 220 | 148 | 169 | **-33%** ✅ |
| Chunks recuperados | 0 | 1 | 5 | +5 ✅ |

### Qualidade
| Métrica | Baseline | Dense | Hybrid | Variação |
|---------|----------|-------|---------|----------|
| BERTScore F1 | 0.567 | 0.637 | 0.600 | **+12%** ✅ |
| Answer Relevancy | - | 0.870 | 0.872 | - |
| Faithfulness | - | 0.667 | 0.889 | **+33%** ✅ |
| Context Precision | - | 1.000 | 1.000 | - |
| Context Recall | - | 0.333 | 0.000 | ⚠️ |

---

## 🎬 Próxima Ação Recomendada

**Executar experimento completo com 30 perguntas:**
```bash
PYTHONPATH=/home/decode/workspace/lion /home/decode/workspace/lion/venv/bin/python \
  scripts/run_experiments.py \
  --experiment rag_vs_no_rag \
  --max-questions 30
```

**Tempo estimado:** 15-20 minutos  
**Resultado esperado:** Validar tendências observadas e ter dados estatísticos robustos
