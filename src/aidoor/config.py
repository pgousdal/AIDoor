from __future__ import annotations

import dataclasses
import tomllib
from pathlib import Path
from typing import Any

from aidoor.errors import ConfigurationError

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclasses.dataclass
class GeneralConfig:
    log_level: str = "INFO"
    log_file: str = ""
    ansi: bool = True
    utf8: bool = True
    pause_on_exit: bool = False
    charset: str = "unicode"

    VALID_CHARSETS = {"unicode", "cp437"}

    def __post_init__(self) -> None:
        if self.log_level.upper() not in VALID_LOG_LEVELS:
            raise ConfigurationError(
                f"Invalid log_level: {self.log_level!r}. "
                f"Must be one of {', '.join(sorted(VALID_LOG_LEVELS))}"
            )
        if self.charset.lower() not in self.VALID_CHARSETS:
            raise ConfigurationError(
                f"Invalid charset: {self.charset!r}. "
                f"Must be one of {', '.join(sorted(self.VALID_CHARSETS))}"
            )


@dataclasses.dataclass
class TerminalConfig:
    width: int = 80
    height: int = 24
    more_prompt: bool = True

    def __post_init__(self) -> None:
        if self.width < 40 or self.width > 999:
            raise ConfigurationError(
                f"Invalid terminal width: {self.width}. Must be between 40 and 999."
            )
        if self.height < 10 or self.height > 200:
            raise ConfigurationError(
                f"Invalid terminal height: {self.height}. Must be between 10 and 200."
            )


@dataclasses.dataclass
class OllamaConfig:
    enabled: bool = True
    host: str = "http://localhost:11434"
    model: str = "llama3.1"
    timeout: int = 120

    def __post_init__(self) -> None:
        if self.timeout < 1 or self.timeout > 600:
            raise ConfigurationError(
                f"Invalid ollama timeout: {self.timeout}. Must be between 1 and 600."
            )
        if not self.host.startswith("http://") and not self.host.startswith("https://"):
            raise ConfigurationError(
                f"Invalid ollama host: {self.host!r}. Must start with http:// or https://."
            )
        if not self.model.strip():
            raise ConfigurationError("ollama model must not be empty")


@dataclasses.dataclass
class ProviderConfig:
    type: str = "ollama"

    def __post_init__(self) -> None:
        valid = {"ollama"}
        if self.type.lower() not in valid:
            raise ConfigurationError(
                f"Invalid provider type: {self.type!r}. "
                f"Must be one of {', '.join(sorted(valid))}"
            )


@dataclasses.dataclass
class AppConfig:
    general: GeneralConfig = dataclasses.field(default_factory=GeneralConfig)
    terminal: TerminalConfig = dataclasses.field(default_factory=TerminalConfig)
    provider: ProviderConfig = dataclasses.field(default_factory=ProviderConfig)
    ollama: OllamaConfig = dataclasses.field(default_factory=OllamaConfig)


def parse_config(config_path: str | None) -> AppConfig:
    if config_path is None:
        return AppConfig()

    path = Path(config_path)
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        raw = path.read_bytes()
        data: dict[str, Any] = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigurationError(f"Invalid configuration file: {exc}") from exc

    general_raw = _filter_known(data.get("general", {}), GeneralConfig)
    terminal_raw = _filter_known(data.get("terminal", {}), TerminalConfig)
    provider_raw = _filter_known(data.get("provider", {}), ProviderConfig)
    ollama_raw = _filter_known(data.get("ollama", {}), OllamaConfig)

    return AppConfig(
        general=GeneralConfig(**general_raw),
        terminal=TerminalConfig(**terminal_raw),
        provider=ProviderConfig(**provider_raw),
        ollama=OllamaConfig(**ollama_raw),
    )


def _filter_known(raw: dict[str, Any], cls: type) -> dict[str, Any]:
    valid = {f.name for f in dataclasses.fields(cls)}
    return {k: v for k, v in raw.items() if k in valid}
