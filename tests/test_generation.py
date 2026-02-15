"""
Teste do Sistema de Geração - LION
Validação end-to-end: Retrieval + Generation
"""

import os
import sys
from pathlib import Path
from time import time
from typing import List

# Adicionar src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from ingestion.vector_store import VectorStore
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.dense_retriever import DenseRetriever
from retrieval.bm25_retriever import BM25Retriever
from generation.llm_client import LLMClient, create_llm_client
from generation.prompts import PromptManager, create_prompt_manager
from generation.output_parser import OutputParser, create_output_parser


def test_rag_pipeline():
    """
    Testa pipeline RAG completo:
    Query → Retrieval → Context Building → Generation → Parsing
    """
    print("🧪 TESTE DO SISTEMA DE GERAÇÃO (RAG)")
    print("=" * 60)
    
    # Carregar componentes
    print("\n📦 Carregando componentes...")
    
    # Vector store
    vector_store = VectorStore(persist_directory="data/vectorstore")
    print(f"   ✓ Vector store: {vector_store.count()} documentos")
    
    # Retrievers
    dense = DenseRetriever(vector_store)
    bm25 = BM25Retriever.from_vector_store(vector_store)
    hybrid = HybridRetriever(dense, bm25, alpha=0.7)
    print(f"   ✓ Retrievers: Dense + BM25 + Hybrid")
    
    # LLM Client
    llm = create_llm_client()
    print(f"   ✓ LLM Client: {llm.model_name}")
    
    # Prompt Manager
    prompt_mgr = create_prompt_manager()
    print(f"   ✓ Prompt Manager: {len(prompt_mgr.templates)} templates")
    
    # Output Parser
    parser = create_output_parser()
    print(f"   ✓ Output Parser")
    
    # Queries de teste
    test_queries = [
        {
            'query': 'Quais são as deduções permitidas no IRPF?',
            'expected_template': 'deductions',
            'description': 'Query sobre deduções'
        },
        {
            'query': 'Como calcular o imposto de renda devido?',
            'expected_template': 'calculation',
            'description': 'Query sobre cálculo'
        },
        {
            'query': 'Qual o prazo para entregar a declaração do IRPF 2024?',
            'expected_template': 'deadlines',
            'description': 'Query sobre prazos'
        }
    ]
    
    # Executar testes
    print("\n\n🔍 EXECUTANDO QUERIES DE TESTE")
    print("=" * 60)
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        query = test['query']
        expected_template = test['expected_template']
        description = test['description']
        
        print(f"\n\n📝 Teste {i}/3: {description}")
        print(f"Query: {query}")
        print("-" * 60)
        
        try:
            start_time = time()
            
            # 1. Detecção de template
            detected_template = prompt_mgr.detect_query_type(query)
            print(f"\n1️⃣ Template detectado: {detected_template}")
            if detected_template != expected_template:
                print(f"   ⚠️ Esperado: {expected_template}")
            
            # 2. Retrieval
            print(f"\n2️⃣ Executando retrieval (hybrid)...")
            retrieved = hybrid.retrieve(query, top_k=5)
            print(f"   ✓ Recuperados: {len(retrieved)} chunks")
            for j, res in enumerate(retrieved[:3], 1):
                print(f"      [{j}] Score: {res.score:.3f} | {res.content[:80]}...")
            
            # 3. Construir contexto
            context_chunks = [res.content for res in retrieved]
            
            # 4. Gerar resposta
            print(f"\n3️⃣ Gerando resposta com LLM...")
            generation_result = llm.generate_with_context(
                query=query,
                context_chunks=context_chunks,
                max_context_length=4000
            )
            
            print(f"   ✓ Gerado: {generation_result.tokens_used} tokens em {generation_result.generation_time:.2f}s")
            
            # 5. Parse da resposta
            print(f"\n4️⃣ Parseando resposta...")
            parsed = parser.parse(generation_result.text, context_chunks)
            
            print(f"   ✓ Confiança: {parsed.confidence:.2f}")
            print(f"   ✓ Tem resposta: {parsed.has_answer}")
            print(f"   ✓ Citações: {len(parsed.citations)}")
            print(f"   ✓ Valores extraídos: {len(parsed.extracted_data.monetary_values)}")
            
            if parsed.warnings:
                print(f"   ⚠️ Warnings:")
                for warning in parsed.warnings:
                    print(f"      - {warning}")
            
            # 6. Exibir resposta
            print(f"\n💬 RESPOSTA FINAL:")
            print("-" * 60)
            print(parsed.clean_text)
            
            if parsed.citations:
                print(f"\n📚 Referências:")
                for citation in parsed.citations:
                    ref = citation.article
                    if citation.paragraph:
                        ref += f", {citation.paragraph}"
                    print(f"   • {ref}")
            
            # Métricas
            elapsed_time = time() - start_time
            
            result = {
                'query': query,
                'template': detected_template,
                'retrieved_count': len(retrieved),
                'has_answer': parsed.has_answer,
                'confidence': parsed.confidence,
                'citations_count': len(parsed.citations),
                'time': elapsed_time,
                'warnings': parsed.warnings
            }
            results.append(result)
            
            print(f"\n⏱️ Tempo total: {elapsed_time:.2f}s")
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            
            results.append({
                'query': query,
                'error': str(e),
                'time': time() - start_time
            })
    
    # Sumário
    print("\n\n" + "=" * 60)
    print("📊 SUMÁRIO DOS TESTES")
    print("=" * 60)
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"\n✅ Sucessos: {len(successful)}/{len(results)}")
    print(f"❌ Falhas: {len(failed)}/{len(results)}")
    
    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        total_citations = sum(r['citations_count'] for r in successful)
        
        print(f"\n📈 Métricas médias:")
        print(f"   • Tempo: {avg_time:.2f}s")
        print(f"   • Confiança: {avg_confidence:.2f}")
        print(f"   • Citações totais: {total_citations}")
        print(f"   • Respostas definitivas: {sum(1 for r in successful if r['has_answer'])}/{len(successful)}")
    
    # Listar warnings
    all_warnings = [w for r in successful for w in r.get('warnings', [])]
    if all_warnings:
        print(f"\n⚠️ Warnings encontrados:")
        unique_warnings = set(all_warnings)
        for warning in unique_warnings:
            count = all_warnings.count(warning)
            print(f"   • {warning} ({count}x)")
    
    print("\n\n✅ Teste concluído!")
    
    return results


def test_generation_only():
    """
    Testa apenas a geração, sem retrieval.
    """
    print("\n\n" + "=" * 60)
    print("🧪 TESTE DE GERAÇÃO (SEM RAG)")
    print("=" * 60)
    
    llm = create_llm_client()
    parser = create_output_parser()
    
    query = "O que é o IRPF?"
    
    print(f"\nQuery: {query}")
    print("-" * 60)
    
    try:
        # Gerar sem contexto
        result = llm.generate(query)
        
        print(f"\n💬 Resposta:")
        print(result.text)
        
        # Parse
        parsed = parser.parse(result.text)
        print(f"\n📊 Confiança: {parsed.confidence:.2f}")
        print(f"Tem resposta: {parsed.has_answer}")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")


if __name__ == "__main__":
    # Verificar .env
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY não configurada no .env")
        print("Configure antes de executar o teste.")
        sys.exit(1)
    
    # Executar testes
    try:
        test_rag_pipeline()
        test_generation_only()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
