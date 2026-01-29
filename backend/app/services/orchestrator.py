"""Orchestrateur central du Conseil des IA.

Coordonne l'interrogation parallèle des modèles, l'optimisation des prompts,
le cache et la synthèse des réponses.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from ..config.logging_config import get_logger
from ..config.schemas import (
    CouncilRequest,
    CouncilResponse,
    ModelResponse,
    ResponseMode,
)
from ..config.settings import PROMPT_TEMPLATES, get_settings
from ..models.base import BaseModelAdapter, ModelResult
from ..models.claude_adapter import ClaudeAdapter
from ..models.cohere_adapter import CohereAdapter
from ..models.deepseek_adapter import DeepSeekAdapter
from ..models.gemini_adapter import GeminiAdapter
from ..models.mistral_adapter import MistralAdapter
from ..models.ollama_adapter import OllamaAdapter
from ..models.openai_adapter import OpenAIAdapter
from .cache import CacheService
from .synthesis import SynthesisService

logger = get_logger("services.orchestrator")


class Orchestrator:
    """Orchestre les appels aux modèles IA et la synthèse des réponses."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._cache = CacheService()
        self._synthesis = SynthesisService()

        # Registre des adaptateurs
        self._adapters: dict[str, BaseModelAdapter] = {
            "claude": ClaudeAdapter(),
            "gpt4": OpenAIAdapter(),
            "gemini": GeminiAdapter(),
            "mistral": MistralAdapter(),
            "cohere": CohereAdapter(),
            "deepseek": DeepSeekAdapter(),
            "ollama": OllamaAdapter(),
        }

        # Statistiques
        self._total_requests = 0
        self._total_cost = 0.0
        self._requests_by_model: dict[str, int] = {}
        self._requests_by_mode: dict[str, int] = {}
        self._total_latency_ms = 0.0

        logger.info(
            "Orchestrateur initialisé",
            extra={
                "extra_data": {
                    "models_disponibles": list(self._adapters.keys()),
                    "models_configurés": {
                        name: adapter.is_configured()
                        for name, adapter in self._adapters.items()
                    },
                }
            },
        )

    def get_configured_models(self) -> dict[str, bool]:
        """Retourne l'état de configuration de chaque modèle."""
        return {
            name: adapter.is_configured()
            for name, adapter in self._adapters.items()
        }

    async def ask(self, request: CouncilRequest) -> CouncilResponse:
        """Traite une requête du conseil.

        1. Vérifie le cache
        2. Optimise les prompts
        3. Interroge les modèles en parallèle
        4. Synthétise les réponses
        5. Met en cache le résultat

        Args:
            request: La requête du conseil.

        Returns:
            La réponse complète du conseil.
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        logger.info(
            "Nouvelle requête [%s]",
            request_id,
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "question_length": len(request.question),
                    "mode": request.mode.value,
                    "models": [m.value for m in request.models],
                    "optimize_prompts": request.optimize_prompts,
                }
            },
        )

        model_names = [m.value for m in request.models]

        # 1. Vérifier le cache
        cached = await self._cache.get(
            request.question, model_names, request.mode.value
        )
        if cached:
            logger.info(
                "Réponse servie depuis le cache [%s]",
                request_id,
                extra={"extra_data": {"request_id": request_id, "cached": True}},
            )
            response = CouncilResponse(**cached)
            response.cached = True
            response.request_id = request_id
            return response

        # 2. Filtrer les modèles configurés
        active_models = [
            name
            for name in model_names
            if name in self._adapters and self._adapters[name].is_configured()
        ]

        if not active_models:
            logger.error(
                "Aucun modèle configuré parmi %s [%s]",
                model_names,
                request_id,
            )
            return CouncilResponse(
                synthesis="Erreur: aucun modèle configuré. Vérifiez vos clés API.",
                request_id=request_id,
                mode=request.mode,
            )

        logger.info(
            "Modèles actifs pour cette requête [%s]: %s",
            request_id,
            active_models,
        )

        # 3. Optimiser les prompts
        prompts: dict[str, str] = {}
        for model_name in active_models:
            if request.optimize_prompts and model_name in PROMPT_TEMPLATES:
                template = PROMPT_TEMPLATES[model_name]
                prompts[model_name] = (
                    f"{template['prefix']}\n\n"
                    f"Question: {request.question}\n\n"
                    f"{template['suffix']}"
                )
            else:
                prompts[model_name] = request.question

        # 4. Interroger en parallèle
        logger.debug(
            "Lancement des appels parallèles [%s]",
            request_id,
        )

        tasks = {
            model_name: self._adapters[model_name].safe_generate(
                prompts[model_name],
                temperature=request.temperature,
                max_tokens=request.max_tokens or self._settings.max_tokens,
            )
            for model_name in active_models
        }

        results: dict[str, ModelResult] = {}
        task_results = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )

        for model_name, result in zip(tasks.keys(), task_results):
            if isinstance(result, Exception):
                logger.error(
                    "Exception non gérée pour %s [%s]: %s",
                    model_name,
                    request_id,
                    result,
                    exc_info=True,
                )
                results[model_name] = ModelResult(
                    model_name=model_name,
                    error=f"Exception: {result}",
                )
            else:
                results[model_name] = result

        # 5. Synthétiser
        synthesis_text = None
        consensus_score = None

        if request.mode == ResponseMode.SYNTHESIS:
            synthesis_text = await self._synthesis.synthesize(
                request.question, results
            )
            consensus_score = self._synthesis.calculate_consensus(results)
        elif request.mode == ResponseMode.DEBATE:
            synthesis_text = await self._synthesis.create_debate(
                request.question, results
            )
            consensus_score = self._synthesis.calculate_consensus(results)

        # 6. Construire la réponse
        total_cost = sum(r.cost for r in results.values())
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        model_responses = {
            name: ModelResponse(
                model=name,
                content=r.content,
                tokens_input=r.tokens_input,
                tokens_output=r.tokens_output,
                latency_ms=r.latency_ms,
                cost=r.cost,
                error=r.error,
            )
            for name, r in results.items()
        }

        response = CouncilResponse(
            synthesis=synthesis_text,
            responses=model_responses,
            consensus_score=consensus_score,
            total_cost=total_cost,
            total_latency_ms=elapsed_ms,
            cached=False,
            mode=request.mode,
            request_id=request_id,
        )

        # 7. Mettre en cache
        await self._cache.set(
            request.question,
            model_names,
            request.mode.value,
            response.model_dump(),
        )

        # 8. Mettre à jour les stats
        self._total_requests += 1
        self._total_cost += total_cost
        self._total_latency_ms += elapsed_ms
        for name in active_models:
            self._requests_by_model[name] = (
                self._requests_by_model.get(name, 0) + 1
            )
        self._requests_by_mode[request.mode.value] = (
            self._requests_by_mode.get(request.mode.value, 0) + 1
        )

        logger.info(
            "Requête terminée [%s] en %.0fms, coût: $%.4f",
            request_id,
            elapsed_ms,
            total_cost,
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "total_latency_ms": elapsed_ms,
                    "total_cost": total_cost,
                    "models_responded": [
                        n for n, r in results.items() if not r.error
                    ],
                    "models_failed": [
                        n for n, r in results.items() if r.error
                    ],
                    "consensus_score": consensus_score,
                }
            },
        )

        return response

    @property
    def stats(self) -> dict[str, Any]:
        """Retourne les statistiques de l'orchestrateur."""
        avg_latency = (
            self._total_latency_ms / self._total_requests
            if self._total_requests > 0
            else 0.0
        )
        return {
            "total_requests": self._total_requests,
            "total_cost": round(self._total_cost, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "requests_by_model": self._requests_by_model,
            "requests_by_mode": self._requests_by_mode,
            "cache": self._cache.stats,
        }
