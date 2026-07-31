from __future__ import annotations

from aidoor.providers.base import Provider
from aidoor.providers.errors import ProviderConfigurationError


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[Provider]] = {}

    def register(self, provider_type: str, provider_cls: type[Provider]) -> None:
        self._providers[provider_type] = provider_cls

    def get(self, provider_type: str) -> type[Provider]:
        cls = self._providers.get(provider_type)
        if cls is None:
            known = ", ".join(sorted(self._providers))
            raise ProviderConfigurationError(
                f"Unknown provider type: {provider_type!r}. "
                f"Known providers: {known}"
            )
        return cls

    def list_providers(self) -> list[str]:
        return list(self._providers)
