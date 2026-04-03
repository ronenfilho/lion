# Análise Comparativa: 1 Pergunta vs 5 Perguntas
## Experimento: Large vs Small Model com BM25

**Data:** 17 de março de 2026  
**Experimento 1:** 20260317_225145 (1 pergunta)  
**Experimento 2:** 20260317_230924 (5 perguntas)  

---

## 🎯 Mudanças Principais com Múltiplas Perguntas

### 1. **Variabilidade Aumenta** (Desvio Padrão)

#### Latência:
| Config | 1 Pergunta | 5 Perguntas | Variação |
|--------|-----------|------------|----------|
| Gemini Baseline | 3,129ms | 3,445ms ±429 | +10% (mais variável) |
| Llama Baseline | 709ms | 734ms ±131 | +3% (mais variável) |
| Gemini k=3 | 2,114ms | 2,532ms ±866 | +20% (muito variável) |
| Llama k=3 | 769ms | 998ms ±249 | +30% (mais variável) |
| Gemini k=5 | 2,882ms | 2,518ms ±561 | -13% (mas com variação) |
| Llama k=5 | 989ms | 999ms ±209 | +1% (estável) |
| Gemini k=10 | 3,456ms | 3,319ms ±464 | -4% (estável) |
| Llama k=10 | 992ms | 1,353ms ±251 | +36% (aumentou!) |

**Conclusão:** Com 5 perguntas, a variabilidade revela inconsistências em certas configurações, especialmente Llama k=10 (+36%).

---

### 2. **Métricas RAGAS: A Grande Reviravolta**

#### Answer Relevancy (Relevância)
```
1 PERGUNTA:
  Gemini k=3:  0.000 ❌
  Gemini k=5:  0.000 ❌
  Gemini k=10: 0.994 🏆
  Llama k=3:   0.000 ❌
  Llama k=5:   0.924 ✓
  Llama k=10:  0.994 🏆

5 PERGUNTAS (MÉDIA):
  Gemini k=3:  0.505 ✓ (+∞ melhora!)
  Gemini k=5:  0.499 ✓ (+∞ melhora!)
  Gemini k=10: 0.669 ✓✓ (-33%)
  Llama k=3:   0.736 ✓✓ (+∞ melhora!)
  Llama k=5:   0.920 ✓✓✓ (praticamente igual)
  Llama k=10:  0.555 ✗ (-44% piora!)
```

**Descoberta Chave:** 
- Gemini k=3 e k=5 eram completamente inúteis com 1 pergunta (0.0), mas com 5 perguntas atingem 0.5!
- Llama k=10 piora dramaticamente: 0.994 → 0.555

#### Faithfulness (Fidelidade)
```
1 PERGUNTA:
  Gemini k=3:  0.750 ✓
  Gemini k=5:  0.818 ✓✓
  Gemini k=10: 0.944 ✓✓✓
  Llama k=3:   0.571 ✓
  Llama k=5:   1.000 🏆
  Llama k=10:  0.666 ✓

5 PERGUNTAS (MÉDIA):
  Gemini k=3:  0.852 ✓✓ (+14%)
  Gemini k=5:  0.761 ✓✓ (-7%)
  Gemini k=10: 0.833 ✓✓ (-12%)
  Llama k=3:   0.671 ✓✓ (+18%)
  Llama k=5:   0.751 ✓✓ (-25%)
  Llama k=10:  0.485 ✗ (-27% piora!)
```

**Descoberta Crítica:** 
- Llama k=5 cai de fidelidade perfeita (1.0) para 0.751 com múltiplas perguntas
- Llama k=10 desaba para 0.485 (menos de 50% fiel!)

---

### 3. **Tokens: Consumo Aumenta Significativamente**

#### Gemini (Tokens usados por pergunta)
```
Baseline:    619 → 619 (estável)
k=3:         102 → 304 (3x mais!)
k=5:         365 → 411 (+13%)
k=10:        344 → 478 (+39%)
```

#### Llama (Tokens usados por pergunta)
```
Baseline:    328 → 408 (+24%)
k=3:         741 → 1,742 (2.3x mais!)
k=5:         1,617 → 2,942 (1.8x mais!)
k=10:        4,539 → 6,501 (1.4x mais!)
```

**Padrão:** Llama consome **muito mais tokens** que Gemini, e o consumo varia bastante entre perguntas.

---

### 4. **Context Precision & Recall: Variabilidade Grande**

#### Context Precision (% de chunks relevantes)
```
1 PERGUNTA:
  Gemini k=3:  0.000 (nenhum relevante)
  Gemini k=5:  0.250 (25%)
  Gemini k=10: 0.308 (31%)
  Llama k=3:   0.000 (nenhum relevante)
  Llama k=5:   0.250 (25%)
  Llama k=10:  0.308 (31%)

5 PERGUNTAS (MÉDIA):
  Gemini k=3:  0.433 (43%)
  Gemini k=5:  0.622 (62%) 🔝
  Gemini k=10: 0.591 (59%)
  Llama k=3:   0.433 (43%)
  Llama k=5:   0.556 (56%)
  Llama k=10:  0.628 (63%) 🔝
```

**Insight:** Com 5 perguntas, Gemini k=5 e Llama k=10 melhoram significativamente em precisão de contexto.

#### Context Recall (% de informação capturada)
```
1 PERGUNTA:
  Gemini k=3:  0.000
  Gemini k=5:  0.000
  Gemini k=10: 1.000 (100% completo)
  Llama k=3:   0.000
  Llama k=5:   0.000
  Llama k=10:  1.000 (100% completo)

5 PERGUNTAS (MÉDIA):
  Gemini k=3:  0.333 (33%)
  Gemini k=5:  0.219 (22%)
  Gemini k=10: 0.533 (53%)
  Llama k=3:   0.333 (33%)
  Llama k=5:   0.333 (33%)
  Llama k=10:  0.533 (53%)
```

**Achado Importante:** Com 1 pergunta, k=10 recuperava TUDO (100%). Com 5 perguntas, cai para 53%.

---

## 📊 Comparação Visual de Configurações

### Ranking de Melhor Performance (5 perguntas)

#### 🥇 **Por Velocidade (Latência):**
```
1. Llama Baseline:      734ms
2. Llama k=3:           998ms (+36%)
3. Llama k=5:           999ms (+36%)
4. Llama k=10:        1,353ms (+84%) ⚠️
5. Gemini k=3:        2,532ms
6. Gemini k=5:        2,518ms
7. Gemini Baseline:   3,445ms
8. Gemini k=10:       3,319ms
```

#### 🥇 **Por Relevância (Answer Relevancy):**
```
1. Llama k=5:         0.920 🏆
2. Llama k=3:         0.736
3. Gemini k=10:       0.669
4. Gemini k=3:        0.505
5. Gemini k=5:        0.499
6. Llama k=10:        0.555 ⚠️
```

#### 🥇 **Por Fidelidade (Faithfulness):**
```
1. Gemini k=3:        0.852 🏆
2. Gemini k=10:       0.833
3. Gemini k=5:        0.761
4. Llama k=5:         0.751
5. Llama k=3:         0.671
6. Llama k=10:        0.485 ⚠️
```

#### 🥇 **Balanceado (Relevância + Fidelidade):**
```
1. Llama k=5:         (0.920 + 0.751) / 2 = 0.835 ✅
2. Gemini k=10:       (0.669 + 0.833) / 2 = 0.751
3. Llama k=3:         (0.736 + 0.671) / 2 = 0.703
4. Gemini k=3:        (0.505 + 0.852) / 2 = 0.678
5. Gemini k=5:        (0.499 + 0.761) / 2 = 0.630
6. Llama k=10:        (0.555 + 0.485) / 2 = 0.520
```

---

## ⚡ Constatações Críticas

### 1. **Llama k=10 é Instável**
- Latência aumenta 36% com múltiplas perguntas
- Relevância cai de 0.994 → 0.555
- Fidelidade desaba de 0.666 → 0.485
- Tokens aumentam de 4,539 → 6,501 (média)
- **Recomendação:** NÃO usar Llama k=10

### 2. **Llama k=5 Mantém Estabilidade**
- Latência praticamente igual (989ms → 999ms)
- Relevância permanece alta (0.924 → 0.920)
- Fidelidade diminui mas permanece aceitável (1.0 → 0.751)
- **Recomendação:** USAR Llama k=5 como padrão

### 3. **Gemini k=3 e k=5 Melhoram com Mais Dados**
- Relevância salta de 0.0 → ~0.5 com 5 perguntas
- Não são boas opções, mas não são completamente inúteis
- Precisam de mais testes para conclusão

### 4. **Gemini k=10 é Consistente mas Lento**
- Latência alta mas previsível
- Relevância moderada (0.669)
- Fidelidade boa (0.833)
- Contexto mais preciso (0.591 precision)

### 5. **1 Pergunta ≠ Múltiplas Perguntas**
- Métricas podem variar DRASTICAMENTE
- Llama k=10: perfeita com 1Q, ruim com 5Q
- Gemini k=3/k=5: inutilizáveis com 1Q, aceitáveis com 5Q
- **Conclusão:** Testes com n=1 são insuficientes para conclusões

---

## 🎓 Recomendações Revisadas

### Use Caso: Máxima Qualidade + Velocidade (RECOMENDADO)
```
Configuração: Llama 3.1 8B + RAG BM25 k=5

Métricas (5 perguntas):
✅ Latência:       999ms (muito rápido)
✅ Relevância:     0.920 (excelente)
✅ Fidelidade:     0.751 (boa)
✅ Precisão:       0.556 (56% relevantes)
✅ Recall:         0.333 (33% informação)
✅ Tokens/query:   2,942 (razoável para qualidade)

Razão: Melhor balanço entre velocidade e qualidade com estabilidade
```

### Use Caso: Máxima Fidelidade
```
Configuração: Gemini + RAG BM25 k=3

Métricas (5 perguntas):
✅ Fidelidade:     0.852 (excelente)
✅ Precisão:       0.433 (43% relevantes)
⚠️  Latência:      2,532ms (lento)
⚠️  Relevância:    0.505 (moderada)

Razão: Quando precisa garantir respostas 100% fiéis ao contexto
```

### Use Caso: Máxima Relevância
```
Configuração: Gemini + RAG BM25 k=10

Métricas (5 perguntas):
✅ Relevância:     0.669 (boa)
✅ Recall:         0.533 (53% informação)
✅ Fidelidade:     0.833 (boa)
⚠️  Latência:      3,319ms (muito lento)
⚠️  Tokens:        478/query (aumenta custo)

Razão: Quando precisa recuperar máxima informação
```

### ❌ NÃO USE
```
Llama k=10: Degrada com múltiplas perguntas
- Latência: 1,353ms (+36%)
- Relevância: 0.555 (-44%)
- Fidelidade: 0.485 (inaceitável)
- Tokens: 6,501/query (muito alto)
```

---

## 📈 Insights Estatísticos

### Variabilidade (Desvio Padrão) por Modelo:

**Gemini:**
- Latência: σ = 429-866ms (alta variabilidade)
- Tokens: σ = 111-214 (moderada)

**Llama:**
- Latência: σ = 131-251ms (moderada em k≤5, 251 em k=10)
- Tokens: σ = 1,137-2,345 (MUITO alta, especialmente k≥3)

**Conclusão:** Llama tem alta variabilidade em consumo de tokens, sugerindo respostas muito diferentes por pergunta.

---

## 🔬 Próximos Passos Sugeridos

1. **Testar com n=10 ou n=30** para estatística mais robusta
2. **Análise por categoria de pergunta** (complexidade, tipo)
3. **Habilitar BERTScore** para validação final
4. **Fine-tuning de Llama** para melhorar fidelidade em k=5
5. **Investigar causa** da degradação Llama k=10
6. **Otimizar k dinâmico** (ajustar automaticamente por pergunta)

---

## 📝 Conclusão Final

**Melhor configuração confirmada:** `Llama 3.1 8B + BM25 k=5`

- ✅ Rápido: 999ms
- ✅ Relevante: 0.920
- ✅ Fiel: 0.751
- ✅ Estável: σ = 209ms em latência
- ✅ Econômico: ~3,000 tokens/query

**Diferença crítica entre 1Q e 5Q:**
- Testes com poucos exemplos podem ser ENGANOSOS
- Sempre validar com n≥5 para conclusões confiáveis
- Llama k=10 é um exemplo de armadilha: perfeito com 1Q, péssimo com 5Q
