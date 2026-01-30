"""Adaptateur pour Google Gemini via google-generativeai."""

from __future__ import annotations

from typing import AsyncIterator, Optional

import google.generativeai as genai

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.gemini")


class GeminiAdapter(BaseModelAdapter):
    """Adaptateur pour Gemini via le SDK google-generativeai."""

    model_name = "gemini"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.google_cloud_project  # Peut servir de clé API
        self._model_id = "gemini-1.5-flash"
        self._configured = False

        # Configurer avec la clé API ou les credentials par défaut
        if self._api_key:
            genai.configure(api_key=self._api_key)
            self._configured = True
            logger.debug("Client Gemini initialisé avec clé API")

    def is_configured(self) -> bool:
        return self._configured

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> ModelResult:
        logger.debug(
            "Envoi requête Gemini",
            extra={"extra_data": {"model_id": self._model_id}},
        )

        model = genai.GenerativeModel(
            self._model_id,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        response = await model.generate_content_async(prompt)

        content = response.text or ""
        tokens_in = 0
        tokens_out = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_in = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            tokens_out = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

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
        logger.debug("Démarrage streaming Gemini")

        model = genai.GenerativeModel(
            self._model_id,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        response = await model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text
