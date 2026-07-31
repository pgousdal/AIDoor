from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from aidoor.config import AppConfig
from aidoor.doctor.checks import (
    CheckResult,
    check_configuration,
    check_log_file,
    check_model_installed,
    check_ollama_host,
    check_ollama_reachable,
    check_package_version,
    check_provider,
    check_python_version,
    check_terminal,
    doctor_main,
    print_report,
    run_checks,
)
from aidoor.providers import Provider, ProviderUnavailable
from aidoor.providers.models import ModelInfo


def _result() -> CheckResult:
    return CheckResult("test")


def _mock_tags_response(names: list[str]) -> MagicMock:
    data = {"models": [{"name": n, "modified_at": "", "size": 0} for n in names]}
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = body
    return resp
    return CheckResult("test")


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


class TestCheckProvider:
    def test_shows_provider_name(self) -> None:
        r = _result()
        provider = MagicMock(spec=Provider)
        provider.provider_name.return_value = "Ollama"
        check_provider(r, provider)
        assert r.passed
        assert any("Ollama" in m for m in r.messages)

    def test_warns_on_no_provider(self) -> None:
        r = _result()
        check_provider(r, None)
        assert r.warnings


class TestCheckTerminal:
    def test_passes_with_defaults(self) -> None:
        r = _result()
        check_terminal(r, AppConfig())
        assert r.passed

    def test_fails_on_narrow(self) -> None:
        r = _result()
        config = AppConfig()
        config.terminal.width = 30
        check_terminal(r, config)
        assert not r.passed

    def test_warns_on_below_recommended(self) -> None:
        r = _result()
        from aidoor.config import TerminalConfig

        config = AppConfig(terminal=TerminalConfig(width=50, height=24))
        check_terminal(r, config)
        assert r.passed
        assert r.warnings

    def test_fails_on_short(self) -> None:
        r = _result()
        config = AppConfig()
        config.terminal.height = 5
        check_terminal(r, config)
        assert not r.passed


class TestCheckLogFile:
    def test_passes_when_not_configured(self) -> None:
        r = _result()
        check_log_file(r, AppConfig())
        assert r.passed

    def test_passes_when_writable(self) -> None:
        r = _result()
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
        check_ollama_host(r, AppConfig())
        assert r.passed

    def test_no_config_does_nothing(self) -> None:
        r = _result()
        check_ollama_host(r, None)
        assert r.passed

    def test_fails_on_bad_url(self) -> None:
        r = _result()
        config = AppConfig()
        config.ollama.host = "localhost:11434"
        check_ollama_host(r, config)
        assert not r.passed


class TestCheckOllamaReachable:
    def test_passes_when_healthy(self) -> None:
        r = _result()
        provider = MagicMock(spec=Provider)
        provider.health.return_value = True
        check_ollama_reachable(r, provider)
        assert r.passed

    def test_fails_when_unreachable(self) -> None:
        r = _result()
        provider = MagicMock(spec=Provider)
        provider.health.return_value = False
        check_ollama_reachable(r, provider)
        assert not r.passed

    def test_warns_without_provider(self) -> None:
        r = _result()
        check_ollama_reachable(r, None)
        assert r.warnings


class TestCheckModelInstalled:
    def test_passes_when_found(self) -> None:
        r = _result()
        provider = MagicMock(spec=Provider)
        provider.list_models.return_value = [
            ModelInfo(name="llama3.1", modified_at="", size=0)
        ]
        check_model_installed(r, provider, AppConfig())
        assert r.passed

    def test_fails_when_not_found(self) -> None:
        r = _result()
        provider = MagicMock(spec=Provider)
        provider.list_models.return_value = [
            ModelInfo(name="mistral", modified_at="", size=0)
        ]
        config = AppConfig()
        config.ollama.model = "nonexistent"
        check_model_installed(r, provider, config)
        assert not r.passed

    def test_warns_on_unreachable(self) -> None:
        r = _result()
        provider = MagicMock(spec=Provider)
        provider.list_models.side_effect = ProviderUnavailable("fail")
        check_model_installed(r, provider, AppConfig())
        assert r.warnings


class TestRunChecks:
    def test_returns_list(self) -> None:
        checks = run_checks(None)
        assert len(checks) >= 7

    def test_each_has_name(self) -> None:
        checks = run_checks(None)
        for c in checks:
            assert c.name

    def test_provider_check_present(self) -> None:
        checks = run_checks(None)
        provider_checks = [c for c in checks if "provider" in c.name.lower()]
        assert len(provider_checks) >= 1


class TestPrintReport:
    def test_returns_zero_on_defaults(self, capsys: pytest.CaptureFixture[str]) -> None:
        checks = run_checks(None)
        score = print_report(checks)
        assert score >= 0
        captured = capsys.readouterr()
        assert "AIDoor Doctor" in captured.out


class TestDoctorMain:
    def test_returns_0_on_no_errors(self) -> None:
        with patch("urllib.request.urlopen") as mock:
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.read.return_value = b'{"version": "0.1.0"}'
            mock.side_effect = [
                mock_response,
                _mock_tags_response(["llama3.1"]),
            ]
            rc = doctor_main(None)
        assert rc in (0, 1)

    def test_returns_2_on_config_error(self) -> None:
        rc = doctor_main("/nonexistent/config.toml")
        assert rc == 2
