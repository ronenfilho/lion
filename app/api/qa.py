"""RAG QA system - combines retrieval and LLM generation."""

from typing import Optional, Tuple, List, Dict, Any
from app.api.retriever import get_retriever_instance
from app.api.llm import get_llm


def answer_question(question: str, context: Optional[str] = None) -> Tuple[str, float, str, List[Dict[str, Any]]]:
    """
    Answer a question using RAG pipeline:
    1. Retrieve relevant documents
    2. Build context from retrieved docs
    3. Generate answer using LLM

    Returns:
        (answer, confidence, source, chunks_with_citations)
    """
    try:
        # Step 1: Retrieve relevant documents
        retriever = get_retriever_instance()
        retrieved_docs = retriever.retrieve(question)

        if not retrieved_docs:
            return (
                "Desculpe, não encontrei informações relevantes para sua pergunta.",
                0.0,
                "retriever_no_results",
                [],
            )

        # Step 2: Build context from retrieved documents with citations
        context_parts = []
        chunks = []
        for idx, (doc, score, chunk_id) in enumerate(retrieved_docs, 1):
            citation = f"[{chunk_id}]"
            context_parts.append(f"- {doc} {citation}")
            chunks.append({
                "index": idx,
                "chunk_id": chunk_id,
                "content": doc,
                "score": score,
            })
        
        context_text = "\n".join(context_parts)
        full_context = f"{context}\n\n{context_text}" if context else context_text

        # Step 3: Generate answer using LLM
        llm = get_llm()
        answer = llm.generate(
            prompt=f"Com base no contexto fornecido, responda à pergunta de forma clara e concisa. Use as citações do contexto quando apropriado.\n\nPergunta: {question}",
            context=full_context,
        )

        # Calculate confidence based on retrieval scores
        confidence = sum(score for _, score, _ in retrieved_docs) / len(retrieved_docs)

        source = f"RAG (retriever + {type(llm).__name__})"

        return answer, confidence, source, chunks

    except Exception as e:
        return (
            f"Erro ao processar sua pergunta: {str(e)}",
            0.0,
            f"error: {type(e).__name__}",
            [],
        )
