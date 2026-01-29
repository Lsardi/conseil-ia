"""Adaptateur pour Google Gemini via Vertex AI / google-genai."""

from __future__ import annotations

from typing import AsyncIterator

from google import genai
from google.genai import types

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.gemini")


class GeminiAdapter(BaseModelAdapter):
    """Adaptateur pour Gemini via le SDK google-genai."""

    model_name = "gemini"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._project = settings.google_cloud_project or settings.gcp_project_id
        self._region = settings.gcp_region
        self._client: genai.Client | None = None
        self._model_id = "gemini-2.0-flash"

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(
                vertexai=True,
                project=self._project,
                location=self._region,
            )
            logger.debug("Client Gemini initialisé (Vertex AI)")
        return self._client

    def is_configured(self) -> bool:
        return bool(self._project)

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> ModelResult:
        client = self._get_client()
        logger.debug(
            "Envoi requête Gemini",
            extra={"extra_data": {"model_id": self._model_id}},
        )

        response = await client.aio.models.generate_content(
            model=self._model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        content = response.text or ""
        tokens_in = 0
        tokens_out = 0
        if response.usage_metadata:
            tokens_in = response.usage_metadata.prompt_token_count or 0
            tokens_out = response.usage_metadata.candidates_token_count or 0

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
        client = self._get_client()
        logger.debug("Démarrage streaming Gemini")

        async for chunk in client.aio.models.generate_content_stream(
            model=self._model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        ):
            if chunk.text:
                yield chunk.text
