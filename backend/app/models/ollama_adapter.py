"""Adaptateur pour Ollama (modèles locaux : Llama, Mistral, etc.)."""

from __future__ import annotations

from typing import AsyncIterator

import httpx

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.ollama")


class OllamaAdapter(BaseModelAdapter):
    """Adaptateur pour les modèles locaux via Ollama.

    Ollama permet d'exécuter des LLM en local (Llama 3, Mistral, Phi, etc.)
    sans coût API. Nécessite que Ollama soit installé et lancé.
    """

    model_name = "ollama"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._base_url = settings.ollama_base_url
        self._model_id = settings.ollama_model
        self._enabled = settings.ollama_enabled
        self._timeout = settings.request_timeout

    def is_configured(self) -> bool:
        return self._enabled

    async def _check_availability(self) -> bool:
        """Vérifie que le serveur Ollama est accessible."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> ModelResult:
        logger.debug(
            "Envoi requête Ollama (local)",
            extra={
                "extra_data": {
                    "model_id": self._model_id,
                    "base_url": self._base_url,
                }
            },
        )

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        tokens_in = data.get("prompt_eval_count", 0)
        tokens_out = data.get("eval_count", 0)

        return ModelResult(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
        )

    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        logger.debug("Démarrage streaming Ollama (local)")

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            ) as response:
                import json

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        msg = data.get("message", {})
                        if msg.get("content"):
                            yield msg["content"]
