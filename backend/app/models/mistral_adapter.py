"""Adaptateur pour l'API Mistral AI."""

from __future__ import annotations

from typing import AsyncIterator

from mistralai import Mistral

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from .base import BaseModelAdapter, ModelResult

logger = get_logger("models.mistral")


class MistralAdapter(BaseModelAdapter):
    """Adaptateur pour Mistral via l'API Mistral AI."""

    model_name = "mistral"

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.mistral_api_key
        self._client: Mistral | None = None
        self._model_id = "mistral-large-latest"

    def _get_client(self) -> Mistral:
        if self._client is None:
            self._client = Mistral(api_key=self._api_key)
            logger.debug("Client Mistral initialisé")
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
            "Envoi requête Mistral",
            extra={"extra_data": {"model_id": self._model_id}},
        )

        response = await client.chat.complete_async(
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
        logger.debug("Démarrage streaming Mistral")

        response = await client.chat.stream_async(
            model=self._model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        async for event in response:
            if (
                event.data
                and event.data.choices
                and event.data.choices[0].delta.content
            ):
                yield event.data.choices[0].delta.content
