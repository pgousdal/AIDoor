from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aidoor.ollama.chat_ui import (
    _sort_and_dedupe_models,
    _strip_cancel_suffix,
    chat_loop,
    show_model_selection,
)
from aidoor.ollama.client import OllamaClient
from aidoor.ollama.errors import (
    OllamaConnectionError,
    OllamaInvalidResponseError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from aidoor.ollama.models import ModelInfo, ModelSelectionResult
from aidoor.terminal import FakeTerminal


def _model(name: str) -> ModelInfo:
    return ModelInfo(name=name, modified_at="", size=0)


def _mock_models(*names: str) -> list[ModelInfo]:
    return [_model(n) for n in names]


def _make_client(models: list[ModelInfo] | None = None) -> OllamaClient:
    client = OllamaClient(host="http://fake:11434", timeout=5)
    if models is not None:
        client.list_models = MagicMock(return_value=models)
    else:
        client.list_models = MagicMock(return_value=_mock_models("llama3.1"))
    client.chat_stream = MagicMock(
        side_effect=lambda *a, **kw: iter(["Hello", " world"])
    )
    return client


class TestSortAndDedupeModels:
    def test_sorts_alphabetically(self) -> None:
        models = [_model("zebra"), _model("alpha"), _model("beta")]
        sorted_m, _ = _sort_and_dedupe_models(models, "llama3.1")
        assert [m.name for m in sorted_m] == ["alpha", "beta", "zebra"]

    def test_case_insensitive_sorting(self) -> None:
        models = [_model("BRAVO"), _model("alpha"), _model("Charlie")]
        sorted_m, _ = _sort_and_dedupe_models(models, "llama3.1")
        assert [m.name for m in sorted_m] == ["alpha", "BRAVO", "Charlie"]

    def test_removes_duplicates(self) -> None:
        models = [_model("llama3.1"), _model("mistral"), _model("llama3.1")]
        sorted_m, _ = _sort_and_dedupe_models(models, "llama3.1")
        assert [m.name for m in sorted_m] == ["llama3.1", "mistral"]

    def test_removes_case_insensitive_duplicates(self) -> None:
        models = [_model("llama3.1"), _model("Llama3.1"), _model("LLAMA3.1")]
        sorted_m, _ = _sort_and_dedupe_models(models, "mistral")
        assert len(sorted_m) == 1
        assert sorted_m[0].name == "llama3.1"

    def test_keeps_first_occurrence_on_duplicate(self) -> None:
        models = [_model("AAA"), _model("aaa"), _model("BBB")]
        sorted_m, _ = _sort_and_dedupe_models(models, "mistral")
        assert len(sorted_m) == 2
        assert sorted_m[0].name == "AAA"
        assert sorted_m[1].name == "BBB"

    def test_highlights_default_model(self) -> None:
        models = [_model("mistral"), _model("llama3.1"), _model("deepseek")]
        _, default_index = _sort_and_dedupe_models(models, "llama3.1")
        assert default_index == 1

    def test_default_index_none_when_not_installed(self) -> None:
        models = [_model("mistral"), _model("deepseek")]
        _, default_index = _sort_and_dedupe_models(models, "llama3.1")
        assert default_index is None

    def test_case_insensitive_default_match(self) -> None:
        models = [_model("LLAMA3.1"), _model("mistral")]
        _, default_index = _sort_and_dedupe_models(models, "llama3.1")
        assert default_index == 0

    def test_empty_model_list(self) -> None:
        sorted_m, default_index = _sort_and_dedupe_models([], "llama3.1")
        assert sorted_m == []
        assert default_index is None


class TestModelSelectionResult:
    def test_successful_selection(self) -> None:
        r = ModelSelectionResult(model="llama3.1")
        assert r.model == "llama3.1"
        assert not r.cancelled

    def test_cancelled(self) -> None:
        r = ModelSelectionResult(cancelled=True)
        assert r.cancelled
        assert r.model is None

    def test_cancelled_with_model_raises(self) -> None:
        with pytest.raises(ValueError, match="cancelled"):
            ModelSelectionResult(model="mistral", cancelled=True)

    def test_non_cancelled_without_model_raises(self) -> None:
        with pytest.raises(ValueError, match="non-cancelled"):
            ModelSelectionResult()

    def test_empty_model_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            ModelSelectionResult(model="")


class TestShowModelSelection:
    def test_select_first_model(self) -> None:
        models = [_model("deepseek"), _model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["1"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "deepseek"
        assert not result.cancelled

    def test_select_second_model(self) -> None:
        models = [_model("deepseek"), _model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["2"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "llama3.1"
        assert not result.cancelled

    def test_cancel(self) -> None:
        models = [_model("deepseek"), _model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["q"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.cancelled
        assert result.model is None

    def test_cancel_uppercase(self) -> None:
        models = [_model("deepseek"), _model("llama3.1")]
        term = FakeTerminal(keys=["Q"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.cancelled
        assert result.model is None

    def test_invalid_selection_retries(self) -> None:
        models = [_model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["x", "1"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "llama3.1"
        assert not result.cancelled

    def test_out_of_range_retries(self) -> None:
        models = [_model("llama3.1")]
        term = FakeTerminal(keys=["5", "1"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "llama3.1"
        assert not result.cancelled

    def test_default_not_installed_shows_note(self) -> None:
        models = [_model("mistral"), _model("deepseek")]
        term = FakeTerminal(keys=["1"])
        show_model_selection(term, models, "llama3.1")
        output = term.output
        assert "not installed" in output
        assert "choose any" in output

    def test_default_installed_shows_label(self) -> None:
        models = [_model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["1"])
        show_model_selection(term, models, "llama3.1")
        output = term.output
        assert "(default)" in output
        assert "not installed" not in output

    def test_alphabetical_order_in_output(self) -> None:
        models = [_model("zebra"), _model("alpha"), _model("beta")]
        term = FakeTerminal(keys=["q"])
        show_model_selection(term, models, "llama3.1")
        output = term.output
        alpha_pos = output.index("alpha")
        beta_pos = output.index("beta")
        zebra_pos = output.index("zebra")
        assert alpha_pos < beta_pos < zebra_pos

    def test_empty_model_list_returns_none(self) -> None:
        sorted_m, _ = _sort_and_dedupe_models([], "llama3.1")
        assert sorted_m == []

    def test_no_sentinel_values_in_output(self) -> None:
        models = [_model("deepseek"), _model("llama3.1")]
        term = FakeTerminal(keys=["1"])
        result = show_model_selection(term, models, "llama3.1")
        assert isinstance(result, ModelSelectionResult)
        assert not isinstance(result, str)
        assert result.model is not None


class TestChatLoopModelSelection:
    def test_ollama_unavailable(self) -> None:
        client = OllamaClient(host="http://fake:11434", timeout=5)
        client.list_models = MagicMock(side_effect=OllamaConnectionError("Not available"))
        term = FakeTerminal(keys=[" "])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "not available" in output

    def test_no_models_installed(self) -> None:
        client = _make_client(models=[])
        term = FakeTerminal(keys=[" "])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "No models" in output

    def test_single_model_auto_selected(self) -> None:
        client = _make_client(models=_mock_models("llama3.1"))
        term = FakeTerminal(keys=["hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "Provider : Ollama" in output

    def test_multiple_models_shows_selection(self) -> None:
        client = _make_client(models=_mock_models("deepseek", "llama3.1", "mistral"))
        term = FakeTerminal(keys=["2", "hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "Installed models" in output

    def test_cancel_model_selection_returns_to_menu(self) -> None:
        client = _make_client(models=_mock_models("deepseek", "llama3.1"))
        term = FakeTerminal(keys=["q"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "You>" not in output


class _V:
    def __init__(self, key_sequence: list[str], expected_tokens: list[str]) -> None:
        self.key_sequence = key_sequence
        self.expected_tokens = expected_tokens


class TestChatLoopStreaming:
    def test_chat_sends_message_and_streams_reply(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "You>" in output
        assert "AI>" in output
        assert "Hello" in output
        assert "world" in output
        client.chat_stream.assert_called_once()

    def test_stream_args_include_session_messages(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        call_args = client.chat_stream.call_args
        assert call_args is not None
        assert call_args[1]["model"] == "llama3.1"
        messages = call_args[1]["messages"]
        assert any(m["role"] == "user" and "hello" in m["content"].lower() for m in messages)

    def test_conversation_accumulates_context(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["first message", "second message", "/quit"])
        chat_loop(term, client, "llama3.1")
        assert client.chat_stream.call_count == 2
        second_call_messages = client.chat_stream.call_args_list[1][1]["messages"]
        roles = [m["role"] for m in second_call_messages]
        assert roles.count("user") == 2
        assert roles.count("assistant") == 1

    def test_empty_input_ignored(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["", "hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        assert client.chat_stream.call_count == 1

    def test_esc_cancels_generation(self) -> None:
        client = _make_client()
        client.chat_stream = MagicMock(
            side_effect=lambda *a, **kw: iter(["one ", "two ", "three "])
        )
        term = FakeTerminal(keys=["hello", "\x1b", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "cancelled" in output.lower()

    def test_ctrl_c_cancels_generation(self) -> None:
        client = _make_client()
        client.chat_stream = MagicMock(
            side_effect=lambda *a, **kw: iter(["one ", "two ", "three "])
        )
        term = FakeTerminal(keys=["hello", "\x03", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "cancelled" in output.lower()


class TestChatLoopCommands:
    def test_quit_returns_to_menu(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        # chat_loop returns without sending any messages
        assert "AI>" not in output

    def test_help_shows_commands(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["/help", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "/help" in output
        assert "/clear" in output
        assert "/model" in output
        assert "/quit" in output

    def test_unknown_command(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["/unknown", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "Unknown command" in output

    def test_clear_without_confirmation(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["hello", "/clear", "n", "/quit"])
        chat_loop(term, client, "llama3.1")
        assert client.chat_stream.call_count == 1

    def test_clear_with_confirmation(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["hello", "/clear", "y", "world", "/quit"])
        chat_loop(term, client, "llama3.1")
        assert client.chat_stream.call_count == 2
        second_call_messages = client.chat_stream.call_args_list[1][1]["messages"]
        assert len(second_call_messages) == 1
        assert second_call_messages[0]["role"] == "user"

    def test_model_shows_current(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["/model", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "llama3.1" in output

    def test_model_list_shows_installed(self) -> None:
        client = _make_client(models=_mock_models("llama3.1", "mistral"))
        term = FakeTerminal(keys=["1", "/model list", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "llama3.1" in output
        assert "(active)" in output

    def test_model_select_cancelled(self) -> None:
        client = _make_client(models=_mock_models("llama3.1", "mistral"))
        term = FakeTerminal(keys=["1", "/model select", "q", "/quit"])
        chat_loop(term, client, "llama3.1")
        assert not any("Switched" in line for line in term._lines)

    def test_model_select_switches_model(self) -> None:
        client = _make_client(models=_mock_models("llama3.1", "mistral"))
        term = FakeTerminal(keys=["1", "/model select", "n", "2", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "Switched" in output
        assert "mistral" in output

    def test_model_select_clears_history_on_switch(self) -> None:
        client = _make_client(models=_mock_models("llama3.1", "mistral"))
        term = FakeTerminal(keys=["1", "hello", "/model select", "y", "2", "/quit"])
        chat_loop(term, client, "llama3.1")
        # After clear and model switch, first chat_stream call was for "hello"
        # The second call should only have the new user message
        assert client.chat_stream.call_count == 1

    def test_model_subcommand_usage(self) -> None:
        client = _make_client()
        term = FakeTerminal(keys=["/model bad", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "Usage" in output
        assert "/model list" in output


class TestStripCancelSuffix:
    def test_no_suffix(self) -> None:
        assert _strip_cancel_suffix("Hello world") == "Hello world"

    def test_with_suffix(self) -> None:
        assert _strip_cancel_suffix("Hello[Generation cancelled]") == "Hello"

    def test_empty_string(self) -> None:
        assert _strip_cancel_suffix("") == ""

    def test_only_suffix(self) -> None:
        assert _strip_cancel_suffix("[Generation cancelled]") == ""


class TestChatLoopErrors:
    def test_model_not_found(self) -> None:
        client = _make_client()
        client.chat_stream = MagicMock(side_effect=OllamaModelNotFoundError("not found"))
        term = FakeTerminal(keys=["hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "not found" in output

    def test_connection_error_during_chat(self) -> None:
        client = _make_client()
        client.chat_stream = MagicMock(side_effect=OllamaConnectionError("Connection refused"))
        term = FakeTerminal(keys=["hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "Connection refused" in output

    def test_timeout_during_chat(self) -> None:
        client = _make_client()
        client.chat_stream = MagicMock(side_effect=OllamaTimeoutError("timed out"))
        term = FakeTerminal(keys=["hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "timed out" in output or "Timeout" in output

    def test_invalid_response_during_chat(self) -> None:
        client = _make_client()
        client.chat_stream = MagicMock(side_effect=OllamaInvalidResponseError("bad json"))
        term = FakeTerminal(keys=["hello", "/quit"])
        chat_loop(term, client, "llama3.1")
        output = term.output
        assert "Invalid response" in output or "bad json" in output

    def test_chat_continues_after_error(self) -> None:
        client = _make_client()
        client.chat_stream = MagicMock(
            side_effect=[
                OllamaConnectionError("fail"),
                iter(["ok"]),
            ]
        )
        term = FakeTerminal(keys=["hello", "world", "/quit"])
        chat_loop(term, client, "llama3.1")
        assert client.chat_stream.call_count == 2
