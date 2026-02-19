# 🦁 LION - Legal Interpretation and Official Norms

Assistente Virtual RAG para IRPF (2026) - Interpretação normativa com IA responsável

[![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)](https://github.com/ronenfilho/lion)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)

---

## 📌 Visão Geral

Sistema RAG (Retrieval-Augmented Generation) para consultas sobre **Imposto de Renda da Pessoa Física (IRPF)** com:
- ✅ Fundamentação em fontes oficiais da RFB
- ✅ Rastreabilidade legal completa
- ✅ Redução de alucinações via guardrails
- ✅ Sem uso de dados pessoais

---

## 🎯 Problema de Pesquisa

> Em que medida uma arquitetura RAG otimizada com segmentação semântica é capaz de garantir acurácia normativa e mitigar alucinações em um assistente virtual de IRPF, quando comparada a modelos de linguagem genéricos sem acesso a contexto externo?

---

## 🏗️ Arquitetura

```
Usuário → Query Understanding → Hybrid Retrieval → Context Builder → LLM + Guardrails → Resposta
```

**Componentes**: Ingestão estrutural | Busca híbrida (dense 70% + BM25 30%) | Gemini/Groq | Validação de citações

**Base**: IN RFB 2.255/2025, Perguntão IRPF 2025, Lei 15.263/2025

---

## 🔬 Experimentos

| ID | Foco | Objetivo |
|----|------|----------|
| **1** | RAG vs Sem RAG | Ganho de acurácia |
| **2** | LLM Pequeno+RAG vs Grande | Arquitetura vs tamanho |
| **3** | Chunking Estrutural vs Fixo | Melhor segmentação |
| **4** | Dense vs Hybrid | Impacto BM25 |
| **5** | Few-shot vs RAG | Exemplos substituem retrieval? |

### Métricas de Avaliação

#### Performance
- **latency_ms**: Tempo total de processamento (ms). Ex: 1176ms
- **tokens_used**: Tokens consumidos pelo LLM. Ex: 1423 (impacta custo)
- **num_chunks**: Quantidade de trechos recuperados. Ex: k=3

#### Qualidade Semântica (BERTScore)
- **bertscore_precision**: % da resposta gerada presente no ground truth (evita info incorreta). Ex: 0.57
- **bertscore_recall**: % do ground truth capturado na resposta (completude). Ex: 0.65
- **bertscore_f1**: Média harmônica precision/recall - **métrica principal de qualidade**. Ex: 0.61

#### Qualidade RAG (RAGAS)
- **answer_relevancy**: Relevância da resposta à pergunta (sem divagações). Ex: 0.90
- **faithfulness**: Fidelidade aos chunks recuperados (anti-alucinação). Ex: 0.80
- **context_precision**: Qualidade do ranking dos chunks recuperados. Ex: 0.99
- **context_recall**: % do ground truth encontrado nos chunks (eficácia do retrieval). Ex: 0.33

---

## 🚀 Quick Start

```bash
# Setup
git clone https://github.com/ronenfilho/lion.git && cd lion
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Editar com API keys

# Uso
python scripts/3_run_experiments.py --experiment model_comparison --max-questions 5
python scripts/4_analyze_results.py --experiment model_comparison
```

**API Python**:
```python
from src.pipeline.rag_pipeline import RAGPipeline

rag = RAGPipeline({'top_k': 5, 'use_reranking': True})
result = rag.query("Quem é obrigado a declarar IRPF 2025?")
print(result['answer'], result['chunks'])
```

---

## 📊 Resultados Esperados

**Hipóteses**:
- H1: RAG reduz alucinações vs LLM sem contexto
- H2: LLM 8B+RAG supera LLM grande sem RAG em fidelidade
- H3: Chunking estrutural aumenta precisão
- H4: Busca híbrida melhora Precision

---

## 🛡️ IA Responsável

✅ Apenas fontes públicas oficiais | ✅ Transparência total | ✅ Sem dados pessoais | ✅ Disclaimers obrigatórios | ✅ Detecção PII | ✅ Anti prompt-injection

---

## 📖 Documentação

- [PROJETO_LION.md](docs/PROJETO_LION.md) - Fundamentação teórica
- [ARQUITETURA.md](docs/ARQUITETURA.md) - Detalhes técnicos v2.0
- [GUIA_IMPLEMENTACAO.md](docs/GUIA_IMPLEMENTACAO.md) - Passo a passo

---

## 🧪 Stack

**Core**: Python 3.10+ | LangChain | ChromaDB | OpenAI/Google/Groq/Local
**Embeddings**: models/gemini-embedding-001
**Eval**: RAGAS | BERTScore | Custom metrics  
**Infra**: FastAPI | Streamlit | Docker

---

## 👨‍💻 Autor

**Ronen Rodrigues Silva Filho** | 2026  
📧 Issues: [github.com/ronenfilho/lion/issues](https://github.com/ronenfilho/lion/issues)

---

## 📚 Citação

```bibtex
@misc{silva2026lion,
  title={LION: Legal Interpretation and Official Norms - Um Assistente Virtual RAG para IRPF},
  author={Silva Filho, Ronen Rodrigues},
  year={2026},
  publisher={GitHub},
  url={https://github.com/ronenfilho/lion}
}
```

---

**Última atualização**: 16/02/2026 | **Licença**: MIT

<div align="center">⭐ Star se este projeto foi útil!</div>
