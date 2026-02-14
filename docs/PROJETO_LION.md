# 🦁 LION

## Legal Interpretation and Official Norms

### Assistente Virtual para Dúvidas do IRPF (2026)

---

## 📌 1. Visão Geral do Projeto

O **LION (Legal Interpretation and Official Norms)** é um assistente virtual baseado em arquitetura **RAG (Retrieval-Augmented Generation)** voltado para interpretação normativa do **Imposto de Renda da Pessoa Física (IRPF)**.

O sistema tem como objetivo responder dúvidas tributárias com:

* ✅ Acurácia normativa
* ✅ Rastreabilidade legal
* ✅ Redução de alucinações
* ✅ Fundamentação em fontes oficiais

O projeto surge como resposta à complexidade do sistema tributário brasileiro e à necessidade de uso responsável de LLMs em domínios *high-stakes*.

---

## 🎯 2. Problema de Pesquisa

> Em que medida uma arquitetura RAG otimizada com segmentação semântica é capaz de garantir acurácia normativa e mitigar alucinações em um assistente virtual de IRPF, quando comparada a modelos de linguagem genéricos sem acesso a contexto externo?

---

## 🧠 3. Fundamentação Técnica

### 3.1 Grandes Modelos de Linguagem (LLMs)

Baseados na arquitetura Transformer (Vaswani et al., 2017), LLMs:

* Operam por predição de próximo token
* Possuem conhecimento paramétrico
* Sofrem com:

  * Desatualização
  * Alucinações

---

### 3.2 Arquitetura RAG

Pipeline dividido em duas etapas:

```
Pergunta → Recuperação (Retrieval) → Contexto → Geração → Resposta fundamentada
```

Fases:

1. **Embedding da pergunta**
2. **Busca semântica em base vetorial**
3. **Montagem do prompt com contexto recuperado**
4. **Geração da resposta pelo LLM**
5. **Entrega com rastreabilidade**

---

### 3.3 Representação Vetorial

* Modelo de embeddings (ex: BGE-m3 ou text-embedding-3-large)
* Banco vetorial (ex: ChromaDB)
* Métrica de similaridade: Cosine Similarity

---

### 3.4 Estratégias de Segmentação (Chunking)

Serão comparadas:

| Estratégia      | Descrição                     | Risco                  |
| --------------- | ----------------------------- | ---------------------- |
| Sliding Window  | Janela fixa com overlap       | Fragmentação normativa |
| Structure-aware | Respeita artigos e parágrafos | Mais complexo          |

---

### 3.5 Métricas de Avaliação

* **BERTScore (F1)** → Similaridade semântica
* **RAGAS**:

  * Faithfulness
  * Answer Relevancy
* Precision / Recall (retrieval)

---

## 🏗️ 4. Arquitetura do Sistema

- `docs/ARQUITETURA.md` (v2.0)

---

## 📚 5. Base de Conhecimento

Fontes oficiais utilizadas:

* Instrução Normativa RFB nº 2.255/2025
* Perguntas e Respostas IRPF 2025 ("Perguntão")
* Lei nº 15.263/2025 (Linguagem Simples)

Todos os dados são públicos.

---

## 🔬 6. Método Experimental

### 6.1 Dataset

* 50 questões do Perguntão IRPF 2025
* Ground truth oficial

---

### 6.2 Experimentos

Serão realizados três comparativos:

1. RAG com chunking fixo
2. RAG com chunking estrutural
3. LLM sem RAG (baseline)
.... TODO. VER OUTROS COMPARATIVOS E EXPERIMENTOS. 


---

### 6.3 Variáveis Observadas

| Métrica      | Objetivo                          |
| ------------ | --------------------------------- |
| Precision    | Qualidade da recuperação          |
| Recall       | Cobertura normativa               |
| Faithfulness | Fidelidade à fonte                |
| BERTScore    | Similaridade com resposta oficial |

---

## 📈 7. Hipótese

**H1:**
A arquitetura RAG com base curada e segmentação estrutural reduzirá significativamente alucinações e aumentará a acurácia normativa em comparação ao uso isolado de LLMs.

---

## 🛡️ 8. Princípios de IA Responsável

* Não utilização de dados pessoais
* Base exclusivamente oficial
* Respostas fundamentadas
* Mitigação ativa de alucinações
* Transparência de fontes

---

## 📅 9. Roadmap de Desenvolvimento

### Stage 1 – Ideação

* Escrita do projeto

### Stage 2 – Planejamento
* Escrita do projeto 
* Definição da arquitetura
* Estrutura do repositório

### Stage 3 – Desenvolvimento

* Implementação do pipeline RAG
* Testes A/B de chunking

### Stage 4 – Resultados

* Execução experimental
* Coleta de métricas

### Stage 5 – Redação

* Consolidação dos resultados

### Stage 6 – Defesa

* Apresentação final

---

## 🚀 10. Próximos Passos Técnicos

* [ ] Implementar pipeline de ingestão
* [ ] Criar segmentador estrutural
* [ ] Gerar embeddings
* [ ] Implementar retriever
* [ ] Criar prompt template com instruções restritivas
* [ ] Construir módulo de avaliação automática
* [ ] Implementar baseline

---

## 📊 11. Resultados Esperados

* Redução significativa de alucinações
* Maior fidelidade normativa
* Melhor performance que LLM zero-shot
* Guia replicável para Legal AI governamental

---

## 👨‍💻 Autor

Ronen Rodrigues Silva Filho
Goiânia – 2026

---

# 🧩 Versão Atual do Projeto

**Status:** Planejamento → Início do Desenvolvimento
**Versão:** 0.1
**Arquitetura:** RAG Experimental