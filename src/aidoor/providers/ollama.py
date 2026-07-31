from __future__ import annotations

from collections.abc import Iterator

from aidoor.config import OllamaConfig
from aidoor.ollama.client import OllamaClient
from aidoor.providers.base import Provider, ProviderInfo
from aidoor.providers.models import ModelInfo


class OllamaProvider(Provider):
    def __init__(self, config: OllamaConfig) -> None:
        self._client = OllamaClient(host=config.host, timeout=config.timeout)

    def health(self) -> bool:
        return self._client.health()

    def list_models(self) -> list[ModelInfo]:
        return self._client.list_models()

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> Iterator[str]:
        return self._client.chat_stream(model, messages)

    def provider_name(self) -> str:
        return "Ollama"

    def provider_type(self) -> str:
        return "ollama"

    def supports_streaming(self) -> bool:
        return True

    @staticmethod
    def info() -> ProviderInfo:
        return ProviderInfo(
            id="ollama",
            display_name="Ollama",
            local=True,
            streaming=True,
            tools=False,
            vision=False,
            embeddings=False,
        )
