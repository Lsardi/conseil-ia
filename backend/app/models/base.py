"""Classe de base abstraite pour tous les adaptateurs de modèles IA."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

from ..config.logging_config import get_logger
from ..config.settings import MODEL_COSTS

logger = get_logger("models.base")


@dataclass
class ModelResult:
    """Résultat brut d'un appel à un modèle IA."""

    content: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    cost: float = 0.0
    model_name: str = ""
    error: Optional[str] = None
    raw_response: Optional[dict] = field(default=None, repr=False)


class BaseModelAdapter(ABC):
    """Interface commune pour tous les adaptateurs de modèles IA.

    Chaque modèle (Claude, GPT-4, Gemini, etc.) implémente cette interface.
    """

    model_name: str = "base"

    def __init__(self) -> None:
        self._logger = get_logger(f"models.{self.model_name}")

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> ModelResult:
        """Génère une réponse à partir d'un prompt.

        Args:
            prompt: Le texte du prompt.
            temperature: Contrôle la créativité (0.0 = déterministe, 2.0 = très créatif).
            max_tokens: Nombre maximum de tokens dans la réponse.

        Returns:
            ModelResult avec le contenu et les métadonnées.
        """

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        """Génère une réponse en streaming.

        Args:
            prompt: Le texte du prompt.
            temperature: Contrôle la créativité.
            max_tokens: Nombre maximum de tokens.

        Yields:
            Fragments de texte au fur et à mesure.
        """

    @abstractmethod
    def is_configured(self) -> bool:
        """Vérifie que l'adaptateur est correctement configuré (clé API, etc.)."""

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calcule le coût en dollars d'un appel."""
        costs = MODEL_COSTS.get(self.model_name, {"input": 0, "output": 0})
        return (tokens_input / 1000 * costs["input"]) + (
            tokens_output / 1000 * costs["output"]
        )

    async def safe_generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> ModelResult:
        """Wrapper sécurisé autour de generate avec logging et gestion d'erreurs."""
        start_time = time.perf_counter()
        self._logger.info(
            "Appel au modèle %s",
            self.model_name,
            extra={
                "extra_data": {
                    "model": self.model_name,
                    "prompt_length": len(prompt),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            },
        )

        try:
            result = await self.generate(
                prompt, temperature=temperature, max_tokens=max_tokens
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result.latency_ms = elapsed_ms
            result.model_name = self.model_name
            result.cost = self.calculate_cost(result.tokens_input, result.tokens_output)

            self._logger.info(
                "Réponse reçue de %s en %.0fms",
                self.model_name,
                elapsed_ms,
                extra={
                    "extra_data": {
                        "model": self.model_name,
                        "latency_ms": elapsed_ms,
                        "tokens_input": result.tokens_input,
                        "tokens_output": result.tokens_output,
                        "cost": result.cost,
                        "content_length": len(result.content),
                    }
                },
            )
            return result

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._logger.error(
                "Erreur modèle %s après %.0fms: %s",
                self.model_name,
                elapsed_ms,
                str(exc),
                exc_info=True,
                extra={
                    "extra_data": {
                        "model": self.model_name,
                        "latency_ms": elapsed_ms,
                        "error_type": type(exc).__name__,
                    }
                },
            )
            return ModelResult(
                model_name=self.model_name,
                latency_ms=elapsed_ms,
                error=f"{type(exc).__name__}: {exc}",
            )
