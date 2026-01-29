"""Schémas Pydantic pour les requêtes et réponses de l'API."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ResponseMode(str, Enum):
    """Modes de réponse disponibles."""

    SYNTHESIS = "synthesis"
    DETAILED = "detailed"
    DEBATE = "debate"


class ModelName(str, Enum):
    """Modèles IA supportés."""

    CLAUDE = "claude"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


class CouncilRequest(BaseModel):
    """Requête envoyée au conseil des IA."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="La question à poser au conseil",
    )
    mode: ResponseMode = Field(
        default=ResponseMode.SYNTHESIS,
        description="Mode de réponse souhaité",
    )
    models: list[ModelName] = Field(
        default=[ModelName.CLAUDE, ModelName.GPT4, ModelName.GEMINI],
        description="Modèles à interroger",
    )
    optimize_prompts: bool = Field(
        default=True,
        description="Optimiser les prompts pour chaque modèle",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Température pour la génération",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=16000,
        description="Nombre max de tokens (défaut: config serveur)",
    )
    stream: bool = Field(
        default=False,
        description="Activer le streaming de la réponse",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Identifiant utilisateur pour le tracking",
    )


class ModelResponse(BaseModel):
    """Réponse individuelle d'un modèle IA."""

    model: str
    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    cost: float = 0.0
    error: Optional[str] = None
    cached: bool = False


class CouncilResponse(BaseModel):
    """Réponse complète du conseil des IA."""

    synthesis: Optional[str] = None
    responses: dict[str, ModelResponse] = {}
    consensus_score: Optional[float] = None
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    cached: bool = False
    mode: ResponseMode = ResponseMode.SYNTHESIS
    request_id: str = ""


class HealthResponse(BaseModel):
    """Réponse du health check."""

    status: str = "healthy"
    version: str = ""
    environment: str = ""
    models_configured: dict[str, bool] = {}
    cache_enabled: bool = False


class StatsResponse(BaseModel):
    """Statistiques d'utilisation."""

    total_requests: int = 0
    total_cost: float = 0.0
    cache_hit_rate: float = 0.0
    avg_latency_ms: float = 0.0
    requests_by_model: dict[str, int] = {}
    requests_by_mode: dict[str, int] = {}


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""

    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
    status_code: int = 500
