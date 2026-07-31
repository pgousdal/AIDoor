from __future__ import annotations

from aidoor.errors import AIDoorError


class ProviderError(AIDoorError):
    pass


class ProviderUnavailable(ProviderError):
    pass


class ProviderAuthenticationError(ProviderError):
    pass


class ProviderConfigurationError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
    pass


class ProviderModelNotFoundError(ProviderError):
    pass
