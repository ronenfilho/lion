"""
Testes de Integração End-to-End - RAG Pipeline
Testa o fluxo completo do sistema RAG
"""

import pytest
import os
from pathlib import Path
import tempfile
import shutil

from src.pipeline.rag_pipeline import create_rag_pipeline, QueryResult


@pytest.fixture
def temp_dir():
    """Diretório temporário para testes"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def sample_pdf(temp_dir):
    """Cria PDF de exemplo para testes"""
    # Para teste real, seria necessário um PDF válido
    # Por enquanto, retorna path que será mockado
    pdf_path = Path(temp_dir) / "test_document.pdf"
    return str(pdf_path)


@pytest.fixture
def test_pipeline(temp_dir):
    """
    Pipeline configurado para testes de integração.
    Usa diretórios temporários.
    """
    # Configurar variáveis de ambiente para teste
    os.environ['CHROMA_PERSIST_DIR'] = str(Path(temp_dir) / "chroma_test")
    
    pipeline = create_rag_pipeline(verbose=True)
    
    yield pipeline
    
    # Cleanup
    if 'CHROMA_PERSIST_DIR' in os.environ:
        del os.environ['CHROMA_PERSIST_DIR']


class TestEndToEndIngestion:
    """Testes end-to-end do fluxo de ingestão"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('RUN_INTEGRATION_TESTS'),
        reason="Testes de integração desabilitados. Use RUN_INTEGRATION_TESTS=1"
    )
    def test_full_ingestion_pipeline(self, test_pipeline, sample_pdf):
        """
        Testa pipeline completo de ingestão:
        PDF → Extração → Limpeza → Chunking → Embeddings → Indexação
        """
        # Este teste requer um PDF real e API keys configuradas
        # Pular se arquivo não existir
        if not Path(sample_pdf).exists():
            pytest.skip("PDF de teste não disponível")
        
        result = test_pipeline.ingest_documents([sample_pdf])
        
        # Validações
        assert result.success is True
        assert result.documents_processed > 0
        assert result.chunks_created > 0
        assert result.chunks_indexed > 0
        assert len(result.errors) == 0
        assert result.processing_time > 0
        
        # Verificar que chunks foram indexados
        stats = test_pipeline.get_stats()
        assert stats['vector_store']['num_chunks'] > 0


class TestEndToEndQuery:
    """Testes end-to-end do fluxo de consulta"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('RUN_INTEGRATION_TESTS'),
        reason="Testes de integração desabilitados. Use RUN_INTEGRATION_TESTS=1"
    )
    def test_full_query_pipeline(self, test_pipeline):
        """
        Testa pipeline completo de query:
        Query → Validação → Retrieval → Generation → Validação → Response
        
        NOTA: Requer vector store populado e API keys de LLM
        """
        # Verificar se tem chunks no vector store
        stats = test_pipeline.get_stats()
        if stats['vector_store']['num_chunks'] == 0:
            pytest.skip("Vector store vazio - execute ingestão primeiro")
        
        # Query de teste
        question = "Como declarar rendimentos de aposentadoria?"
        
        result = test_pipeline.query(question)
        
        # Validações básicas
        assert isinstance(result, QueryResult)
        assert result.query == question
        assert result.answer is not None
        assert len(result.answer) > 0
        assert result.timestamp is not None
        
        # Validar metadata
        assert 'retrieval_time' in result.metadata
        assert 'generation_time' in result.metadata
        assert 'total_time' in result.metadata
        assert result.metadata['total_time'] > 0
        
        # Validar chunks
        if len(result.chunks) > 0:
            chunk = result.chunks[0]
            assert 'content' in chunk
            assert 'metadata' in chunk
            assert 'score' in chunk
    
    @pytest.mark.integration
    def test_query_with_evaluation(self, test_pipeline):
        """
        Testa query com avaliação de métricas.
        Requer RAGAS_API_KEY ou GOOGLE_API_KEY configurado.
        """
        if not os.getenv('GOOGLE_API_KEY') and not os.getenv('RAGAS_API_KEY'):
            pytest.skip("API key não configurada para avaliação")
        
        stats = test_pipeline.get_stats()
        if stats['vector_store']['num_chunks'] == 0:
            pytest.skip("Vector store vazio")
        
        question = "Quais são os limites de dedução para despesas médicas?"
        ground_truth = "Não há limite para dedução de despesas médicas no IRPF."
        
        result = test_pipeline.query(
            question=question,
            evaluate=True,
            ground_truth=ground_truth
        )
        
        # Validar que métricas foram calculadas
        assert result.metrics is not None
        assert len(result.metrics) > 0
        
        # Verificar métricas específicas
        if 'faithfulness' in result.metrics:
            assert 0.0 <= result.metrics['faithfulness'] <= 1.0
        
        if 'answer_relevancy' in result.metrics:
            assert 0.0 <= result.metrics['answer_relevancy'] <= 1.0
        
        if 'bertscore_f1' in result.metrics:
            assert 0.0 <= result.metrics['bertscore_f1'] <= 1.0


class TestEndToEndCache:
    """Testes end-to-end do sistema de cache"""
    
    @pytest.mark.integration
    def test_cache_behavior(self, test_pipeline):
        """Testa que cache acelera queries repetidas"""
        stats = test_pipeline.get_stats()
        if stats['vector_store']['num_chunks'] == 0:
            pytest.skip("Vector store vazio")
        
        question = "Teste de cache"
        
        # Primeira query (sem cache)
        result1 = test_pipeline.query(question)
        time1 = result1.metadata['total_time']
        cache_hit1 = result1.metadata.get('cache_hit', False)
        
        # Segunda query (com cache)
        result2 = test_pipeline.query(question)
        time2 = result2.metadata['total_time']
        cache_hit2 = result2.metadata.get('cache_hit', False)
        
        # Validações
        assert cache_hit1 is False  # Primeira não estava no cache
        assert cache_hit2 is True   # Segunda veio do cache
        assert time2 < time1 * 0.5  # Cache deve ser muito mais rápido
        assert result1.answer == result2.answer  # Mesma resposta


class TestEndToEndBatch:
    """Testes end-to-end do processamento em lote"""
    
    @pytest.mark.integration
    def test_batch_processing(self, test_pipeline):
        """Testa processamento de múltiplas queries"""
        stats = test_pipeline.get_stats()
        if stats['vector_store']['num_chunks'] == 0:
            pytest.skip("Vector store vazio")
        
        questions = [
            "Como declarar dependentes?",
            "Quais despesas são dedutíveis?",
            "Qual o prazo para declaração?"
        ]
        
        results = test_pipeline.batch_query(questions)
        
        # Validações
        assert len(results) == len(questions)
        assert all(isinstance(r, QueryResult) for r in results)
        assert all(r.answer is not None for r in results)
        assert all(len(r.answer) > 0 for r in results)
        
        # Verificar que queries diferentes têm respostas diferentes
        answers = [r.answer for r in results]
        assert len(set(answers)) > 1  # Pelo menos 2 respostas únicas


class TestEndToEndErrorHandling:
    """Testes end-to-end de tratamento de erros"""
    
    def test_query_too_short(self, test_pipeline):
        """Testa query muito curta"""
        result = test_pipeline.query("oi")
        
        # Deve retornar erro de validação
        assert "❌" in result.answer
        assert 'error' in result.metadata
    
    def test_query_with_empty_vector_store(self):
        """Testa query com vector store vazio"""
        # Criar pipeline com vector store vazio
        pipeline = create_rag_pipeline(verbose=False)
        
        result = pipeline.query("Como declarar imposto?")
        
        # Deve retornar erro de chunks não encontrados
        assert "Não encontrei" in result.answer or len(result.chunks) == 0
    
    def test_ingestion_nonexistent_file(self, test_pipeline):
        """Testa ingestão de arquivo inexistente"""
        result = test_pipeline.ingest_documents(["arquivo_que_nao_existe.pdf"])
        
        # Deve ter erros
        assert result.success is False
        assert len(result.errors) > 0
        assert result.documents_processed == 0


class TestEndToEndStatistics:
    """Testes end-to-end das estatísticas do pipeline"""
    
    def test_get_comprehensive_stats(self, test_pipeline):
        """Testa obtenção de estatísticas completas"""
        stats = test_pipeline.get_stats()
        
        # Validar estrutura
        assert 'vector_store' in stats
        assert 'cache_size' in stats
        assert 'config' in stats
        
        # Validar config
        config = stats['config']
        assert 'retrieval_strategy' in config
        assert 'top_k' in config
        assert 'llm_model' in config
        assert 'embedding_model' in config
        assert 'chunking_strategy' in config
    
    def test_cache_statistics(self, test_pipeline):
        """Testa estatísticas de cache"""
        initial_stats = test_pipeline.get_stats()
        initial_cache_size = initial_stats['cache_size']
        
        # Fazer algumas queries
        if initial_stats['vector_store']['num_chunks'] > 0:
            test_pipeline.query("Teste 1")
            test_pipeline.query("Teste 2")
            
            updated_stats = test_pipeline.get_stats()
            updated_cache_size = updated_stats['cache_size']
            
            # Cache deve ter crescido
            assert updated_cache_size > initial_cache_size


class TestEndToEndLogging:
    """Testes end-to-end do sistema de logging"""
    
    @pytest.mark.integration
    def test_save_query_log(self, test_pipeline, temp_dir):
        """Testa salvamento de logs de queries"""
        stats = test_pipeline.get_stats()
        if stats['vector_store']['num_chunks'] == 0:
            pytest.skip("Vector store vazio")
        
        log_file = Path(temp_dir) / "query_logs.jsonl"
        
        # Fazer query
        result = test_pipeline.query("Teste de logging")
        
        # Salvar log
        test_pipeline.save_query_log(result, str(log_file))
        
        # Validar que arquivo foi criado
        assert log_file.exists()
        
        # Ler e validar conteúdo
        with open(log_file, 'r', encoding='utf-8') as f:
            import json
            log_entry = json.loads(f.readline())
        
        assert 'query' in log_entry
        assert 'answer' in log_entry
        assert 'timestamp' in log_entry
        assert log_entry['query'] == "Teste de logging"


# Fixtures para configuração de testes
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuração global dos testes de integração"""
    # Configurar ambiente de teste
    os.environ['ENVIRONMENT'] = 'test'
    
    yield
    
    # Cleanup
    if 'ENVIRONMENT' in os.environ:
        del os.environ['ENVIRONMENT']


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "-m", "integration",
        "--tb=short"
    ])
