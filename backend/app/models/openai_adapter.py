"""Adaptateur pour l'API OpenAI (GPT-4)."""

from __future__ import annotations

from typing import AsyncIterator

import openai

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.openai")


class OpenAIAdapter(BaseModelAdapter):
    """Adaptateur pour GPT-4 via l'API OpenAI."""

    model_name = "gpt4"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._client: openai.AsyncOpenAI | None = None
        self._model_id = "gpt-4o"

    def _get_client(self) -> openai.AsyncOpenAI:
        if self._client is None:
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
            logger.debug("Client OpenAI initialisé")
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
            "Envoi requête GPT-4",
            extra={"extra_data": {"model_id": self._model_id}},
        )

        response = await client.chat.completions.create(
            model=self._model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        choice = response.choices[0]
        usage = response.usage

        return ModelResult(
            content=choice.message.content or "",
            tokens_input=usage.prompt_tokens if usage else 0,
            tokens_output=usage.completion_tokens if usage else 0,
        )

    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        logger.debug("Démarrage streaming GPT-4")

        stream = await client.chat.completions.create(
            model=self._model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
