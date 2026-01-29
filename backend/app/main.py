"""Point d'entrée de l'application FastAPI - Conseil des IA."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config.logging_config import get_logger, setup_logging
from .config.settings import get_settings
from .middleware.rate_limiter import RateLimiterMiddleware
from .middleware.request_logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Gère le cycle de vie de l'application."""
    # Startup
    setup_logging()
    logger = get_logger("main")
    settings = get_settings()

    logger.info(
        "Démarrage de %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment.value,
        extra={
            "extra_data": {
                "host": settings.host,
                "port": settings.port,
                "models_par_defaut": settings.default_models,
                "cache_enabled": settings.cache_enabled,
                "ollama_enabled": settings.ollama_enabled,
            }
        },
    )

    yield

    # Shutdown
    logger.info("Arrêt de %s", settings.app_name)


def create_app() -> FastAPI:
    """Factory pour créer l'application FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Plateforme multi-modèle intelligente qui interroge simultanément "
            "Claude, GPT-4, Gemini, Mistral, Cohere, DeepSeek et des modèles locaux (Ollama), "
            "puis synthétise leurs réponses."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware (ordre inverse d'exécution)
    app.add_middleware(RateLimiterMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(router)

    return app


app = create_app()
