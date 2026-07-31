from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Iterator

from aidoor.providers.models import ModelInfo


@dataclasses.dataclass(frozen=True)
class ProviderInfo:
    id: str
    display_name: str
    local: bool
    streaming: bool
    tools: bool
    vision: bool
    embeddings: bool


class Provider(ABC):
    @abstractmethod
    def health(self) -> bool:
        ...

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        ...

    @abstractmethod
    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> Iterator[str]:
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    def provider_type(self) -> str:
        ...

    def supports_streaming(self) -> bool:
        return False

    def supports_tools(self) -> bool:
        return False

    def supports_images(self) -> bool:
        return False

    def supports_embeddings(self) -> bool:
        return False
