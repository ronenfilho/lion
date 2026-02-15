"""
RAG Pipeline - LION
Pipeline completo integrando todos os componentes do sistema RAG
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging
import json

# Configuração
from src.utils.config import Config, load_config

# Ingestão
from src.ingestion.extractors.pdf_extractor import PDFExtractor
from src.ingestion.extractors.html_extractor import HTMLExtractor
from src.ingestion.extractors.text_cleaner import TextCleaner
from src.ingestion.chunking.structural_chunker import StructuralChunker
from src.ingestion.embeddings_pipeline import EmbeddingsPipeline
from src.ingestion.vector_store import VectorStore

# Retrieval
from src.retrieval.hybrid_retriever import HybridRetriever

# Generation
from src.generation.llm_client import LLMClient
from src.generation.prompts import PromptManager

# Guardrails
from src.guardrails.input_validator import InputValidator
from src.guardrails.output_validator import OutputValidator

# Evaluation
from src.evaluation.metrics.rag_metrics import RAGEvaluator
from src.evaluation.metrics.bertscore import BERTScoreEvaluator
from src.evaluation.metrics.ragas_metrics import RAGASEvaluator


@dataclass
class QueryResult:
    """Resultado de uma consulta ao sistema RAG"""
    query: str
    answer: str
    chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    metrics: Optional[Dict[str, float]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return asdict(self)


@dataclass
class IngestionResult:
    """Resultado da ingestão de documentos"""
    success: bool
    documents_processed: int
    chunks_created: int
    chunks_indexed: int
    errors: List[str]
    processing_time: float
    metadata: Dict[str, Any]


class RAGPipeline:
    """
    Pipeline RAG completo integrando todos os componentes.
    
    Fluxo de Ingestão:
    1. Extração (PDF/HTML) → 2. Limpeza → 3. Chunking → 4. Embeddings → 5. Indexação
    
    Fluxo de Query:
    1. Validação Input → 2. Retrieval → 3. Geração → 4. Validação Output → 5. Avaliação
    """
    
    def __init__(self, config: Optional[Config] = None, verbose: bool = False):
        """
        Inicializa pipeline RAG.
        
        Args:
            config: Configuração do sistema (usa padrão se None)
            verbose: Se True, imprime logs detalhados
        """
        self.config = config or load_config()
        self.verbose = verbose
        
        # Configurar logging
        self._setup_logging()
        
        # Inicializar componentes
        self.logger.info("Inicializando componentes do pipeline RAG...")
        
        # Ingestão
        self.pdf_extractor = PDFExtractor()
        self.html_extractor = HTMLExtractor()
        self.text_cleaner = TextCleaner()
        self.chunker = StructuralChunker(
            max_chunk_size=self.config.chunking.max_chunk_size,
            overlap=self.config.chunking.overlap
        )
        self.embeddings_pipeline = EmbeddingsPipeline(
            model_name=self.config.embeddings.model,
            batch_size=self.config.embeddings.batch_size
        )
        self.vector_store = VectorStore(
            persist_directory=self.config.vector_store.persist_directory,
            collection_name=self.config.vector_store.collection_name
        )
        
        # Retrieval
        from src.retrieval.dense_retriever import DenseRetriever
        dense_retriever = DenseRetriever(
            vector_store=self.vector_store,
            embeddings_pipeline=self.embeddings_pipeline,
            top_k=self.config.retrieval.top_k
        )
        
        self.retriever = HybridRetriever(
            dense_retriever=dense_retriever,
            alpha=self.config.retrieval.hybrid_alpha,
            top_k=self.config.retrieval.top_k
        )
        
        # Generation
        self.llm_client = LLMClient(
            model_name=self.config.generation.model,
            config=self.config.generation
        )
        self.prompt_manager = PromptManager()
        
        # Guardrails
        if self.config.guardrails.input_validation:
            self.input_validator = InputValidator()
        else:
            self.input_validator = None
        
        if self.config.guardrails.output_validation:
            self.output_validator = OutputValidator()
        else:
            self.output_validator = None
        
        # Evaluation (opcional)
        self.rag_evaluator = None
        self.bert_evaluator = None
        self.ragas_evaluator = None
        
        # Cache semântico (se habilitado)
        self.cache = {} if self.config.cache.enabled else None
        
        self.logger.info("✅ Pipeline RAG inicializado com sucesso")
    
    def _setup_logging(self):
        """Configura sistema de logging"""
        self.logger = logging.getLogger("RAGPipeline")
        self.logger.setLevel(
            getattr(logging, self.config.monitoring.log_level.upper())
        )
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def ingest_documents(
        self,
        file_paths: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionResult:
        """
        Pipeline completo de ingestão de documentos.
        
        Args:
            file_paths: Lista de caminhos para arquivos (PDF/HTML)
            metadata: Metadados adicionais para os documentos
            
        Returns:
            IngestionResult com estatísticas do processo
        """
        start_time = time.time()
        errors = []
        all_chunks = []
        docs_processed = 0
        
        self.logger.info(f"Iniciando ingestão de {len(file_paths)} documentos...")
        
        for file_path in file_paths:
            try:
                # 1. Extração
                self.logger.info(f"Extraindo: {file_path}")
                doc_data = self._extract_document(file_path)
                
                if not doc_data:
                    errors.append(f"Falha ao extrair: {file_path}")
                    continue
                
                # 2. Limpeza
                self.logger.info("Limpando texto extraído...")
                cleaned_text = self.text_cleaner.clean(doc_data['text'])
                doc_data['text'] = cleaned_text
                
                # 3. Chunking
                self.logger.info("Segmentando documento...")
                chunks = self.chunker.chunk_document(
                    text=doc_data['text'],
                    metadata={**doc_data.get('metadata', {}), **(metadata or {})}
                )
                
                all_chunks.extend(chunks)
                docs_processed += 1
                
                self.logger.info(f"✅ {len(chunks)} chunks criados de {file_path}")
                
            except Exception as e:
                error_msg = f"Erro ao processar {file_path}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        # 4. Embeddings
        chunks_indexed = 0
        if all_chunks:
            try:
                self.logger.info(f"Gerando embeddings para {len(all_chunks)} chunks...")
                chunks_with_embeddings = self.embeddings_pipeline.generate_embeddings(
                    all_chunks
                )
                
                # 5. Indexação
                self.logger.info("Indexando chunks no vector store...")
                chunks_indexed = self.vector_store.add_chunks(chunks_with_embeddings)
                
                self.logger.info(f"✅ {chunks_indexed} chunks indexados com sucesso")
                
            except Exception as e:
                error_msg = f"Erro na indexação: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        processing_time = time.time() - start_time
        
        result = IngestionResult(
            success=len(errors) == 0,
            documents_processed=docs_processed,
            chunks_created=len(all_chunks),
            chunks_indexed=chunks_indexed,
            errors=errors,
            processing_time=processing_time,
            metadata={
                'config': {
                    'chunking_strategy': self.config.chunking.strategy,
                    'max_chunk_size': self.config.chunking.max_chunk_size,
                    'embedding_model': self.config.embeddings.model
                }
            }
        )
        
        self.logger.info(
            f"Ingestão concluída: {docs_processed} docs, "
            f"{chunks_indexed} chunks em {processing_time:.2f}s"
        )
        
        return result
    
    def _extract_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extrai documento baseado na extensão.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dicionário com texto e metadados ou None se falhar
        """
        path = Path(file_path)
        
        if not path.exists():
            self.logger.error(f"Arquivo não encontrado: {file_path}")
            return None
        
        ext = path.suffix.lower()
        
        try:
            if ext == '.pdf':
                return self.pdf_extractor.extract(str(path))
            elif ext in ['.html', '.htm']:
                return self.html_extractor.extract(str(path))
            else:
                self.logger.warning(f"Extensão não suportada: {ext}")
                return None
        except Exception as e:
            self.logger.error(f"Erro na extração de {file_path}: {e}")
            return None
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        evaluate: bool = False,
        ground_truth: Optional[str] = None
    ) -> QueryResult:
        """
        Processa consulta completa ao sistema RAG.
        
        Args:
            question: Pergunta do usuário
            top_k: Número de chunks a recuperar (usa config se None)
            filters: Filtros de metadados para retrieval
            evaluate: Se True, calcula métricas de avaliação
            ground_truth: Resposta esperada (para avaliação)
            
        Returns:
            QueryResult com resposta e metadados
        """
        start_time = time.time()
        top_k = top_k or self.config.retrieval.top_k
        
        self.logger.info(f"Processando query: {question[:50]}...")
        
        # 1. Validação de entrada
        if self.input_validator:
            is_valid, error_msg = self.input_validator.validate(question)
            if not is_valid:
                self.logger.warning(f"Query inválida: {error_msg}")
                return QueryResult(
                    query=question,
                    answer=f"❌ {error_msg}",
                    chunks=[],
                    metadata={'error': error_msg, 'stage': 'input_validation'}
                )
        
        # 2. Verificar cache
        if self.cache is not None:
            cached_result = self._check_cache(question)
            if cached_result:
                self.logger.info("✅ Resposta encontrada no cache")
                cached_result.metadata['cache_hit'] = True
                return cached_result
        
        # 3. Retrieval
        self.logger.info("Recuperando contexto relevante...")
        retrieval_start = time.time()
        
        chunks = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filters=filters
        )
        
        retrieval_time = time.time() - retrieval_start
        self.logger.info(f"✅ {len(chunks)} chunks recuperados em {retrieval_time:.2f}s")
        
        if not chunks:
            self.logger.warning("Nenhum chunk relevante encontrado")
            return QueryResult(
                query=question,
                answer="❌ Não encontrei informações relevantes para responder sua pergunta.",
                chunks=[],
                metadata={'error': 'no_chunks_found', 'retrieval_time': retrieval_time}
            )
        
        # 4. Geração
        self.logger.info("Gerando resposta...")
        generation_start = time.time()
        
        # Montar prompt
        context_text = "\n\n---\n\n".join([
            f"[Fonte: {c.get('metadata', {}).get('source', 'Desconhecida')}]\n{c.get('content', c.get('text', ''))}"
            for c in chunks
        ])
        
        system_prompt, user_prompt = self.prompt_manager.format_prompt(
            template_name='rag_default',
            query=question,
            context=context_text
        )
        
        # Gerar resposta
        response = self.llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        generation_time = time.time() - generation_start
        self.logger.info(f"✅ Resposta gerada em {generation_time:.2f}s")
        
        # 5. Validação de saída
        if self.output_validator:
            is_valid, validated_response = self.output_validator.validate(
                response=response,
                retrieved_chunks=chunks
            )
            
            if not is_valid:
                self.logger.warning("Resposta não passou na validação de saída")
            else:
                response = validated_response
        
        # 6. Métricas (opcional)
        metrics = None
        if evaluate:
            metrics = self._evaluate_response(
                question=question,
                answer=response,
                chunks=chunks,
                ground_truth=ground_truth
            )
        
        # Criar resultado
        total_time = time.time() - start_time
        
        result = QueryResult(
            query=question,
            answer=response,
            chunks=[
                {
                    'content': c.get('content', c.get('text', '')),
                    'metadata': c.get('metadata', {}),
                    'score': c.get('score', 0.0)
                }
                for c in chunks
            ],
            metadata={
                'retrieval_time': retrieval_time,
                'generation_time': generation_time,
                'total_time': total_time,
                'num_chunks': len(chunks),
                'cache_hit': False,
                'config': {
                    'top_k': top_k,
                    'temperature': self.config.generation.temperature,
                    'retrieval_strategy': self.config.retrieval.strategy
                }
            },
            metrics=metrics
        )
        
        # Adicionar ao cache
        if self.cache is not None:
            self._add_to_cache(question, result)
        
        self.logger.info(f"✅ Query processada em {total_time:.2f}s")
        
        return result
    
    def _check_cache(self, query: str) -> Optional[QueryResult]:
        """
        Verifica se existe resposta em cache para query similar.
        
        Args:
            query: Query atual
            
        Returns:
            QueryResult do cache ou None
        """
        # TODO: Implementar cache semântico usando embeddings
        # Por enquanto, apenas cache exato
        return self.cache.get(query)
    
    def _add_to_cache(self, query: str, result: QueryResult):
        """
        Adiciona resultado ao cache.
        
        Args:
            query: Query
            result: Resultado a cachear
        """
        if len(self.cache) >= self.config.cache.max_size:
            # Remover entrada mais antiga (FIFO simples)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[query] = result
    
    def _evaluate_response(
        self,
        question: str,
        answer: str,
        chunks: List[Dict],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Avalia qualidade da resposta usando métricas disponíveis.
        
        Args:
            question: Pergunta
            answer: Resposta gerada
            chunks: Chunks recuperados
            ground_truth: Resposta esperada (opcional)
            
        Returns:
            Dicionário com métricas
        """
        metrics = {}
        
        try:
            # Métricas básicas RAG
            if self.rag_evaluator is None:
                from src.evaluation.metrics import create_rag_evaluator
                self.rag_evaluator = create_rag_evaluator()
            
            rag_metrics = self.rag_evaluator.evaluate(
                query=question,
                answer=answer,
                context=chunks
            )
            metrics.update(rag_metrics)
            
            # BERTScore (se tiver ground truth)
            if ground_truth:
                if self.bert_evaluator is None:
                    from src.evaluation.metrics import create_bertscore_evaluator
                    self.bert_evaluator = create_bertscore_evaluator()
                
                bert_result = self.bert_evaluator.evaluate_single(
                    candidate=answer,
                    reference=ground_truth
                )
                metrics['bertscore_f1'] = bert_result.f1
                metrics['bertscore_precision'] = bert_result.precision
                metrics['bertscore_recall'] = bert_result.recall
            
            # RAGAS (se configurado)
            if os.getenv('RAGAS_API_KEY') or os.getenv('GOOGLE_API_KEY'):
                if self.ragas_evaluator is None:
                    from src.evaluation.metrics import create_ragas_evaluator
                    self.ragas_evaluator = create_ragas_evaluator(verbose=False)
                
                contexts = [[c.get('content', c.get('text', '')) for c in chunks]]
                
                ragas_result = self.ragas_evaluator.evaluate_single(
                    question=question,
                    answer=answer,
                    context=contexts[0],
                    ground_truth=ground_truth,
                    metrics=['faithfulness', 'answer_relevancy']
                )
                
                metrics['faithfulness'] = ragas_result.faithfulness
                metrics['answer_relevancy'] = ragas_result.answer_relevancy
                
        except Exception as e:
            self.logger.warning(f"Erro ao calcular métricas: {e}")
        
        return metrics
    
    def batch_query(
        self,
        questions: List[str],
        evaluate: bool = False,
        ground_truths: Optional[List[str]] = None
    ) -> List[QueryResult]:
        """
        Processa múltiplas queries em lote.
        
        Args:
            questions: Lista de perguntas
            evaluate: Se True, calcula métricas
            ground_truths: Respostas esperadas (opcional)
            
        Returns:
            Lista de QueryResult
        """
        results = []
        
        for i, question in enumerate(questions):
            ground_truth = ground_truths[i] if ground_truths else None
            
            result = self.query(
                question=question,
                evaluate=evaluate,
                ground_truth=ground_truth
            )
            
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do pipeline.
        
        Returns:
            Dicionário com estatísticas
        """
        vector_store_stats = self.vector_store.get_stats()
        
        return {
            'vector_store': vector_store_stats,
            'cache_size': len(self.cache) if self.cache else 0,
            'config': {
                'retrieval_strategy': self.config.retrieval.strategy,
                'top_k': self.config.retrieval.top_k,
                'llm_model': self.config.generation.model,
                'embedding_model': self.config.embeddings.model,
                'chunking_strategy': self.config.chunking.strategy
            }
        }
    
    def clear_cache(self):
        """Limpa o cache de queries"""
        if self.cache:
            self.cache.clear()
            self.logger.info("Cache limpo")
    
    def save_query_log(self, result: QueryResult, output_file: str):
        """
        Salva log de query em arquivo JSON.
        
        Args:
            result: Resultado da query
            output_file: Caminho do arquivo de saída
        """
        log_entry = result.to_dict()
        
        # Criar diretório se não existir
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append ao arquivo (JSONL format)
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        self.logger.info(f"Log salvo em {output_file}")


# Factory function
def create_rag_pipeline(
    config_path: Optional[str] = None,
    verbose: bool = False
) -> RAGPipeline:
    """
    Factory function para criar RAGPipeline.
    
    Args:
        config_path: Caminho para arquivo de configuração YAML (opcional)
        verbose: Se True, imprime logs detalhados
        
    Returns:
        RAGPipeline configurado
    """
    if config_path:
        config = load_config(config_path)
    else:
        config = load_config()
    
    return RAGPipeline(config=config, verbose=verbose)


if __name__ == "__main__":
    # Teste rápido do pipeline
    print("🧪 TESTE DO RAG PIPELINE")
    print("="*80)
    
    # Criar pipeline
    pipeline = create_rag_pipeline(verbose=True)
    
    print("\n📊 Estatísticas do Pipeline:")
    stats = pipeline.get_stats()
    print(f"   Vector Store: {stats['vector_store']['count']} documentos")
    print(f"   Estratégia Retrieval: {stats['config']['retrieval_strategy']}")
    print(f"   Modelo LLM: {stats['config']['llm_model']}")
    
    print("\n" + "="*80)
    print("✅ Pipeline RAG pronto para uso")

