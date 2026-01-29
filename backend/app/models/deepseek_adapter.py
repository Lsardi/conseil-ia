"""Adaptateur pour l'API DeepSeek (compatible OpenAI)."""

from __future__ import annotations

from typing import AsyncIterator

import openai

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.deepseek")


class DeepSeekAdapter(BaseModelAdapter):
    """Adaptateur pour DeepSeek via son API compatible OpenAI."""

    model_name = "deepseek"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.deepseek_api_key
        self._client: openai.AsyncOpenAI | None = None
        self._model_id = "deepseek-chat"
        self._base_url = "https://api.deepseek.com"

    def _get_client(self) -> openai.AsyncOpenAI:
        if self._client is None:
            self._client = openai.AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
            logger.debug("Client DeepSeek initialisé")
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
            "Envoi requête DeepSeek",
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
        logger.debug("Démarrage streaming DeepSeek")

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
