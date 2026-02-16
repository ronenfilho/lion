# Relatório de Análise: Experimento 4 - Comparação de Modelos
**Projeto LION - Sistema RAG para IRPF 2025**

---

## 📋 Informações Gerais

- **Experimento**: model_comparison (Experimento 4)
- **Data**: 16/02/2026
- **Configurações Testadas**: 2 modelos (teste inicial)
- **Perguntas por Configuração**: 1
- **Dataset**: `manual_rfb_test.json`
- **Objetivo**: Comparar modelo cloud (Gemini Flash) vs modelo local quantizado (TinyLlama 1.1B)

---

## 🎯 Objetivo do Experimento

Avaliar se modelos locais quantizados (<1B parâmetros) podem substituir modelos cloud em cenários de menor complexidade, visando:

1. **Redução de custos**: Modelos locais não têm custo de API
2. **Redução de latência**: Inferência local pode ser mais rápida que chamadas API
3. **Privacidade**: Dados não saem do ambiente local
4. **Independência**: Não depender de disponibilidade de serviços externos

---

## ⚙️ Configurações Testadas

### Baseline: Gemini 2.5 Flash (Cloud)
```json
{
  "use_rag": true,
  "retrieval_method": "dense",
  "k": 3,
  "llm": "gemini-2.5-flash"
}
```
- Modelo cloud da Google (última versão)
- Inferência em servidores Google (TPU/GPU otimizadas)
- Custo por token (~$0.075/1M tokens input, $0.30/1M output)

### Modelo Local: TinyLlama 1.1B (CPU)
```json
{
  "use_rag": true,
  "retrieval_method": "dense",
  "k": 3,
  "llm": "local:tinyllama"
}
```
- **Modelo**: TinyLlama/TinyLlama-1.1B-Chat-v1.0
- **Parâmetros**: 1.1 bilhões
- **Tamanho**: ~700MB em FP32 (sem quantização 4-bit por falta de GPU)
- **Hardware**: CPU Intel (sem CUDA)
- **Nota**: Quantização 4-bit requer GPU; rodou em FP32 em CPU

---

## 📊 Resultados Comparativos

### Métricas de Qualidade

| Métrica | Gemini Flash | TinyLlama | Δ Absoluta | Δ Relativa |
|---------|--------------|-----------|------------|------------|
| **BERTScore F1** | 0.6365 | 0.6016 | -0.0349 | **-5.5%** |
| BERTScore Precision | 0.6228 | 0.5608 | -0.0620 | -10.0% |
| BERTScore Recall | 0.6508 | 0.6489 | -0.0019 | -0.3% |
| **Answer Relevancy** | 0.8696 | 0.8397 | -0.0299 | **-3.4%** |
| **Faithfulness** | 0.6667 | 0.3462 | -0.3205 | **-48.1%** ⚠️ |
| Context Precision | 1.0000 | 1.0000 | 0.0000 | 0.0% |
| Context Recall | 0.3333 | 0.3333 | 0.0000 | 0.0% |

### Métricas de Performance

| Métrica | Gemini Flash | TinyLlama | Δ Absoluta | Δ Relativa |
|---------|--------------|-----------|------------|------------|
| **Latência (ms)** | 3,153 | 236,604 | +233,451 | **+7,405%** ⚠️ |
| **Latência (s)** | 3.15 | 236.6 | +233.45 | **~75x mais lento** |
| **Tokens Gerados** | 148 | 1,028 | +880 | +595% |
| Chunks Recuperados | 1 | 1 | 0 | 0% |

---

## 🔍 Análise Detalhada

### 1. Qualidade das Respostas

#### ✅ Métricas Aceitáveis
- **BERTScore F1**: TinyLlama teve -5.5% de queda, ainda aceitável para casos simples
- **Answer Relevancy**: -3.4% de queda, mantém relevância razoável

#### ❌ Problema Crítico: Faithfulness
- **Gemini Flash**: 66.7% de fidelidade ao contexto
- **TinyLlama**: 34.6% de fidelidade (**-48.1%**)
- **Implicação**: TinyLlama "alucina" muito mais, inventando informações não presentes no contexto

### 2. Performance e Latência

#### ❌ Problema Crítico: Latência em CPU

| Modelo | Tempo | Comparação |
|--------|-------|------------|
| Gemini Flash | 3.15s | Baseline |
| TinyLlama (CPU) | 236.6s | **75x mais lento** |

**Análise**:
- Inferência em CPU sem quantização é **inviável** para produção
- 4 minutos por resposta é inaceitável para usuário final
- Gemini Flash, apesar de ser API externa, é 75x mais rápido

**Estimativa com GPU + Quantização 4-bit**:
- Esperado: 1-2s por resposta (redução de 100-200x)
- Isso tornaria competitivo com Gemini Flash

### 3. Verbosidade do Modelo

- **TinyLlama**: 1,028 tokens gerados vs 148 do Gemini (+595%)
- Modelos menores tendem a ser mais verbosos/repetitivos
- Impacta latência e qualidade percebida

---

## 🚨 Limitações do Teste Atual

### 1. Hardware Inadequado
- **Sem GPU CUDA**: Forçou uso de CPU em FP32
- **Sem Quantização 4-bit**: Impossível comprimir modelo sem GPU
- **Impacto**: Latência 100-200x pior que o esperado

### 2. Amostra Reduzida
- Apenas **1 pergunta** testada
- Não representa distribuição de dificuldades
- Resultados podem não generalizar

### 3. Modelos Não Testados
- **Phi-2 (2.7B)**: Não testado (maior que TinyLlama)
- **Qwen2-0.5B**: Não testado (menor que TinyLlama)
- Esses modelos podem ter tradeoffs diferentes

---

## 💡 Conclusões e Recomendações

### ❌ Inviabilidade Atual (CPU Apenas)

**Com CPU apenas, modelos locais são inviáveis**:
1. Latência 75x maior que cloud
2. Faithfulness 48% menor (alucina muito)
3. Experiência de usuário inaceitável (4min por resposta)

### ⏳ Potencial com GPU

**Com GPU + Quantização 4-bit, cenário muda**:

| Cenário | Latência Esperada | F1 Esperado | Viável? |
|---------|-------------------|-------------|---------|
| TinyLlama CPU FP32 | 236s | 0.602 | ❌ Não |
| TinyLlama GPU Q4 | 1-2s | 0.55-0.60 | ⚠️ Talvez |
| Gemini Flash Cloud | 3s | 0.636 | ✅ Sim |

**Estimativa**: Com GPU, TinyLlama seria 2x mais rápido que Gemini, mas com -6% F1.

### 🎯 Recomendações

#### Curto Prazo (Sem GPU)
1. **Usar Gemini Flash exclusivamente**
2. Investir em otimização de prompts e chunking (já feito)
3. Implementar cache de respostas comuns

#### Médio Prazo (Com GPU)
1. **Re-executar experimento 4 com GPU**:
   - TinyLlama 1.1B (Q4)
   - Phi-2 2.7B (Q4)
   - Qwen2-0.5B (Q4)
2. **Implementar arquitetura híbrida** se viável:
   ```
   Query → Classifier → Simples? → TinyLlama GPU (1s, $0)
                      ↓ Complexa? → Gemini Flash (3s, $0.001)
   ```
3. Critério de decisão:
   - **Simples**: Cálculos diretos, consultas objetivas → Local
   - **Complexa**: Interpretação legal, múltiplas regras → Cloud

#### Longo Prazo (Produção)
1. **Cenário A: Híbrido** (com GPU disponível)
   - Classificador de complexidade
   - 60-70% queries simples → Local (economia ~$200-300/mês)
   - 30-40% queries complexas → Cloud
   - Monitoramento A/B testing

2. **Cenário B: Cloud Only** (sem GPU)
   - Gemini Flash exclusivo
   - Cache agressivo (Redis)
   - Otimizar custos via batch processing

---

## 📈 Próximos Passos

### Prioridade 1: Validar GPU
- [ ] Obter acesso a GPU CUDA (Google Colab, AWS, etc.)
- [ ] Re-executar experimento 4 com quantização 4-bit
- [ ] Validar latência <2s e F1 >0.58

### Prioridade 2: Expandir Testes
- [ ] Rodar experimento com 30 perguntas (dataset completo)
- [ ] Testar Phi-2 e Qwen2-0.5B
- [ ] Análise por categoria/dificuldade

### Prioridade 3: Implementar Híbrido (se viável)
- [ ] Criar classificador de complexidade
- [ ] Pipeline de roteamento
- [ ] Monitoramento de qualidade/custo

---

## 📝 Metadados

- **Análise gerada**: 16/02/2026
- **Experimento ID**: model_comparison
- **Configurações**: 2 (gemini_flash_baseline, tinyllama)
- **Perguntas**: 1 por configuração
- **Hardware**: CPU Intel (sem CUDA)
- **Limitação crítica**: Sem GPU para quantização 4-bit

---

## 🔗 Arquivos Relacionados

- Resultados brutos: `experiments/results/model_comparison_*.json`
- Script de experimento: `scripts/run_experiments.py`
- LocalLLMClient: `src/generation/local_llm_client.py`
- Guia de implementação: `docs/GUIA_IMPLEMENTACAO.md`

---

**Conclusão Final**: Sem GPU, modelos locais são inviáveis. Com GPU + quantização, há potencial para arquitetura híbrida que reduza custos mantendo qualidade. Recomenda-se validar com GPU antes de decisão final sobre arquitetura de produção.
