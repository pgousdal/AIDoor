from __future__ import annotations

from aidoor.ollama.chat_session import ChatSession
from aidoor.ollama.models import Message


class TestChatSession:
    def test_default_model(self) -> None:
        s = ChatSession(model="llama3.1")
        assert s.model == "llama3.1"

    def test_set_model(self) -> None:
        s = ChatSession(model="llama3.1")
        s.model = "mistral"
        assert s.model == "mistral"

    def test_empty_messages_initially(self) -> None:
        s = ChatSession(model="llama3.1")
        assert s.messages == []

    def test_system_prompt_included(self) -> None:
        s = ChatSession(model="llama3.1", system_prompt="Be helpful")
        assert len(s.messages) == 1
        assert s.messages[0].role == "system"
        assert s.messages[0].content == "Be helpful"

    def test_add_user_message(self) -> None:
        s = ChatSession(model="llama3.1")
        s.add_user_message("Hello")
        assert len(s.messages) == 1
        assert s.messages[0].role == "user"
        assert s.messages[0].content == "Hello"

    def test_add_assistant_message(self) -> None:
        s = ChatSession(model="llama3.1")
        s.add_user_message("Hello")
        s.add_assistant_message("Hi there")
        assert len(s.messages) == 2
        assert s.messages[1].role == "assistant"

    def test_clear_removes_all_non_system(self) -> None:
        s = ChatSession(model="llama3.1", system_prompt="Be helpful")
        s.add_user_message("Hello")
        s.add_assistant_message("Hi")
        s.clear()
        assert len(s.messages) == 1
        assert s.messages[0].role == "system"

    def test_clear_without_system(self) -> None:
        s = ChatSession(model="llama3.1")
        s.add_user_message("Hello")
        s.clear()
        assert s.messages == []

    def test_to_api_format(self) -> None:
        s = ChatSession(model="llama3.1")
        s.add_user_message("Hello")
        api = s.to_api_format()
        assert api == [{"role": "user", "content": "Hello"}]

    def test_to_api_format_with_system(self) -> None:
        s = ChatSession(model="llama3.1", system_prompt="Be nice")
        s.add_user_message("Hi")
        api = s.to_api_format()
        assert api == [
            {"role": "system", "content": "Be nice"},
            {"role": "user", "content": "Hi"},
        ]

    def test_message_count(self) -> None:
        s = ChatSession(model="llama3.1")
        assert s.message_count == 0
        s.add_user_message("A")
        assert s.message_count == 1
        s.add_assistant_message("B")
        assert s.message_count == 2
        s.clear()
        assert s.message_count == 0

    def test_messages_returns_copy(self) -> None:
        s = ChatSession(model="llama3.1")
        s.add_user_message("Hello")
        msgs = s.messages
        msgs.append(Message(role="user", content="injected"))
        assert s.message_count == 1

    def test_multiple_turns(self) -> None:
        s = ChatSession(model="llama3.1")
        s.add_user_message("Q1")
        s.add_assistant_message("A1")
        s.add_user_message("Q2")
        s.add_assistant_message("A2")
        assert len(s.messages) == 4
        assert s.to_api_format() == [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ]
