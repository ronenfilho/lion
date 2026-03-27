"""Configuration module - loads environment variables and settings."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from .env"""

    # LLM API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")  # groq, openai, anthropic, google
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "800"))

    # Retrieval Configuration
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    HYBRID_ALPHA: float = float(os.getenv("HYBRID_ALPHA", "0.7"))

    # Vector Store
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "3072"))

    # API Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))

    @staticmethod
    def get_api_key(provider: str) -> str:
        """Get API key for a given provider."""
        provider_lower = provider.lower()
        if provider_lower == "openai":
            return Settings.OPENAI_API_KEY
        elif provider_lower == "groq":
            return Settings.GROQ_API_KEY
        elif provider_lower == "anthropic":
            return Settings.ANTHROPIC_API_KEY
        elif provider_lower == "google":
            return Settings.GOOGLE_API_KEY
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def validate():
        """Validate that required settings are configured."""
        if not Settings.GROQ_API_KEY and not Settings.OPENAI_API_KEY:
            raise ValueError(
                "At least one API key (GROQ_API_KEY or OPENAI_API_KEY) must be configured in .env"
            )
        if not os.path.exists(Settings.CHROMA_PERSIST_DIR):
            os.makedirs(Settings.CHROMA_PERSIST_DIR, exist_ok=True)


settings = Settings()
