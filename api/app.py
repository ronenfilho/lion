from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from .qa import answer_question


class AskRequest(BaseModel):
    question: str
    context: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    confidence: Optional[float] = None
    source: Optional[str] = None


app = FastAPI(title="LION Q&A API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """Recebe uma pergunta e retorna a resposta.

    Este endpoint chama `answer_question` em `api.qa`.
    Troque a implementação de `answer_question` para integrar seu modelo.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Campo 'question' é obrigatório")

    answer, confidence, source = answer_question(req.question, req.context)

    return AskResponse(answer=answer, confidence=confidence, source=source)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
