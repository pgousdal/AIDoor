from __future__ import annotations

import os
import sys
from pathlib import Path

from aidoor.config import AppConfig, parse_config
from aidoor.providers import (
    Provider,
    ProviderError,
    ProviderUnavailable,
    create_provider,
)
from aidoor.version import __version__


class CheckResult:
    def __init__(self, name: str) -> None:
        self.name = name
        self.passed: bool = True
        self.messages: list[str] = []
        self.warnings: list[str] = []

    def fail(self, msg: str) -> None:
        self.passed = False
        self.messages.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return self.passed and not self.warnings

    @property
    def has_warnings(self) -> bool:
        return not self.passed or bool(self.warnings)


def check_python_version(result: CheckResult) -> None:
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 11):
        result.fail(f"Python 3.11+ required, found {v.major}.{v.minor}.{v.micro}")
    else:
        result.messages.append(f"Python {v.major}.{v.minor}.{v.micro}")


def check_package_version(result: CheckResult) -> None:
    result.messages.append(f"AIDoor {__version__}")


def check_configuration(result: CheckResult, config_path: str | None) -> AppConfig | None:
    try:
        config = parse_config(config_path)
        source = config_path or "defaults"
        result.messages.append(f"Configuration loaded ({source})")
        if config_path:
            path = Path(config_path)
            if not os.access(str(path), os.R_OK):
                result.warn(f"Configuration file not readable: {config_path}")
        return config
    except Exception as exc:
        result.fail(f"Configuration error: {exc}")
        return None


def check_terminal(result: CheckResult, config: AppConfig | None) -> None:
    width = config.terminal.width if config else 80
    height = config.terminal.height if config else 24
    if width < 40:
        result.fail(f"Terminal width {width} below minimum 40")
    elif width < 60:
        result.warn(f"Terminal width {width} below recommended 60")
    else:
        result.messages.append(f"Terminal width {width}")
    if height < 10:
        result.fail(f"Terminal height {height} below minimum 10")
    else:
        result.messages.append(f"Terminal height {height}")


def check_log_file(result: CheckResult, config: AppConfig | None) -> None:
    if config is None or not config.general.log_file:
        result.messages.append("No log file configured (logging to stderr)")
        return
    log_path = Path(config.general.log_file)
    try:
        if log_path.exists():
            if not os.access(str(log_path), os.W_OK):
                result.fail(f"Log file not writable: {log_path}")
            else:
                result.messages.append(f"Log file writable: {log_path}")
        else:
            parent = log_path.parent
            if parent.exists() and os.access(str(parent), os.W_OK):
                result.messages.append(f"Log file creatable: {log_path}")
            else:
                result.fail(f"Log directory not writable: {parent}")
    except OSError as exc:
        result.fail(f"Log file check failed: {exc}")


def check_provider(result: CheckResult, provider: Provider | None) -> None:
    if provider is None:
        result.warn("Cannot check provider — none configured")
        return
    name = provider.provider_name()
    result.messages.append(f"Provider: {name}")


def check_ollama_reachable(result: CheckResult, provider: Provider | None) -> None:
    if provider is None:
        result.warn("Cannot check Ollama without configuration")
        return
    try:
        ok = provider.health()
    except Exception:
        ok = False
    if ok:
        host = getattr(provider, "_client", None)
        host_str = getattr(host, "_host", "unknown") if host else "unknown"
        result.messages.append(f"Ollama reachable at {host_str}")
    else:
        result.messages.append("Ollama not reachable")
        result.fail("Cannot connect to Ollama")


def check_model_installed(
    result: CheckResult, provider: Provider | None, config: AppConfig | None
) -> None:
    if provider is None or config is None:
        result.warn("Cannot check model without configuration")
        return
    model = config.ollama.model
    try:
        models = provider.list_models()
    except (ProviderUnavailable, ProviderError):
        result.warn("Cannot list models — Ollama unreachable")
        return
    model_names = {m.name.lower() for m in models}
    if model.lower() in model_names:
        result.messages.append(f"Model '{model}' installed")
    else:
        result.fail(f"Configured model '{model}' not installed")


def check_ollama_host(result: CheckResult, config: AppConfig | None) -> None:
    if config is None:
        return
    host = config.ollama.host
    if not host.startswith("http://") and not host.startswith("https://"):
        result.fail(f"Invalid Ollama URL: {host}")
    else:
        result.messages.append(f"Ollama URL: {host}")


def run_checks(config_path: str | None) -> list[CheckResult]:
    checks: list[CheckResult] = []

    r = CheckResult("package version")
    check_package_version(r)
    checks.append(r)

    r = CheckResult("python version")
    check_python_version(r)
    checks.append(r)

    r = CheckResult("configuration")
    config = check_configuration(r, config_path)
    checks.append(r)

    provider: Provider | None = None
    if config is not None:
        try:
            provider = create_provider(config)
        except Exception:
            provider = None

    r = CheckResult("provider")
    check_provider(r, provider)
    checks.append(r)

    r = CheckResult("ollama URL")
    check_ollama_host(r, config)
    checks.append(r)

    r = CheckResult("terminal")
    check_terminal(r, config)
    checks.append(r)

    r = CheckResult("log file")
    check_log_file(r, config)
    checks.append(r)

    r = CheckResult("ollama reachable")
    check_ollama_reachable(r, provider)
    checks.append(r)

    r = CheckResult("model installed")
    check_model_installed(r, provider, config)
    checks.append(r)

    return checks


def print_report(checks: list[CheckResult]) -> int:
    errors = 0
    warnings = 0
    print()
    print(f"  AIDoor Doctor — {__version__}")
    print()
    for r in checks:
        status = "\u2713" if r.ok else "\u2717"
        label = f"  {status} {r.name}"
        print(label)
        for msg in r.messages:
            icon = "\u2713" if r.passed else "\u2717"
            print(f"      {icon} {msg}")
        for w in r.warnings:
            print(f"      \u26a0 {w}")
            warnings += 1
        if not r.passed:
            errors += 1
    print()
    if errors == 0 and warnings == 0:
        print("  All checks passed.")
    elif errors == 0 and warnings > 0:
        print(f"  Passed with {warnings} warning(s).")
    else:
        print(f"  {errors} check(s) failed, {warnings} warning(s).")
    print()
    return errors + warnings


def doctor_main(config_path: str | None) -> int:
    checks = run_checks(config_path)
    score = print_report(checks)
    if sum(1 for c in checks if not c.passed) > 0:
        return 2
    if score > 0:
        return 1
    return 0
