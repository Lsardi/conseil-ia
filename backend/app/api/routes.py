"""Routes de l'API REST du Conseil des IA."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config.logging_config import get_logger
from ..config.schemas import (
    CouncilRequest,
    CouncilResponse,
    ErrorResponse,
    HealthResponse,
    StatsResponse,
)
from ..config.settings import get_settings
from ..services.orchestrator import Orchestrator

logger = get_logger("api.routes")

router = APIRouter(prefix="/api/v1", tags=["council"])

# Instance globale de l'orchestrateur
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Retourne l'instance singleton de l'orchestrateur."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Vérifie l'état de santé du service."""
    settings = get_settings()
    orchestrator = get_orchestrator()

    logger.debug("Health check demandé")

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment.value,
        models_configured=orchestrator.get_configured_models(),
        cache_enabled=settings.cache_enabled,
    )


@router.post(
    "/council/ask",
    response_model=CouncilResponse,
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def ask_council(request: CouncilRequest) -> CouncilResponse:
    """Interroge le conseil des IA.

    Envoie la question à tous les modèles sélectionnés en parallèle,
    puis synthétise les réponses selon le mode choisi.

    **Modes disponibles:**
    - `synthesis` : Synthèse unifiée (défaut)
    - `detailed` : Réponses complètes de chaque IA
    - `debate` : Les IA débattent entre elles
    """
    orchestrator = get_orchestrator()

    logger.info(
        "Requête /council/ask reçue",
        extra={
            "extra_data": {
                "mode": request.mode.value,
                "models": [m.value for m in request.models],
                "question_preview": request.question[:100],
            }
        },
    )

    try:
        response = await orchestrator.ask(request)
        return response
    except Exception as exc:
        logger.error("Erreur lors du traitement de la requête: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/models", response_model=dict)
async def list_models() -> dict:
    """Liste les modèles disponibles et leur état."""
    orchestrator = get_orchestrator()
    configured = orchestrator.get_configured_models()

    return {
        "models": [
            {
                "name": name,
                "configured": is_configured,
                "type": "local" if name == "ollama" else "cloud",
            }
            for name, is_configured in configured.items()
        ]
    }


@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Retourne les statistiques d'utilisation."""
    orchestrator = get_orchestrator()
    stats = orchestrator.stats

    logger.debug("Statistiques demandées", extra={"extra_data": stats})

    return StatsResponse(
        total_requests=stats["total_requests"],
        total_cost=stats["total_cost"],
        avg_latency_ms=stats["avg_latency_ms"],
        cache_hit_rate=stats["cache"]["hit_rate"],
        requests_by_model=stats["requests_by_model"],
        requests_by_mode=stats["requests_by_mode"],
    )
