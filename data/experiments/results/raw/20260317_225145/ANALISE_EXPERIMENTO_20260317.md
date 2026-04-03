# Análise do Experimento: Large vs Small Model com BM25

**Data:** 17 de março de 2026  
**Timestamp:** 20260317_225145  
**Pergunta Testada:** "Quais os objetivos da Lei nº 15.270, de 2025?"  

---

## 📊 Resumo Executivo

Experimento científico comparando **Gemini (grande)** vs **Llama 3.1 8B (pequeno)** com diferentes configurações de RAG usando BM25.

### Principais Descobertas:

| Métrica | Gemini | Llama |
|---------|--------|-------|
| **Latência (sem RAG)** | 3.13s | 709ms |
| **Velocidade Relativa** | 1x | 4.4x mais rápido |
| **Tokens (sem RAG)** | 506 | 328 |
| **Melhor Relevância** | k=10 (0.994) | k=10 (0.994) |
| **Melhor Fidelidade** | k=5 (0.818) | k=5 (1.0) ✨ |

---

## 🔍 Análise Detalhada por Configuração

### 1️⃣ BASELINE (Sem RAG)

**Gemini Baseline:**
- Latência: 3,128ms (lento)
- Tokens: 506
- Sem acesso a chunks
- Baseline para comparação

**Llama Baseline:**
- Latência: 709ms (**4.4x mais rápido** 🚀)
- Tokens: 328 (35% menos tokens)
- **Conclusão:** Llama é significativamente mais rápido sem RAG

---

### 2️⃣ RAG com k=3 (Contexto Mínimo)

**Gemini + BM25 k=3:**
- Latência: 2,114ms
- Chunks: 3
- Tokens: 102 (redução de 80% vs baseline!)
- Faithfulness: 0.75
- Answer Relevancy: 0.0 ❌ (resposta não relevante)
- **Problema:** Chunks insuficientes causam baixa relevância

**Llama + BM25 k=3:**
- Latência: 769ms
- Chunks: 3
- Tokens: 741 (+ contexto aumentou tokens)
- Faithfulness: 0.571
- Answer Relevancy: 0.0 ❌ (mesma questão)
- **Problema:** Similar ao Gemini, k=3 é insuficiente

---

### 3️⃣ RAG com k=5 (Contexto Padrão)

**Gemini + BM25 k=5:**
- Latência: 2,882ms
- Chunks: 5
- Tokens: 365
- Faithfulness: **0.818** ✨ (muito bom)
- Context Precision: 0.25 (25% dos chunks relevantes)
- Answer Relevancy: 0.0 (ainda problemático)
- **Análise:** Gemini produz respostas fiéis mas não tão relevantes

**Llama + BM25 k=5:** ⭐ **MELHOR COMBINAÇÃO PARA k=5**
- Latência: 989ms
- Chunks: 5
- Tokens: 1,617 (usa muito mais contexto)
- Faithfulness: **1.0** 🏆 (perfeito! Resposta totalmente fiel)
- Answer Relevancy: **0.924** 🎯 (MUITO relevante)
- Context Precision: 0.25
- **Conclusão:** Llama com k=5 é a melhor opção para qualidade

---

### 4️⃣ RAG com k=10 (Contexto Rico)

**Gemini + BM25 k=10:** ⭐ **MELHOR PARA GEMINI**
- Latência: 3,456ms
- Chunks: 10
- Tokens: 344
- Faithfulness: 0.944 ✨ (excelente)
- Answer Relevancy: **0.994** 🏆 (praticamente perfeito!)
- Context Recall: **1.0** (recuperou toda a informação relevante)
- Context Precision: 0.308 (31% de relevância)
- **Análise:** Com mais contexto, Gemini melhora drasticamente

**Llama + BM25 k=10:**
- Latência: 992ms (praticamente mesmo tempo que k=5)
- Chunks: 10
- Tokens: 4,539 (processamento muito mais pesado)
- Faithfulness: 0.666 (piora vs k=5!)
- Answer Relevancy: **0.994** (mantém relevância alta)
- Context Recall: **1.0**
- **Problema:** Aumento de contexto prejudica fidelidade, mais tokens (4.5x!)

---

## 📈 Comparativa de Métricas

### Latência Total (ms)
```
Gemini Baseline:    3,129 ms
Gemini k=3:         2,114 ms (-32%)
Gemini k=5:         2,882 ms (-8%)
Gemini k=10:        3,456 ms (+10%) ⬆️

Llama Baseline:     709 ms
Llama k=3:          769 ms (+9%)
Llama k=5:          989 ms (+39%)
Llama k=10:         992 ms (+40%)
```

### Faithfulness (Fidelidade)
```
Gemini k=3:         0.750 ✓
Gemini k=5:         0.818 ✓✓
Gemini k=10:        0.944 ✓✓✓

Llama k=3:          0.571 ✓
Llama k=5:          1.000 ✓✓✓✓ 🏆
Llama k=10:         0.666 ✓✓ (piora!)
```

### Answer Relevancy (Relevância da Resposta)
```
Gemini k=3:         0.000 ❌
Gemini k=5:         0.000 ❌
Gemini k=10:        0.994 🏆 EXCELENTE

Llama k=3:          0.000 ❌
Llama k=5:          0.924 ✓✓✓ MUITO BOM
Llama k=10:         0.994 🏆 EXCELENTE
```

---

## 🎯 Recomendações

### Para Latência (Velocidade):
1. **Llama Baseline** - 709ms (sem RAG)
2. **Llama k=3** - 769ms (+ contexto rápido)
3. **Llama k=5** - 989ms (equilíbrio)

### Para Qualidade (Relevância + Fidelidade):
1. **Llama k=5** - Melhor balanço (0.924 relevância, 1.0 fidelidade)
2. **Gemini k=10** - Máxima relevância (0.994)
3. **Llama k=10** - Máxima relevância, mas menos fiel

### Recomendação Prática:
```
USE: Llama 3.1 8B + RAG BM25 k=5

Razões:
✅ Latência: 989ms (aceitável)
✅ Faithfulness: 1.0 (respostas 100% fiéis ao contexto)
✅ Relevancy: 0.924 (muito relevante)
✅ Tokens: 1,617 (razoável)
✅ Economia: Menor custo que Gemini
```

---

## 📌 Insights Técnicos

### Comportamento do Gemini:
- **Lento:** Latência 3-3.5s consistentemente
- **Eficiente com tokens:** k=10 usa apenas 344 tokens
- **Precisa de contexto:** Relevância salta de 0.0 → 0.994 com k=10
- **Fidelidade cresce:** Com mais chunks (k=10: 0.944)

### Comportamento do Llama 8B:
- **Rápido:** Latência 700-1000ms (4-5x mais rápido)
- **Usa muito contexto:** k=10 usa 4,539 tokens
- **Ótimo com k=5:** Ponto ótimo de qualidade
- **Degrada com k=10:** Fidelidade cai (1.0 → 0.666)

### Efeito do Tamanho de Contexto (k):
- **k=3:** Insuficiente, answer_relevancy = 0.0 para ambos
- **k=5:** Ponto ótimo para Llama (equilibrado)
- **k=10:** Ótimo para Gemini (máxima relevância), prejudicial para Llama

---

## 🔬 Conclusões Científicas

1. **Modelos menores podem ser melhores:** Llama 8B supera Gemini em velocidade (4-5x) mantendo qualidade comparável

2. **Tamanho de contexto importa:** Diferentes modelos têm pontos ótimos diferentes (Llama: k=5, Gemini: k=10)

3. **Trade-off Velocidade vs Qualidade:**
   - Sem RAG: Llama é 4.4x mais rápido
   - Com RAG: Ambos competem, Llama k=5 vence em equilíbrio

4. **RAG melhora relevância:** Jump dramático com mais contexto (0.0 → 0.994)

5. **Faithfulness é crítica:** Llama k=5 mantém fidelidade 1.0 enquanto Llama k=10 piora para 0.666

---

## 📊 Tabela Resumida

| Modelo | Config | Latência | Relevância | Fidelidade | Recomendação |
|--------|--------|----------|-----------|-----------|--------------|
| Gemini | Baseline | 3.13s | N/A | N/A | ❌ Não |
| Gemini | k=3 | 2.11s | 0.00 | 0.75 | ❌ Não |
| Gemini | k=5 | 2.88s | 0.00 | 0.82 | ❌ Não |
| Gemini | k=10 | 3.46s | 0.99 | 0.94 | ⚠️ Se máxima qualidade |
| Llama | Baseline | 709ms | N/A | N/A | ✅ Rápido |
| Llama | k=3 | 769ms | 0.00 | 0.57 | ❌ k pequeno |
| **Llama** | **k=5** | **989ms** | **0.92** | **1.00** | **✅ MELHOR** |
| Llama | k=10 | 992ms | 0.99 | 0.67 | ⚠️ Menos fiel |

---

## 🎓 Próximos Passos

1. Testar com múltiplas perguntas (n>1) para validar estatisticamente
2. Implementar cache de embeddings para reduzir latência
3. Tunar k por modelo (Llama: k=5, Gemini: k=10)
4. Habilitar BERTScore quando necessário máxima precisão
5. Considerar fine-tuning de Llama para melhorar fidelidade em k=10
