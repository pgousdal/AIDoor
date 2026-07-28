from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class ModelSelectionResult:
    model: str | None = None
    cancelled: bool = False

    def __post_init__(self) -> None:
        if self.cancelled and self.model is not None:
            raise ValueError("cancelled result must not have a model")
        if not self.cancelled and self.model is None:
            raise ValueError("non-cancelled result must have a model")
        if self.model is not None and not self.model:
            raise ValueError("model must not be empty")


@dataclasses.dataclass(frozen=True)
class ModelInfo:
    name: str
    modified_at: str
    size: int


@dataclasses.dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclasses.dataclass(frozen=True)
class ChatResponse:
    model: str
    message: Message
    done: bool
    total_duration: int | None = None


@dataclasses.dataclass(frozen=True)
class VersionInfo:
    version: str
