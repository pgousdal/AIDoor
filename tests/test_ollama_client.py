from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from aidoor.ollama.client import OllamaClient
from aidoor.ollama.errors import (
    OllamaConnectionError,
    OllamaInvalidResponseError,
    OllamaModelNotFoundError,
)
from aidoor.providers.models import ModelInfo


def _mock_response(data: object, status: int = 200) -> MagicMock:
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = body
    resp.status = status
    resp.getcode.return_value = status
    return resp


def _mock_stream_response(chunks: list[dict]) -> MagicMock:
    lines = [json.dumps(c).encode("utf-8") + b"\n" for c in chunks]
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.__iter__.return_value = iter(lines)
    resp.status = 200
    return resp


class TestHealth:
    def test_healthy(self) -> None:
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=_mock_response({"version": "0.1.0"})):
            assert client.health()

    def test_unhealthy(self) -> None:
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            assert not client.health()

    def test_invalid_json(self) -> None:
        client = OllamaClient()
        resp = MagicMock()
        resp.__enter__.return_value = resp
        resp.read.return_value = b"not json"
        with patch("urllib.request.urlopen", return_value=resp):
            assert not client.health()


class TestListModels:
    def test_returns_models(self) -> None:
        data = {
            "models": [
                {"name": "llama3.1", "modified_at": "2024-01-01", "size": 1000},
                {"name": "mistral", "modified_at": "2024-02-01", "size": 2000},
            ]
        }
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=_mock_response(data)):
            models = client.list_models()
            assert len(models) == 2
            assert models[0].name == "llama3.1"
            assert models[1].name == "mistral"

    def test_empty_response(self) -> None:
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=_mock_response({"models": []})):
            models = client.list_models()
            assert models == []

    def test_connection_error(self) -> None:
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            with pytest.raises(OllamaConnectionError, match="Cannot connect"):
                client.list_models()

    def test_timeout(self) -> None:
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError):
            with pytest.raises(OllamaConnectionError, match="Cannot connect"):
                client.list_models()

    def test_invalid_json(self) -> None:
        resp = MagicMock()
        resp.__enter__.return_value = resp
        resp.read.return_value = b"bad json"
        resp.status = 200
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=resp):
            with pytest.raises(OllamaInvalidResponseError, match="Invalid response"):
                client.list_models()

    def test_404_returns_empty(self) -> None:
        from urllib.error import HTTPError

        exc = HTTPError("http://localhost/api/tags", 404, "Not Found", {}, None)
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=exc):
            models = client.list_models()
            assert models == []

    def test_model_info_fields(self) -> None:
        data = {"models": [{"name": "test-model", "modified_at": "2024-01-01", "size": 500}]}
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=_mock_response(data)):
            models = client.list_models()
            m = models[0]
            assert isinstance(m, ModelInfo)
            assert m.name == "test-model"
            assert m.modified_at == "2024-01-01"
            assert m.size == 500


class TestChatStream:
    def test_streams_tokens(self) -> None:
        chunks = [
            {"model": "llama3.1", "message": {"role": "assistant", "content": "Hello"},
             "done": False},
            {"model": "llama3.1", "message": {"role": "assistant", "content": " world"},
             "done": False},
            {"model": "llama3.1", "message": {"role": "assistant", "content": ""},
             "done": True},
        ]
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=_mock_stream_response(chunks)):
            tokens = list(client.chat_stream("llama3.1", []))
            assert tokens == ["Hello", " world"]

    def test_empty_stream(self) -> None:
        chunks = [
            {"model": "llama3.1", "message": {"role": "assistant", "content": ""}, "done": True},
        ]
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=_mock_stream_response(chunks)):
            tokens = list(client.chat_stream("llama3.1", []))
            assert tokens == []

    def test_connection_error(self) -> None:
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            with pytest.raises(OllamaConnectionError, match="Cannot connect"):
                list(client.chat_stream("llama3.1", []))

    def test_timeout(self) -> None:
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError):
            with pytest.raises(OllamaConnectionError, match="Cannot connect"):
                list(client.chat_stream("llama3.1", []))

    def test_unknown_model_404(self) -> None:
        from urllib.error import HTTPError

        exc = HTTPError("http://localhost/api/chat", 404, "Not Found", {}, None)
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(OllamaModelNotFoundError, match="not found"):
                list(client.chat_stream("nonexistent", []))

    def test_server_error(self) -> None:
        from urllib.error import HTTPError

        body = json.dumps({"error": "internal error"}).encode("utf-8")
        exc = HTTPError("http://localhost/api/chat", 500, "Internal Error", {}, MagicMock())
        exc.read = MagicMock(return_value=body)
        client = OllamaClient()
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(OllamaConnectionError, match="500"):
                list(client.chat_stream("llama3.1", []))

    def test_stream_json_error(self) -> None:
        resp = MagicMock()
        resp.__enter__.return_value = resp
        resp.__iter__.return_value = iter([b"not json\n"])
        resp.status = 200
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=resp):
            with pytest.raises(OllamaInvalidResponseError, match="Failed to parse"):
                list(client.chat_stream("llama3.1", []))

    def test_stream_ollama_error_field(self) -> None:
        chunks = [
            {"error": "model not found"},
        ]
        client = OllamaClient()
        with patch("urllib.request.urlopen", return_value=_mock_stream_response(chunks)):
            with pytest.raises(OllamaConnectionError, match="model not found"):
                list(client.chat_stream("llama3.1", []))

    def test_sends_messages_and_model(self) -> None:
        client = OllamaClient()
        chunks = [
            {"model": "mistral", "message": {"role": "assistant", "content": "ok"}, "done": False},
            {"model": "mistral", "message": {"role": "assistant", "content": ""}, "done": True},
        ]
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _mock_stream_response(chunks)
            list(client.chat_stream("mistral", [{"role": "user", "content": "hi"}]))
            req = mock_urlopen.call_args[0][0]
            body = json.loads(req.data)
            assert body["model"] == "mistral"
            assert body["messages"] == [{"role": "user", "content": "hi"}]
            assert body["stream"] is True
