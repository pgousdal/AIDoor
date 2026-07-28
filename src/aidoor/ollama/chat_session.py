from __future__ import annotations

from aidoor.ollama.models import Message


class ChatSession:
    def __init__(self, model: str, system_prompt: str = "") -> None:
        self._model = model
        self._messages: list[Message] = []
        if system_prompt:
            self._messages.append(Message(role="system", content=system_prompt))

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    def add_user_message(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        self._messages.append(Message(role="assistant", content=content))

    def clear(self) -> None:
        system = [m for m in self._messages if m.role == "system"]
        self._messages = system

    def to_api_format(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self._messages]

    @property
    def message_count(self) -> int:
        return len(self._messages)
