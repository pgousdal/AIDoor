from __future__ import annotations

from aidoor.errors import AIDoorError


class OllamaError(AIDoorError):
    pass


class OllamaConnectionError(OllamaError):
    pass


class OllamaTimeoutError(OllamaError):
    pass


class OllamaModelNotFoundError(OllamaError):
    pass


class OllamaInvalidResponseError(OllamaError):
    pass
