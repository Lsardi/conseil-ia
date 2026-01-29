"""Configuration centralisée de l'application."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Environnements d'exécution."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Niveaux de log disponibles."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Configuration globale chargée depuis les variables d'environnement."""

    # --- Application ---
    app_name: str = "Conseil des IA"
    app_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080

    # --- Logging ---
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"  # "json" ou "text"
    log_file: Optional[str] = None

    # --- API Keys ---
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_cloud_project: str = ""
    google_application_credentials: Optional[str] = None
    mistral_api_key: str = ""
    cohere_api_key: str = ""
    deepseek_api_key: str = ""

    # --- Ollama (Local) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_enabled: bool = False

    # --- GCP ---
    gcp_project_id: str = ""
    gcp_region: str = "europe-west1"

    # --- Firestore Cache ---
    firestore_collection: str = "conseil_cache"
    cache_ttl: int = 3600
    cache_enabled: bool = True

    # --- Modèles IA ---
    default_models: list[str] = ["claude", "gpt4", "gemini"]
    max_tokens: int = 4000
    default_temperature: float = 0.7
    request_timeout: int = 30

    # --- Rate Limiting ---
    rate_limit_per_minute: int = 20
    max_cost_per_user_per_day: float = 5.0

    # --- CORS ---
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # --- Streaming ---
    enable_streaming: bool = True

    # --- Prompt Templates ---
    prompt_optimization_enabled: bool = True

    @field_validator(
        "anthropic_api_key",
        "openai_api_key",
        "mistral_api_key",
        "cohere_api_key",
        "deepseek_api_key",
        mode="before",
    )
    @classmethod
    def allow_empty_keys(cls, v: str) -> str:
        """Accepte les clés vides en dev."""
        return v or ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance singleton des settings."""
    return Settings()


# Templates de prompts optimisés par modèle
PROMPT_TEMPLATES = {
    "claude": {
        "prefix": (
            "Tu es un expert rigoureux et nuancé. "
            "Structure ta réponse avec des sections claires. "
            "Cite tes sources de raisonnement."
        ),
        "suffix": "Sois concis mais complet.",
    },
    "gpt4": {
        "prefix": (
            "You are a knowledgeable expert. "
            "Provide a well-structured, thorough answer. "
            "Use examples where helpful."
        ),
        "suffix": "Be precise and actionable.",
    },
    "gemini": {
        "prefix": (
            "Provide a comprehensive and accurate response. "
            "Include relevant context and practical insights. "
            "Structure your answer clearly."
        ),
        "suffix": "Focus on accuracy and clarity.",
    },
    "mistral": {
        "prefix": (
            "Tu es un assistant expert. "
            "Fournis une réponse structurée, précise et argumentée."
        ),
        "suffix": "Sois rigoureux dans ton analyse.",
    },
    "cohere": {
        "prefix": (
            "You are an expert assistant. "
            "Provide a clear, well-organized answer with relevant details."
        ),
        "suffix": "Be thorough yet concise.",
    },
    "deepseek": {
        "prefix": (
            "You are a highly capable reasoning assistant. "
            "Think step by step and provide a well-structured answer."
        ),
        "suffix": "Show your reasoning clearly.",
    },
    "ollama": {
        "prefix": (
            "You are a helpful assistant. "
            "Provide a clear and structured response."
        ),
        "suffix": "Be concise and accurate.",
    },
}

# Coûts estimés par 1K tokens (input/output)
MODEL_COSTS = {
    "claude": {"input": 0.003, "output": 0.015},
    "gpt4": {"input": 0.01, "output": 0.03},
    "gemini": {"input": 0.00025, "output": 0.0005},
    "mistral": {"input": 0.002, "output": 0.006},
    "cohere": {"input": 0.0005, "output": 0.0015},
    "deepseek": {"input": 0.0014, "output": 0.0028},
    "ollama": {"input": 0.0, "output": 0.0},  # Local = gratuit
}
