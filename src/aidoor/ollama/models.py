from __future__ import annotations

import dataclasses

from aidoor.providers.models import Message, ModelInfo, ModelSelectionResult

__all__ = [
    "ChatResponse",
    "Message",
    "ModelInfo",
    "ModelSelectionResult",
    "VersionInfo",
]


@dataclasses.dataclass(frozen=True)
class ChatResponse:
    model: str
    message: Message
    done: bool
    total_duration: int | None = None


@dataclasses.dataclass(frozen=True)
class VersionInfo:
    version: str
