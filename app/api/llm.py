"""LLM integration module - supports Groq, OpenAI, Anthropic, Google."""

from typing import Optional
from app.api.config import settings


class LLMProvider:
    """Abstract LLM provider interface."""

    def generate(self, prompt: str, context: str = "", temperature: Optional[float] = None) -> str:
        """Generate response from LLM."""
        raise NotImplementedError


class GroqProvider(LLMProvider):
    """Groq LLM provider."""

    def __init__(self):
        try:
            from groq import Groq
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")

    def generate(self, prompt: str, context: str = "", temperature: Optional[float] = None) -> str:
        """Generate response using Groq."""
        full_prompt = f"{context}\n\nPergunta: {prompt}" if context else prompt
        temp = temperature if temperature is not None else settings.TEMPERATURE

        try:
            message = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=temp,
                max_tokens=settings.MAX_TOKENS,
            )
            return message.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def generate(self, prompt: str, context: str = "", temperature: Optional[float] = None) -> str:
        """Generate response using OpenAI."""
        full_prompt = f"{context}\n\nPergunta: {prompt}" if context else prompt
        temp = temperature if temperature is not None else settings.TEMPERATURE

        try:
            message = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=temp,
                max_tokens=settings.MAX_TOKENS,
            )
            return message.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def generate(self, prompt: str, context: str = "", temperature: Optional[float] = None) -> str:
        """Generate response using Anthropic Claude."""
        full_prompt = f"{context}\n\nPergunta: {prompt}" if context else prompt
        temp = temperature if temperature is not None else settings.TEMPERATURE

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=settings.MAX_TOKENS,
                temperature=temp,
                messages=[{"role": "user", "content": full_prompt}],
            )
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")


def get_llm_provider() -> LLMProvider:
    """Factory function to get configured LLM provider."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        return GroqProvider()
    elif provider == "openai":
        return OpenAIProvider()
    elif provider == "anthropic":
        return AnthropicProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Lazy initialization
_llm_instance = None


def get_llm() -> LLMProvider:
    """Get or create LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm_provider()
    return _llm_instance
