"""FastAPI application with RAG-based Q&A endpoints."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.api.qa import answer_question
from app.api.config import settings

# Validate settings on startup
try:
    settings.validate()
except ValueError as e:
    print(f"Warning: {e}")


class AskRequest(BaseModel):
    """Request model for /ask endpoint."""

    question: str
    context: Optional[str] = None


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""

    answer: str
    confidence: float
    source: str


# Initialize FastAPI app
app = FastAPI(
    title="LION Q&A API",
    description="RAG-based Question & Answer system",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "LION Q&A API"}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """
    Ask a question and get an answer using RAG pipeline.

    The system retrieves relevant documents and generates an answer using an LLM.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Campo 'question' é obrigatório e não pode estar vazio")

    try:
        answer, confidence, source = answer_question(req.question, req.context)
        return AskResponse(answer=answer, confidence=confidence, source=source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.app:app", host="0.0.0.0", port=8000, reload=True)
