from typing import Optional, Tuple


def answer_question(question: str, context: Optional[str] = None) -> Tuple[str, float, str]:
    """
    Placeholder function to answer a question.

    Retorna uma tupla (answer, confidence, source).

    Substitua esta função pela integração com o modelo/serviço desejado
    (ex.: chamada a LLM, RAG pipeline, buscador + prompt, etc.).
    """
    # Implementação mínima: ecoa a pergunta e fornece informação fictícia
    if context:
        answer = f"(Mock) Com base no contexto fornecido: resposta para '{question}'"
    else:
        answer = f"(Mock) Resposta para '{question}'"

    confidence = 0.5
    source = "mock"

    return answer, confidence, source
