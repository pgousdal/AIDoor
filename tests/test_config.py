from __future__ import annotations

import os
import tempfile

import pytest

from aidoor.config import AppConfig, GeneralConfig, OllamaConfig, TerminalConfig, parse_config
from aidoor.errors import ConfigurationError


class TestDefaultConfig:
    def test_default_values(self) -> None:
        config = AppConfig()
        assert config.general.log_level == "INFO"
        assert config.general.log_file == ""
        assert config.general.ansi
        assert config.terminal.width == 80
        assert config.terminal.height == 24
        assert config.terminal.more_prompt

    def test_parse_config_without_file(self) -> None:
        config = parse_config(None)
        assert config.general.log_level == "INFO"


class TestGeneralConfig:
    def test_valid_log_levels(self) -> None:
        for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            gc = GeneralConfig(log_level=level)
            assert gc.log_level == level

    def test_invalid_log_level(self) -> None:
        with pytest.raises(ConfigurationError, match="Invalid log_level"):
            GeneralConfig(log_level="TRACE")

    def test_case_insensitive_log_level(self) -> None:
        gc = GeneralConfig(log_level="info")
        assert gc.log_level == "info"

    def test_invalid_charset(self) -> None:
        with pytest.raises(ConfigurationError, match="Invalid charset"):
            GeneralConfig(charset="utf8")


class TestTerminalConfig:
    def test_valid_sizes(self) -> None:
        tc = TerminalConfig(width=80, height=25)
        assert tc.width == 80
        assert tc.height == 25

    def test_width_too_small(self) -> None:
        with pytest.raises(ConfigurationError, match="width"):
            TerminalConfig(width=30, height=24)

    def test_width_too_large(self) -> None:
        with pytest.raises(ConfigurationError, match="width"):
            TerminalConfig(width=1000, height=24)

    def test_height_too_small(self) -> None:
        with pytest.raises(ConfigurationError, match="height"):
            TerminalConfig(width=80, height=5)

    def test_height_too_large(self) -> None:
        with pytest.raises(ConfigurationError, match="height"):
            TerminalConfig(width=80, height=300)


class TestOllamaConfig:
    def test_default_values(self) -> None:
        oc = OllamaConfig()
        assert oc.enabled
        assert oc.host == "http://localhost:11434"
        assert oc.model == "llama3.1"
        assert oc.timeout == 120

    def test_invalid_timeout(self) -> None:
        with pytest.raises(ConfigurationError, match="timeout"):
            OllamaConfig(timeout=0)

    def test_invalid_host(self) -> None:
        with pytest.raises(ConfigurationError, match="host"):
            OllamaConfig(host="localhost:11434")

    def test_empty_model(self) -> None:
        with pytest.raises(ConfigurationError, match="model"):
            OllamaConfig(model="")


class TestParseConfig:
    def test_valid_toml(self) -> None:
        content = """
[general]
log_level = "DEBUG"
log_file = "/tmp/aidoor.log"
ansi = false

[terminal]
width = 100
height = 30
more_prompt = false

[ollama]
host = "http://ollama:11434"
model = "mistral"
timeout = 60
"""
        fd, path = tempfile.mkstemp(suffix=".toml")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            config = parse_config(path)
            assert config.general.log_level == "DEBUG"
            assert config.general.log_file == "/tmp/aidoor.log"
            assert not config.general.ansi
            assert config.terminal.width == 100
            assert config.terminal.height == 30
            assert not config.terminal.more_prompt
            assert config.ollama.host == "http://ollama:11434"
            assert config.ollama.model == "mistral"
            assert config.ollama.timeout == 60
        finally:
            os.unlink(path)

    def test_missing_explicit_file(self) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            parse_config("/nonexistent/aidoor.toml")

    def test_invalid_toml(self) -> None:
        content = "this is not toml = {{{"
        fd, path = tempfile.mkstemp(suffix=".toml")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            with pytest.raises(ConfigurationError, match="Invalid"):
                parse_config(path)
        finally:
            os.unlink(path)

    def test_unknown_keys_ignored(self) -> None:
        content = """
[general]
log_level = "INFO"
unknown_key = "value"

[terminal]
width = 80
height = 24

[ollama]
enabled = true
host = "http://localhost:11434"
model = "llama3.1"
timeout = 120

[unknown_section]
foo = "bar"
"""
        fd, path = tempfile.mkstemp(suffix=".toml")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            config = parse_config(path)
            assert config.general.log_level == "INFO"
        finally:
            os.unlink(path)
