from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator

from aidoor.ollama.errors import (
    OllamaConnectionError,
    OllamaInvalidResponseError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from aidoor.ollama.models import ModelInfo


class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434", timeout: int = 120) -> None:
        self._host = host.rstrip("/")
        self._timeout = timeout

    def health(self) -> bool:
        try:
            req = urllib.request.Request(f"{self._host}/api/version", method="GET")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return "version" in data
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError, OSError):
            return False

    def list_models(self) -> list[ModelInfo]:
        try:
            req = urllib.request.Request(f"{self._host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return []
            raise OllamaConnectionError(f"Ollama returned HTTP {exc.code}") from exc
        except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._host}"
            ) from exc
        except (json.JSONDecodeError, OSError) as exc:
            raise OllamaInvalidResponseError("Invalid response from Ollama") from exc

        models: list[ModelInfo] = []
        for m in data.get("models", []):
            models.append(
                ModelInfo(
                    name=m.get("name", "unknown"),
                    modified_at=m.get("modified_at", ""),
                    size=m.get("size", 0),
                )
            )
        return models

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> Iterator[str]:
        body = json.dumps({"model": model, "messages": messages, "stream": True}).encode(
            "utf-8"
        )
        req = urllib.request.Request(
            f"{self._host}/api/chat",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            resp = urllib.request.urlopen(req, timeout=self._timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model}' not found on server"
                ) from exc
            body_raw = exc.read().decode("utf-8", errors="replace")
            try:
                err_data = json.loads(body_raw)
                err_msg = err_data.get("error", body_raw)
            except json.JSONDecodeError:
                err_msg = body_raw
            raise OllamaConnectionError(f"Ollama returned HTTP {exc.code}: {err_msg}") from exc
        except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._host}"
            ) from exc
        except OSError as exc:
            raise OllamaConnectionError(f"Connection error: {exc}") from exc

        try:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise OllamaInvalidResponseError(
                        "Failed to parse streaming response"
                    ) from exc

                if "error" in chunk:
                    raise OllamaConnectionError(
                        f"Ollama error: {chunk['error']}"
                    )

                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token

                if chunk.get("done"):
                    return
        except urllib.error.URLError as exc:
            raise OllamaConnectionError(f"Connection lost during streaming: {exc}") from exc
        except TimeoutError as exc:
            raise OllamaTimeoutError("Stream timed out") from exc
