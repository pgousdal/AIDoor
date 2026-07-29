from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from aidoor.cli import main


def _mock_response(data: object) -> MagicMock:
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = body
    return resp


def _side_effect(*args: object, **kwargs: object) -> MagicMock:
    for a in args:
        if hasattr(a, "full_url"):
            url = a.full_url  # type: ignore[union-attr]
            if "/api/tags" in url:
                data = {"models": [{"name": "llama3.1", "modified_at": "", "size": 0}]}
                return _mock_response(data)
            if "/api/" in url:
                return _mock_response({"version": "0.1.0"})
    return _mock_response({"version": "0.1.0"})


class TestCliArgumentParsing:
    def test_version(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0

    def test_help(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_no_args_shows_help(self) -> None:
        result = main([])
        assert result == 1

    def test_door32_missing_file_returns_1(self) -> None:
        result = main(["--door32", "/nonexistent/door32.sys"])
        assert result == 1

    def test_invalid_door32_file_returns_1(self) -> None:
        content = "3\n0\n9600\nTest\n1\nUser\nAlias\n50\n300\nANSI\n1\n"
        fd, path = tempfile.mkstemp(suffix=".sys")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            result = main(["--door32", path])
            assert result == 1
        finally:
            os.unlink(path)

    def test_config_not_found_returns_1(self) -> None:
        result = main(["--local", "--config", "/nonexistent/config.toml"])
        assert result == 1

    def test_run_subcommand_with_local(self) -> None:
        result = main(["run", "--local"])
        assert result != 0

    def test_doctor_subcommand(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", side_effect=_side_effect):
            result = main(["doctor"])
        assert result in (0, 1)

    def test_models_subcommand(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", return_value=_mock_response(
            {"models": [{"name": "llama3.1", "modified_at": "", "size": 0}]}
        )):
            result = main(["models"])
        assert result == 0

    def test_version_subcommand(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["version"])
        assert result == 0
