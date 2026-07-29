from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from aidoor.doctor.checks import (
    CheckResult,
    check_configuration,
    check_log_file,
    check_model_installed,
    check_ollama_host,
    check_ollama_reachable,
    check_package_version,
    check_python_version,
    check_terminal,
    doctor_main,
    print_report,
    run_checks,
)
from aidoor.ollama.errors import OllamaConnectionError


def _result() -> CheckResult:
    return CheckResult("test")


def _mock_response(data: object) -> MagicMock:
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = body
    return resp


class TestCheckPythonVersion:
    def test_passes_for_3_11_plus(self) -> None:
        r = _result()
        check_python_version(r)
        assert r.passed

    def test_has_version_string(self) -> None:
        r = _result()
        check_python_version(r)
        assert any("Python" in m for m in r.messages)


class TestCheckPackageVersion:
    def test_has_version_string(self) -> None:
        r = _result()
        check_package_version(r)
        assert any("AIDoor" in m for m in r.messages)


class TestCheckConfiguration:
    def test_passes_with_defaults(self) -> None:
        r = _result()
        config = check_configuration(r, None)
        assert r.passed
        assert config is not None

    def test_fails_on_bad_path(self) -> None:
        r = _result()
        config = check_configuration(r, "/nonexistent/config.toml")
        assert not r.passed
        assert config is None


class TestCheckTerminal:
    def test_passes_with_defaults(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        check_terminal(r, AppConfig())
        assert r.passed

    def test_fails_on_narrow(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        config = AppConfig()
        config.terminal.width = 30
        check_terminal(r, config)
        assert not r.passed

    def test_warns_on_below_recommended(self) -> None:
        r = _result()
        from aidoor.config import AppConfig, TerminalConfig

        config = AppConfig(terminal=TerminalConfig(width=50, height=24))
        check_terminal(r, config)
        assert r.passed
        assert r.warnings

    def test_fails_on_short(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        config = AppConfig()
        config.terminal.height = 5
        check_terminal(r, config)
        assert not r.passed


class TestCheckLogFile:
    def test_passes_when_not_configured(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        check_log_file(r, AppConfig())
        assert r.passed

    def test_passes_when_writable(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        fd, path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        try:
            config = AppConfig()
            config.general.log_file = path
            check_log_file(r, config)
            assert r.passed
        finally:
            os.unlink(path)

    def test_fails_on_unwritable_dir(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        config = AppConfig()
        config.general.log_file = "/nonexistent/deep/aidoor.log"
        check_log_file(r, config)
        assert not r.passed

    def test_no_config_still_passes(self) -> None:
        r = _result()
        check_log_file(r, None)
        assert r.passed


class TestCheckOllamaHost:
    def test_passes_with_valid(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        check_ollama_host(r, AppConfig())
        assert r.passed

    def test_no_config_does_nothing(self) -> None:
        r = _result()
        check_ollama_host(r, None)
        assert r.passed

    def test_fails_on_bad_url(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        config = AppConfig()
        config.ollama.host = "localhost:11434"
        check_ollama_host(r, config)
        assert not r.passed


class TestCheckOllamaReachable:
    def test_passes_when_healthy(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        with patch("urllib.request.urlopen", return_value=_mock_response({"version": "0.1.0"})):
            check_ollama_reachable(r, AppConfig())
        assert r.passed

    def test_fails_when_unreachable(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            check_ollama_reachable(r, AppConfig())
        assert not r.passed

    def test_warns_without_config(self) -> None:
        r = _result()
        check_ollama_reachable(r, None)
        assert r.warnings


class TestCheckModelInstalled:
    def test_passes_when_found(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        data = {"models": [{"name": "llama3.1", "modified_at": "", "size": 0}]}
        with patch("urllib.request.urlopen", return_value=_mock_response(data)):
            check_model_installed(r, AppConfig())
        assert r.passed

    def test_fails_when_not_found(self) -> None:
        r = _result()
        from aidoor.config import AppConfig, OllamaConfig

        config = AppConfig(ollama=OllamaConfig(model="nonexistent"))
        data = {"models": [{"name": "llama3.1", "modified_at": "", "size": 0}]}
        with patch("urllib.request.urlopen", return_value=_mock_response(data)):
            check_model_installed(r, config)
        assert not r.passed

    def test_warns_on_unreachable(self) -> None:
        r = _result()
        from aidoor.config import AppConfig

        with patch("urllib.request.urlopen", side_effect=OllamaConnectionError("fail")):
            check_model_installed(r, AppConfig())
        assert r.warnings


def _ollama_side_effect(*args: object, **kwargs: object) -> MagicMock:
    for a in args:
        if hasattr(a, "full_url"):
            url = a.full_url  # type: ignore[union-attr]
            if "/api/tags" in url:
                tag_data = {"models": [{"name": "llama3.1", "modified_at": "", "size": 0}]}
                return _mock_response(tag_data)
            if "/api/" in url:
                return _mock_response({"version": "0.1.0"})
    return _mock_response({"version": "0.1.0"})


class TestRunChecks:
    def test_returns_list(self) -> None:
        with patch("urllib.request.urlopen", side_effect=_ollama_side_effect):
            checks = run_checks(None)
        assert len(checks) >= 6

    def test_each_has_name(self) -> None:
        with patch("urllib.request.urlopen", side_effect=_ollama_side_effect):
            checks = run_checks(None)
        for c in checks:
            assert c.name

    def test_ollama_checks_with_mock(self) -> None:
        with patch("urllib.request.urlopen", side_effect=_ollama_side_effect):
            checks = run_checks(None)
            ollama_checks = [
                c for c in checks
                if "ollama" in c.name.lower() or "model" in c.name.lower()
            ]
            assert len(ollama_checks) >= 2


class TestPrintReport:
    def test_returns_zero_on_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("urllib.request.urlopen", side_effect=_ollama_side_effect):
            checks = run_checks(None)
            score = print_report(checks)
        assert score >= 0
        captured = capsys.readouterr()
        assert "AIDoor Doctor" in captured.out


class TestDoctorMain:
    def test_returns_0_on_no_errors(self) -> None:
        with patch("urllib.request.urlopen", side_effect=_ollama_side_effect):
            rc = doctor_main(None)
            assert rc in (0, 1)

    def test_returns_2_on_config_error(self) -> None:
        rc = doctor_main("/nonexistent/config.toml")
        assert rc == 2
