# 🦁 LION - Legal Interpretation and Official Norms

## Assistente Virtual para Dúvidas do IRPF (2026) com Arquitetura RAG

[![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)](https://github.com/ronenfilho/lion)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 Visão Geral

O **LION** é um assistente virtual baseado em **RAG (Retrieval-Augmented Generation)** para interpretação normativa do **Imposto de Renda da Pessoa Física (IRPF)**. 

O sistema garante:
- ✅ **Acurácia normativa** com fundamentação em fontes oficiais
- ✅ **Rastreabilidade legal** completa
- ✅ **Redução de alucinações** através de guardrails
- ✅ **IA Responsável** sem uso de dados pessoais

---

## 🎯 Problema de Pesquisa

> Em que medida uma arquitetura RAG otimizada com segmentação semântica é capaz de garantir acurácia normativa e mitigar alucinações em um assistente virtual de IRPF, quando comparada a modelos de linguagem genéricos sem acesso a contexto externo?

---

## 🏗️ Arquitetura

### Visão Geral do Sistema

```
┌────────────────────┐
│    Usuário         │
└─────────┬──────────┘
          │
          ▼
┌─────────────────────┐
│ Query Understanding │  ← Intent Classification
└─────────┬───────────┘    Entity Extraction
          │                Normalization
          ▼
┌─────────────────────┐
│ Hybrid Retrieval    │  ← Dense (70%) + Sparse (30%)
│  + Re-ranking       │    BM25 + Embeddings
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Context Builder     │  ← Top-5 chunks
└─────────┬───────────┘    + Metadata
          │
          ▼
┌─────────────────────┐
│ LLM Generation      │  ← Prompt Engineering
│  + Guardrails       │    Citation Validation
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Resposta Final     │  ← Com fontes citadas
└─────────────────────┘    + Disclaimer
```

### Componentes Principais

1. **📥 Ingestão**: Extração, limpeza e segmentação estrutural de documentos normativos
2. **🔍 Retrieval Híbrido**: Busca vetorial + BM25 + Re-ranking
3. **🧠 Geração**: LLMs com prompt engineering otimizado
4. **🛡️ Guardrails**: Validação de entrada/saída para segurança
5. **📊 Avaliação**: BERTScore, RAGAS e métricas customizadas
6. **💾 Cache Semântico**: Redução de latência e custos

---

## 📚 Base de Conhecimento

### Fontes Oficiais

- **Instrução Normativa RFB nº 2.255/2025**
- **Perguntas e Respostas IRPF 2025** ("Perguntão")
- **Lei nº 15.263/2025** (Linguagem Simples)

> Todos os dados são públicos e oficiais da Receita Federal do Brasil.

---

## 🔬 Metodologia Experimental

### Experimentos Planejados

| ID | Descrição | Objetivo |
|----|-----------|----------|
| **Exp 1** | RAG vs Sem RAG (Gemini) | Medir ganho de acurácia |
| **Exp 2** | LLM Grande vs Pequeno+RAG | Validar arquitetura vs tamanho |
| **Exp 3** | Chunking Fixo vs Estrutural | Melhor estratégia de segmentação |
| **Exp 4** | Few-shot vs RAG | Exemplos substituem retrieval? |
| **Exp 5** | Dense vs Hybrid Retrieval | Impacto de BM25 |

### Métricas

- **BERTScore F1**: Similaridade semântica com resposta oficial
- **Faithfulness (RAGAS)**: Fidelidade às fontes
- **Answer Relevancy**: Relevância da resposta
- **Precision@5 / Recall@5**: Qualidade do retrieval
- **Citation Accuracy**: % de citações corretas

---

## 🚀 Quick Start

### Instalação

```bash
# Clonar repositório
git clone https://github.com/ronenfilho/lion.git
cd lion

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas API keys
```

### Uso Básico

```python
from src.rag_pipeline import RAGPipeline

# Inicializar pipeline
config = {
    'use_reranking': True,
    'enable_cache': True,
    'top_k': 5
}
rag = RAGPipeline(config)

# Fazer pergunta
result = rag.query("Quem é obrigado a declarar o IRPF 2025?")

print(result['answer'])
# Imprime resposta fundamentada com citações

print(result['chunks'])
# Mostra chunks recuperados com fontes
```

### Executar Experimentos

```bash
# Rodar experimento específico
python scripts/3_run_experiments.py --config experiments/configs/exp_001_gemini_rag.yaml

# Analisar resultados
python scripts/generate_report.py --experiment exp_001
```

---

## 📂 Estrutura do Projeto

`ARQUITETURA.md`

---

## 📊 Resultados Esperados

### Hipóteses

- **H1**: RAG reduz alucinações em **30-40%** vs LLM sem contexto
- **H2**: LLM pequeno (8B) + RAG supera LLM grande sem RAG em **fidelidade normativa**
- **H3**: Chunking estrutural aumenta **precisão em 15-20%**
- **H4**: Busca híbrida melhora **Precision@5 em 10-15%**

---

## 🛡️ IA Responsável

### Princípios

- ✅ Apenas fontes oficiais públicas
- ✅ Transparência total de fontes
- ✅ Sem dados pessoais ou sintéticos
- ✅ Disclaimers em todas respostas
- ✅ Não constitui consultoria jurídica

### Segurança

- Detecção automática de PII (CPF, email, etc)
- Proteção contra prompt injection
- Validação de citações
- Rate limiting
- Logs estruturados para auditoria

---

## 📖 Documentação

### Documentos Principais

| Documento | Descrição |
|-----------|-----------|
| [PROJETO_LION.md](docs/PROJETO_LION.md) | Visão geral e fundamentação teórica |
| [ARQUITETURA.md](docs/ARQUITETURA.md) | Arquitetura técnica detalhada (v2.0) |
| [MELHORIAS_ARQUITETURA.md](docs/MELHORIAS_ARQUITETURA.md) | Melhorias implementadas |
| [GUIA_IMPLEMENTACAO.md](docs/GUIA_IMPLEMENTACAO.md) | Passo a passo de implementação |

### Arquitetura Avançada (v2.0)

A arquitetura foi expandida com:

- 🆕 **Query Understanding Layer** (intent classification, entity extraction)
- 🔍 **Hybrid Search** (Dense + Sparse + Re-ranking)
- 🛡️ **Guardrails** completos (input/output validation)
- 💾 **Semantic Caching** multi-camadas
- 📊 **Observabilidade** estruturada (logs, métricas, tracing)
- 🎯 **Prompt Engineering** otimizado para domínio legal
- 🚀 **Produção-ready** (deploy, escalabilidade, custos)

Ver [MELHORIAS_ARQUITETURA.md](docs/MELHORIAS_ARQUITETURA.md) para detalhes completos.

---

## 🧪 Tecnologias

### Core
- **Python 3.10+**
- **LangChain / LlamaIndex** - Framework RAG
- **ChromaDB / Qdrant** - Vector store
- **OpenAI / Anthropic / Google** - LLM providers

### Embeddings
- text-embedding-3-large (OpenAI)
- BGE-m3 (BAAI)
- multilingual-e5-large

### Evaluation
- RAGAS
- BERTScore
- Custom metrics (Citation Accuracy, Normative Coverage)

### Infraestrutura
- FastAPI (API REST)
- Streamlit (Interface)
- Prometheus + Grafana (Monitoramento)
- Docker (Containerização)

---

## 📈 Roadmap

### ✅ Fase 1: Planejamento (Concluída)
- Definição do problema
- Arquitetura detalhada
- Estrutura do projeto

### 🔄 Fase 2: Desenvolvimento (Em Andamento)
- [ ] Implementação do pipeline de ingestão
- [ ] Retrieval híbrido + re-ranking
- [ ] Generation layer + guardrails
- [ ] Sistema de avaliação

### 📊 Fase 3: Experimentação
- [ ] Execução dos 5 experimentos
- [ ] Análise estatística
- [ ] Validação de hipóteses

### 📝 Fase 4: Documentação
- [ ] Relatório final
- [ ] Artigo científico
- [ ] Apresentação

### 🚀 Fase 5: Produção (Opcional)
- [ ] API REST
- [ ] Interface web
- [ ] Deploy cloud
- [ ] Monitoramento

---

## 📅 Cronograma de Implementação

- [x] **Fase 1: Setup e Infra**
- [x] **Fase 2: Módulo de Ingestão**
- [x] **Fase 3: Processamento e Segmentação**
- [x] **Fase 4: Vetorização e Indexação**
- [x] **Fase 5: Interface de Chat/CLI**
- [x] **Fase 6: Otimização de busca (Híbrida)**
- [x] **Fase 7: Guardrails e Filtros**
- [x] **Fase 8: Métricas e Avaliação (BERTScore, RAGAS)** ← **CONCLUÍDO**
- [x] **Fase 9: Pipeline RAG Completo** ← **CONCLUÍDO**
- [ ] **Fase 10: Experimentos e Dashboards**

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Este é um projeto acadêmico com foco em:

- Metodologia replicável
- Código bem documentado
- Boas práticas de engenharia

### Como Contribuir

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Ver [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

**Ronen Rodrigues Silva Filho**

- 📅 Ano: 2026

---

## 📚 Citação

Se você usar este projeto em sua pesquisa, por favor cite:

```bibtex
@misc{silva2026lion,
  title={LION: Legal Interpretation and Official Norms - Um Assistente Virtual RAG para IRPF},
  author={Silva Filho, Ronen Rodrigues},
  year={2026},
  publisher={GitHub},
  howpublished={\\url{https://github.com/ronenfilho/lion}}
}
```

---

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma [issue](https://github.com/ronenfilho/lion/issues)
- Consulte a [documentação](docs/)

---

**Última atualização:** 14 de fevereiro de 2026

**Status do Projeto:** 🟡 Em Desenvolvimento Ativo

---

<div align="center">

### ⭐ Se este projeto foi útil, considere dar uma estrela!

</div>
