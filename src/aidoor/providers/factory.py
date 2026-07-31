from __future__ import annotations

from aidoor.config import AppConfig
from aidoor.providers.base import Provider
from aidoor.providers.ollama import OllamaProvider
from aidoor.providers.registry import ProviderRegistry

_registry: ProviderRegistry | None = None


def _get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        _registry.register("ollama", OllamaProvider)
    return _registry


def set_registry(registry: ProviderRegistry) -> None:
    global _registry
    _registry = registry


def reset_registry() -> None:
    global _registry
    _registry = None


def create_provider(config: AppConfig) -> Provider:
    provider_type = config.provider.type
    registry = _get_registry()
    provider_cls = registry.get(provider_type)
    return provider_cls(config.ollama)  # type: ignore[call-arg]
