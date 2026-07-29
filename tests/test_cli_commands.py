from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from aidoor.cli import _cmd_models, _cmd_version, main


def _mock_response(data: object) -> MagicMock:
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = body
    return resp


def _ollama_side(*args: object, **kwargs: object) -> MagicMock:
    for a in args:
        if hasattr(a, "full_url"):
            url = a.full_url  # type: ignore[union-attr]
            if "/api/tags" in url:
                data = {"models": [{"name": "llama3.1", "modified_at": "", "size": 0}]}
                return _mock_response(data)
            if "/api/" in url:
                return _mock_response({"version": "0.1.0"})
    return _mock_response({"version": "0.1.0"})


class TestVersionSubcommand:
    def test_version_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", return_value=_mock_response({"version": "0.1.0"})):
            rc = _cmd_version(None)
        assert rc == 0
        captured = capsys.readouterr()
        assert "AIDoor version" in captured.out

    def test_version_command_no_ollama(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            rc = _cmd_version(None)
        assert rc == 0
        captured = capsys.readouterr()
        assert "unavailable" in captured.out

    def test_version_via_cli(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["version"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "AIDoor version" in captured.out


class TestModelsSubcommand:
    def test_models_lists_installed(self, capsys: pytest.CaptureFixture[str]) -> None:
        data = {
            "models": [
                {"name": "llama3.1", "modified_at": "", "size": 0},
                {"name": "mistral", "modified_at": "", "size": 0},
            ]
        }
        with patch("urllib.request.urlopen", return_value=_mock_response(data)):
            rc = _cmd_models(None)
        assert rc == 0
        captured = capsys.readouterr()
        assert "llama3.1" in captured.out
        assert "mistral" in captured.out

    def test_models_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", return_value=_mock_response({"models": []})):
            rc = _cmd_models(None)
        assert rc == 0
        captured = capsys.readouterr()
        assert "(none)" in captured.out

    def test_models_connection_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            rc = _cmd_models(None)
        assert rc == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_models_via_cli(self, capsys: pytest.CaptureFixture[str]) -> None:
        data = {"models": [{"name": "llama3.1", "modified_at": "", "size": 0}]}
        with patch("urllib.request.urlopen", return_value=_mock_response(data)):
            rc = main(["models"])
        assert rc == 0


class TestDoctorSubcommand:
    def test_doctor_via_cli(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", side_effect=_ollama_side):
            rc = main(["doctor"])
        assert rc in (0, 1)
        captured = capsys.readouterr()
        assert "AIDoor Doctor" in captured.out

    def test_doctor_with_config_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        content = """
[general]
log_level = "INFO"

[ollama]
host = "http://localhost:11434"
model = "llama3.1"
timeout = 120
"""
        fd, path = tempfile.mkstemp(suffix=".toml")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            with patch("urllib.request.urlopen", side_effect=_ollama_side):
                rc = main(["doctor", "--config", path])
            assert rc in (0, 1)
        finally:
            os.unlink(path)

    def test_doctor_with_bad_config(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["doctor", "--config", "/nonexistent/config.toml"])
        assert rc == 2
        captured = capsys.readouterr()
        assert "Error" in captured.out or "fail" in captured.out.lower()


class TestRunSubcommand:
    def test_run_requires_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["run"])
        assert rc == 1

    def test_run_local_with_config(self, capsys: pytest.CaptureFixture[str]) -> None:
        content = """
[general]
log_level = "INFO"
"""
        fd, path = tempfile.mkstemp(suffix=".toml")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            rc = main(["run", "--local", "--config", path])
            assert rc != 0
        finally:
            os.unlink(path)


class TestHelp:
    def test_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([])
        assert rc == 1
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0
