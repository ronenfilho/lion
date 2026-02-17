# 🛠️ LION - Guia Prático de Implementação

## 📋 Roadmap de Implementação Detalhado

### 📊 Progresso Geral: 94% Completo (33/35 tarefas)

```markdown
## ✅ Fase 1: Setup Inicial (100% - 6/6)
- [x] Estrutura de diretórios criada (30+ pastas)
- [x] requirements.txt criado (40+ dependências)
- [x] .env.example configurado
- [x] .gitignore criado
- [x] Git inicializado
- [x] Arquitetura e documentação completa (8 docs, ~3800 linhas)
📝 Commit: 9d6f6c6 - "docs: expandir arquitetura e criar estrutura inicial"

## ✅ Fase 2: Configuração do Sistema (100% - 6/6)
- [x] Sistema de configuração YAML implementado
- [x] Validação Pydantic (config.py com 8 classes)
- [x] config/default.yaml (configuração base)
- [x] config/development.yaml (ambiente dev)
- [x] config/production.yaml (ambiente prod)
- [x] Modelos trocados para Google (Gemini 2.0 Flash + text-embedding-004)
📝 Commit: ede83f1 - "feat: implementar sistema de configuração e estrutura base"

## ✅ Fase 3: Ambiente Python (100% - 2/2)
- [x] Ambiente virtual criado (venv)
- [x] Dependências instaladas compatíveis com Python 3.12
- [x] Integração .env → YAML implementada (prioridade: .env > {env}.yaml > default.yaml)
- [x] Sistema de configuração testado e validado ✓
📝 Commit: ede83f1 - "feat: implementar sistema de configuração e estrutura base"

## ✅ Fase 4: Ingestão de Dados (100% - 10/10)
- [x] src/ingestion/extractors/pdf_extractor.py (PyMuPDF + detecção estrutural)
- [x] src/ingestion/extractors/html_extractor.py (BeautifulSoup4 + encoding automático, tables + line breaks)
- [x] src/ingestion/extractors/text_cleaner.py (normalização + limpeza legal)
- [x] src/ingestion/chunking/structural_chunker.py (unified chunker com chunk_markdown() + chunk_pdf())
- [x] src/ingestion/embeddings_pipeline.py (gemini-embedding-001, 3072d)
- [x] src/ingestion/vector_store.py (ChromaDB com persistência, busca e filtros)
- [x] scripts/2_ingest_processed_documents.py (pipeline completo: load → chunk → embed → store)
- [x] scripts/2.1_show_chunk_stats.py + 2.2_show_chunks.py (visualização de chunks)
- [x] scripts/1_create_test_dataset.py (extração Q&A do Manual RFB)
- [x] experiments/datasets/manual_rfb_test.json (30 pares pergunta-resposta estruturados)
📝 Commit: 7da3c3e - "feat: implementa módulo de ingestão com extractors e chunkers"
📝 Commit: aac8d85 - "feat: adiciona embeddings pipeline com Google Gemini"
📝 Commit: 55abc1b - "feat: adiciona vector store com ChromaDB"
📝 Commit: a1e1023 - "feat(ingestion): unifica chunkers e implementa pipeline completo de ingestão"
✅ **Pipeline Testado**: 36 chunks criados de L15270_processed.md, embeddings 3072d, ChromaDB persistente

## ✅ Fase 5: Sistema de Retrieval (60% - 3/5)
- [x] src/retrieval/dense_retriever.py (busca vetorial com ChromaDB)
- [x] src/retrieval/bm25_retriever.py (busca por termos com tokenização legal)
- [x] src/retrieval/hybrid_retriever.py (RRF + weighted fusion, 70% dense / 30% BM25)
- [ ] src/retrieval/reranker.py (cross-encoder para reordenar resultados)
- [ ] Testar e comparar performance dos retrievers
📝 Commit: db17679 - "feat: implementa sistema de retrieval (dense, BM25, hybrid)"

## ✅ Fase 6: Geração de Respostas (100% - 3/3)
- [x] src/generation/llm_client.py (Google Gemini) - Commit: 549cabf
- [x] src/generation/prompts.py (templates especializados) - Commit: 549cabf
- [x] src/generation/output_parser.py (estruturação) - Commit: 549cabf

## ✅ Fase 7: Guardrails (100% - 3/3)
- [x] src/guardrails/pii_detector.py (regex patterns) - Commit: d199133
- [x] src/guardrails/input_validator.py (PII, prompt injection) - Commit: d199133
- [x] src/guardrails/output_validator.py (citações, relevância) - Commit: d199133

## ✅ Fase 8: Avaliação (100% - 5/5)
- [x] src/evaluation/metrics/rag_metrics.py (precision, recall, MRR, faithfulness, hallucination) - Commit: 01c505c
- [x] src/evaluation/metrics/comparative_metrics.py (ComparativeEvaluator, A/B testing) - Commit: 01c505c
- [x] src/evaluation/experiments/runner.py (automated experiment execution) - Commit: 01c505c
- [x] src/evaluation/metrics/bertscore.py (similaridade semântica BERT-based, bert-base-multilingual-cased)
- [x] src/evaluation/metrics/ragas_metrics.py (7 métricas RAG, integração Gemini 2.5 Flash, validado com score 1.000)
- [x] tests/evaluation/test_bertscore.py (4/4 testes passando)
- [x] Configuração .env para RAGAS (RAGAS_LLM_PROVIDER=gemini, embeddings configurados)
📝 Fase completa em: 15/02/2026

## ✅ Fase 9: Pipeline RAG Completo (100% - 3/3)
- [x] src/pipeline/rag_pipeline.py (integração completa - ingestion → retrieval → generation → evaluation)
- [x] tests/unit/test_rag_pipeline.py (18 testes unitários cobrindo todos os métodos)
- [x] tests/integration/test_rag_pipeline_integration.py (testes end-to-end do pipeline completo)
📝 Fase completa em: 15/02/2026

## 🔄 Fase 10: Experimentos (30% - 2/5)
- [x] **Etapa 10.1**: Criar dataset de teste ✅ (manual_rfb_test.json com 30 Q&A)
- [x] **Etapa 10.2**: Ingerir documentos processados ✅ (L15270_processed.md → 36 chunks no ChromaDB)
- [x] **Etapa 10.3**: Executar experimentos comparativos (4 experimentos: dense vs BM25 vs hybrid)
- [x] **Etapa 10.4**: Analisar resultados e calcular métricas (RAGAS, BERTScore)
- [x] **Etapa 10.5**: Gerar relatórios e visualizações
```

---

## 🎯 EXECUÇÃO

**Objetivo:** Executar experimentos comparativos para validar as hipóteses da pesquisa e medir o impacto de diferentes configurações do RAG.

#### **Tarefa Imediata: Implementar e Executar Experimentos**

**Experimentos Planejados:**

1. **Experimento 1: RAG vs Sem RAG**
   - **Config A**: Gemini sem RAG (baseline)
   - **Config B**: Gemini 2.5 Flash + RAG (dense retrieval)
   - **Objetivo**: Medir ganho de acurácia e redução de alucinações
   - **Métricas**: Faithfulness, Answer Relevancy, BERTScore F1

2. **Experimento 2: LLM Grande vs Pequeno+RAG**
   - **Config A**: Gemini 2.0 Flash (maior contexto, sem RAG)
   - **Config B**: Gemini 2.5 Flash + RAG
   - **Objetivo**: Validar se arquitetura RAG supera tamanho do modelo
   - **Métricas**: Fidelidade normativa, Custo-benefício (tokens)

3. **Experimento 3: Estratégias de Retrieval**
   - **Config A**: Dense retrieval (embeddings apenas)
   - **Config B**: BM25 retrieval (termos apenas)
   - **Config C**: Hybrid retrieval (70% dense + 30% BM25)
   - **Objetivo**: Melhor estratégia de busca para termos normativos
   - **Métricas**: Context Precision, Context Recall, MRR

4. **Experimento 4: Número de Chunks Retrieved**
   - **Config A**: k=3 chunks
   - **Config B**: k=5 chunks
   - **Config C**: k=10 chunks
   - **Objetivo**: Balancear contexto vs ruído
   - **Métricas**: Answer Relevancy, Context Utilization, Latência

**Pipeline de Execução:**

```bash
# 1. Criar script de experimentos
scripts/3_run_experiments.py

# 2. Executar cada configuração
python scripts/3_run_experiments.py --experiment rag_vs_no_rag --max-questions 1
python scripts/3_run_experiments.py --experiment llm_size --max-questions 3
python scripts/3_run_experiments.py --experiment retrieval_strategy --max-questions 1
python scripts/3_run_experiments.py --experiment chunk_count --max-questions 29

# 3. Analisar resultados
python scripts/3.1_analyze_results.py

# 4. Gerar relatórios
python scripts/3.2_generate_report.py
```

---
```json
{
  "dataset_name": "lei_15270_qa_test",
  "version": "1.0",
  "created_at": "2026-02-15",
  "total_questions": 30,
  "questions": [
    {
      "id": "q001",
      "question": "Quem é obrigado a declarar o Imposto de Renda?",
      "ground_truth": "É obrigado a apresentar a Declaração de Ajuste Anual quem recebeu...",
      "category": "obrigatoriedade",
      "difficulty": "facil",
      "source": "Lei 15.270/2025, Art. 3º",
      "metadata": {
        "article": "3",
        "section": "obrigatoriedade"
      }
    }
  ]
}
```

**Data:** 16/02/2026  
**Versão:** 1.4  
**Última Atualização:** Experimentos 1-4 completos (Fase Experimental 99% concluída)  
**Status:** LocalLLMClient implementado, Experimento 4 executado, aguardando GPU para validação final  