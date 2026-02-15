"""
Testes Unitários - RAG Pipeline
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.pipeline.rag_pipeline import (
    RAGPipeline,
    QueryResult,
    IngestionResult,
    create_rag_pipeline
)


class TestRAGPipeline:
    """Testes para classe RAGPipeline"""
    
    @pytest.fixture
    def mock_config(self):
        """Configuração mockada para testes"""
        config = Mock()
        
        # Chunking
        config.chunking.strategy = "structural"
        config.chunking.max_chunk_size = 800
        config.chunking.overlap = 0
        
        # Embeddings
        config.embeddings.model = "test-model"
        config.embeddings.batch_size = 32
        
        # Vector Store
        config.vector_store.persist_directory = "./test_data"
        config.vector_store.collection_name = "test_collection"
        
        # Retrieval
        config.retrieval.strategy = "hybrid"
        config.retrieval.top_k = 5
        config.retrieval.hybrid_alpha = 0.7
        
        # Generation
        config.generation.model = "test-llm"
        config.generation.temperature = 0.2
        config.generation.max_tokens = 800
        
        # Guardrails
        config.guardrails.input_validation = True
        config.guardrails.output_validation = True
        
        # Cache
        config.cache.enabled = True
        config.cache.max_size = 100
        
        # Monitoring
        config.monitoring.enabled = False
        config.monitoring.log_level = "INFO"
        
        return config
    
    @pytest.fixture
    def pipeline(self, mock_config):
        """Pipeline mockado para testes"""
        with patch('src.pipeline.rag_pipeline.PDFExtractor'), \
             patch('src.pipeline.rag_pipeline.HTMLExtractor'), \
             patch('src.pipeline.rag_pipeline.TextCleaner'), \
             patch('src.pipeline.rag_pipeline.StructuralChunker'), \
             patch('src.pipeline.rag_pipeline.EmbeddingsPipeline'), \
             patch('src.pipeline.rag_pipeline.VectorStore'), \
             patch('src.pipeline.rag_pipeline.HybridRetriever'), \
             patch('src.pipeline.rag_pipeline.LLMClient'), \
             patch('src.pipeline.rag_pipeline.PromptManager'), \
             patch('src.pipeline.rag_pipeline.InputValidator'), \
             patch('src.pipeline.rag_pipeline.OutputValidator'):
            
            pipeline = RAGPipeline(config=mock_config, verbose=False)
            return pipeline
    
    def test_pipeline_initialization(self, pipeline):
        """Testa inicialização do pipeline"""
        assert pipeline is not None
        assert pipeline.config is not None
        assert pipeline.logger is not None
        assert pipeline.cache is not None
    
    def test_query_result_creation(self):
        """Testa criação de QueryResult"""
        result = QueryResult(
            query="Test query?",
            answer="Test answer",
            chunks=[{"content": "chunk1"}],
            metadata={"test": "metadata"}
        )
        
        assert result.query == "Test query?"
        assert result.answer == "Test answer"
        assert len(result.chunks) == 1
        assert result.timestamp is not None
        
        # Converter para dict
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['query'] == "Test query?"
    
    def test_ingestion_result_creation(self):
        """Testa criação de IngestionResult"""
        result = IngestionResult(
            success=True,
            documents_processed=5,
            chunks_created=100,
            chunks_indexed=100,
            errors=[],
            processing_time=10.5,
            metadata={"test": "data"}
        )
        
        assert result.success is True
        assert result.documents_processed == 5
        assert result.chunks_created == 100
        assert result.errors == []
    
    def test_extract_pdf_document(self, pipeline):
        """Testa extração de documento PDF"""
        # Mock do extractor
        pipeline.pdf_extractor.extract = Mock(return_value={
            'text': 'Test PDF content',
            'metadata': {'source': 'test.pdf'}
        })
        
        result = pipeline._extract_document('test.pdf')
        
        assert result is not None
        assert result['text'] == 'Test PDF content'
        assert 'metadata' in result
    
    def test_extract_html_document(self, pipeline):
        """Testa extração de documento HTML"""
        # Mock do extractor
        pipeline.html_extractor.extract = Mock(return_value={
            'text': 'Test HTML content',
            'metadata': {'source': 'test.html'}
        })
        
        result = pipeline._extract_document('test.html')
        
        assert result is not None
        assert result['text'] == 'Test HTML content'
    
    def test_extract_unsupported_format(self, pipeline):
        """Testa extração de formato não suportado"""
        result = pipeline._extract_document('test.docx')
        assert result is None
    
    def test_query_with_invalid_input(self, pipeline):
        """Testa query com input inválido"""
        # Mock validator retornando inválido
        pipeline.input_validator.validate = Mock(return_value=(False, "Query muito curta"))
        
        result = pipeline.query("test")
        
        assert "❌" in result.answer
        assert result.metadata['error'] == "Query muito curta"
        assert result.metadata['stage'] == 'input_validation'
    
    def test_query_with_no_chunks_found(self, pipeline):
        """Testa query quando nenhum chunk é encontrado"""
        # Mock validator válido
        pipeline.input_validator.validate = Mock(return_value=(True, ""))
        
        # Mock retriever sem resultados
        pipeline.retriever.retrieve = Mock(return_value=[])
        
        result = pipeline.query("Como declarar imposto de renda?")
        
        assert "Não encontrei informações" in result.answer
        assert len(result.chunks) == 0
        assert 'no_chunks_found' in result.metadata.get('error', '')
    
    def test_query_success(self, pipeline):
        """Testa query bem-sucedida"""
        # Mock validator válido
        pipeline.input_validator.validate = Mock(return_value=(True, ""))
        
        # Mock retriever com chunks
        mock_chunks = [
            {
                'content': 'Chunk 1 sobre IRPF',
                'metadata': {'source': 'doc1.pdf'},
                'score': 0.9
            },
            {
                'content': 'Chunk 2 sobre declaração',
                'metadata': {'source': 'doc2.pdf'},
                'score': 0.8
            }
        ]
        pipeline.retriever.retrieve = Mock(return_value=mock_chunks)
        
        # Mock prompt manager
        pipeline.prompt_manager.format_prompt = Mock(
            return_value=("System prompt", "User prompt")
        )
        
        # Mock LLM response
        pipeline.llm_client.generate = Mock(
            return_value="Resposta gerada pelo LLM"
        )
        
        # Mock output validator
        pipeline.output_validator.validate = Mock(
            return_value=(True, "Resposta gerada pelo LLM")
        )
        
        result = pipeline.query("Como declarar imposto de renda?")
        
        assert result.answer == "Resposta gerada pelo LLM"
        assert len(result.chunks) == 2
        assert result.metadata['num_chunks'] == 2
        assert 'retrieval_time' in result.metadata
        assert 'generation_time' in result.metadata
    
    def test_query_with_cache_hit(self, pipeline):
        """Testa query com cache hit"""
        # Adicionar ao cache
        cached_result = QueryResult(
            query="Test query?",
            answer="Cached answer",
            chunks=[],
            metadata={'cache_hit': True}
        )
        pipeline.cache["Test query?"] = cached_result
        
        # Mock validator
        pipeline.input_validator.validate = Mock(return_value=(True, ""))
        
        result = pipeline.query("Test query?")
        
        assert result.answer == "Cached answer"
        assert result.metadata.get('cache_hit') is True
    
    def test_cache_management(self, pipeline):
        """Testa gerenciamento de cache"""
        pipeline.config.cache.max_size = 2
        
        # Adicionar 3 queries (deve remover a primeira)
        for i in range(3):
            query = f"Query {i}"
            result = QueryResult(
                query=query,
                answer=f"Answer {i}",
                chunks=[],
                metadata={}
            )
            pipeline._add_to_cache(query, result)
        
        # Verificar que cache tem tamanho máximo
        assert len(pipeline.cache) == 2
        
        # Primeira query deve ter sido removida
        assert "Query 0" not in pipeline.cache
        assert "Query 1" in pipeline.cache
        assert "Query 2" in pipeline.cache
    
    def test_clear_cache(self, pipeline):
        """Testa limpeza de cache"""
        # Adicionar ao cache
        pipeline.cache["test"] = QueryResult(
            query="test",
            answer="answer",
            chunks=[],
            metadata={}
        )
        
        assert len(pipeline.cache) > 0
        
        pipeline.clear_cache()
        
        assert len(pipeline.cache) == 0
    
    def test_get_stats(self, pipeline):
        """Testa obtenção de estatísticas"""
        # Mock vector store stats
        pipeline.vector_store.get_stats = Mock(return_value={
            'num_chunks': 100,
            'collection': 'test_collection'
        })
        
        stats = pipeline.get_stats()
        
        assert 'vector_store' in stats
        assert 'cache_size' in stats
        assert 'config' in stats
        assert stats['config']['retrieval_strategy'] == 'hybrid'
    
    def test_batch_query(self, pipeline):
        """Testa processamento em lote"""
        # Mock validator
        pipeline.input_validator.validate = Mock(return_value=(True, ""))
        
        # Mock retriever
        pipeline.retriever.retrieve = Mock(return_value=[
            {'content': 'chunk', 'metadata': {}, 'score': 0.9}
        ])
        
        # Mock prompts e LLM
        pipeline.prompt_manager.format_prompt = Mock(
            return_value=("sys", "usr")
        )
        pipeline.llm_client.generate = Mock(return_value="Answer")
        pipeline.output_validator.validate = Mock(
            return_value=(True, "Answer")
        )
        
        questions = ["Q1?", "Q2?", "Q3?"]
        results = pipeline.batch_query(questions)
        
        assert len(results) == 3
        assert all(isinstance(r, QueryResult) for r in results)
    
    def test_ingest_documents_success(self, pipeline):
        """Testa ingestão bem-sucedida"""
        # Mock extractors
        pipeline.pdf_extractor.extract = Mock(return_value={
            'text': 'Test content',
            'metadata': {'source': 'test.pdf'}
        })
        
        # Mock cleaner
        pipeline.text_cleaner.clean = Mock(return_value='Cleaned content')
        
        # Mock chunker
        mock_chunks = [
            {'content': 'chunk1', 'metadata': {}},
            {'content': 'chunk2', 'metadata': {}}
        ]
        pipeline.chunker.chunk_document = Mock(return_value=mock_chunks)
        
        # Mock embeddings
        pipeline.embeddings_pipeline.generate_embeddings = Mock(
            return_value=mock_chunks
        )
        
        # Mock vector store
        pipeline.vector_store.add_chunks = Mock(return_value=2)
        
        result = pipeline.ingest_documents(['test.pdf'])
        
        assert result.success is True
        assert result.documents_processed == 1
        assert result.chunks_created == 2
        assert result.chunks_indexed == 2
        assert len(result.errors) == 0
    
    def test_ingest_documents_with_errors(self, pipeline):
        """Testa ingestão com erros"""
        # Mock extractor que falha
        pipeline.pdf_extractor.extract = Mock(side_effect=Exception("Extraction failed"))
        
        result = pipeline.ingest_documents(['test.pdf'])
        
        assert result.success is False
        assert result.documents_processed == 0
        assert len(result.errors) > 0


class TestFactoryFunction:
    """Testes para função factory"""
    
    @patch('src.pipeline.rag_pipeline.load_config')
    @patch('src.pipeline.rag_pipeline.RAGPipeline')
    def test_create_rag_pipeline(self, mock_rag_pipeline, mock_load_config):
        """Testa criação via factory function"""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        pipeline = create_rag_pipeline(verbose=True)
        
        mock_load_config.assert_called_once()
        mock_rag_pipeline.assert_called_once_with(
            config=mock_config,
            verbose=True
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
