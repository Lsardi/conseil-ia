"""Adaptateur pour l'API Cohere."""

from __future__ import annotations

from typing import AsyncIterator

import cohere

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.cohere")


class CohereAdapter(BaseModelAdapter):
    """Adaptateur pour Cohere Command R+."""

    model_name = "cohere"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.cohere_api_key
        self._client: cohere.AsyncClientV2 | None = None
        self._model_id = "command-r-plus"

    def _get_client(self) -> cohere.AsyncClientV2:
        if self._client is None:
            self._client = cohere.AsyncClientV2(api_key=self._api_key)
            logger.debug("Client Cohere initialisé")
        return self._client

    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> ModelResult:
        client = self._get_client()
        logger.debug(
            "Envoi requête Cohere",
            extra={"extra_data": {"model_id": self._model_id}},
        )

        response = await client.chat(
            model=self._model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        content = ""
        if response.message and response.message.content:
            for block in response.message.content:
                if hasattr(block, "text"):
                    content += block.text

        tokens_in = 0
        tokens_out = 0
        if response.usage and response.usage.tokens:
            tokens_in = response.usage.tokens.input_tokens or 0
            tokens_out = response.usage.tokens.output_tokens or 0

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
        logger.debug("Démarrage streaming Cohere")

        response = client.chat_stream(
            model=self._model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        async for event in response:
            if event.type == "content-delta" and event.delta and event.delta.message:
                if event.delta.message.content and event.delta.message.content.text:
                    yield event.delta.message.content.text
