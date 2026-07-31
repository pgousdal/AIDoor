from __future__ import annotations

from aidoor.providers.errors import (
    ProviderError,
    ProviderModelNotFoundError,
    ProviderResponseError,
    ProviderUnavailable,
)


class OllamaError(ProviderError):
    pass


class OllamaConnectionError(ProviderUnavailable):
    pass


class OllamaTimeoutError(ProviderUnavailable):
    pass


class OllamaModelNotFoundError(ProviderModelNotFoundError):
    pass


class OllamaInvalidResponseError(ProviderResponseError):
    pass
