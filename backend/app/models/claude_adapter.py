"""Adaptateur pour l'API Anthropic (Claude)."""

from __future__ import annotations

from typing import AsyncIterator

import anthropic

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.claude")


class ClaudeAdapter(BaseModelAdapter):
    """Adaptateur pour Claude via l'API Anthropic."""

    model_name = "claude"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.anthropic_api_key
        self._client: anthropic.AsyncAnthropic | None = None
        self._model_id = "claude-sonnet-4-20250514"

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
            logger.debug("Client Anthropic initialisé")
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
            "Envoi requête Claude",
            extra={"extra_data": {"model_id": self._model_id}},
        )

        response = await client.messages.create(
            model=self._model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return ModelResult(
            content=content,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
        )

    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        logger.debug("Démarrage streaming Claude")

        async with client.messages.stream(
            model=self._model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
