from __future__ import annotations

import argparse
import logging
import platform
import sys

from aidoor.app import run_app
from aidoor.config import parse_config
from aidoor.doctor.checks import doctor_main
from aidoor.errors import AIDoorError, ConfigurationError, DropFileError
from aidoor.logging_config import setup_logging
from aidoor.providers import (
    ProviderConfigurationError,
    ProviderError,
    ProviderUnavailable,
    create_provider,
)
from aidoor.version import __app_name__, __version__

logger = logging.getLogger("aidoor")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=__app_name__.lower(),
        description=f"{__app_name__} — {__version__} — ANSI-based BBS door",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Run interactively (default)")
    run_parser.add_argument("--door32", metavar="PATH", help="Path to DOOR32.SYS drop file")
    run_parser.add_argument(
        "--local", action="store_true", help="Run in local test mode without Mystic"
    )
    run_parser.add_argument("--config", metavar="PATH", help="Path to configuration file")

    doctor_parser = sub.add_parser("doctor", help="Run diagnostics")
    doctor_parser.add_argument("--config", metavar="PATH", help="Path to configuration file")

    models_parser = sub.add_parser("models", help="List installed Ollama models")
    models_parser.add_argument("--config", metavar="PATH", help="Path to configuration file")

    ver_parser = sub.add_parser("version", help="Show version information")
    ver_parser.add_argument(
        "--config", metavar="PATH", help="Path to configuration file (for Ollama version)"
    )

    return parser


def _format_error(message: str) -> str:
    return f"Error: {message}"


def _cmd_run(args: argparse.Namespace) -> int:
    if not args.local and not args.door32:
        print("Specify --local or --door32", file=sys.stderr)
        return 1

    try:
        config = parse_config(args.config)
    except ConfigurationError as exc:
        print(_format_error(str(exc)), file=sys.stderr)
        return 1

    setup_logging(log_level=config.general.log_level, log_file=config.general.log_file)

    if config.general.log_file:
        logger.info("%s v%s starting", __app_name__, __version__)

    try:
        return run_app(door32_path=args.door32, local=args.local, config=config)
    except DropFileError as exc:
        logger.error("Drop file error: %s", exc)
        print(_format_error(str(exc)), file=sys.stderr)
        return 1
    except ConfigurationError as exc:
        logger.error("Configuration error: %s", exc)
        print(_format_error(str(exc)), file=sys.stderr)
        return 1
    except AIDoorError as exc:
        logger.error("Application error: %s", exc)
        print(_format_error(str(exc)), file=sys.stderr)
        return 1
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        print(_format_error("An unexpected error occurred. See log for details."), file=sys.stderr)
        return 2


def _cmd_doctor(config_path: str | None) -> int:
    return doctor_main(config_path)


def _cmd_models(config_path: str | None) -> int:
    try:
        config = parse_config(config_path)
    except ConfigurationError as exc:
        print(_format_error(str(exc)), file=sys.stderr)
        return 1

    try:
        provider = create_provider(config)
        models = provider.list_models()
    except (ProviderUnavailable, ProviderError) as exc:
        print(_format_error(str(exc)), file=sys.stderr)
        return 1
    except ProviderConfigurationError as exc:
        print(_format_error(str(exc)), file=sys.stderr)
        return 1

    if not models:
        print("Installed models")
        print("  (none)")
    else:
        print("Installed models")
        for m in models:
            print(f"  {m.name}")
    return 0


def _cmd_version(config_path: str | None) -> int:
    print(f"AIDoor version  : {__version__}")
    print(f"Python version  : {sys.version.split()[0]}")
    print(f"Platform        : {sys.platform} ({platform.machine()})")

    try:
        config = parse_config(config_path)
        provider = create_provider(config)
        print(f"Provider        : {provider.provider_name()}")
        if provider.health():
            print("Ollama version  : available")
        else:
            print("Ollama version  : unavailable")
    except Exception:
        print("Provider        : Ollama")
        print("Ollama version  : unavailable")

    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    known_commands = {"run", "doctor", "models", "version"}

    if argv:
        parser = _build_parser()

        # Handle top-level --version and --help explicitly
        if argv[0] in ("--version", "--help"):
            parser.parse_args(argv)
            return 0

        if argv[0] in known_commands:
            # Subcommand mode
            args = parser.parse_args(argv)
            if args.command == "doctor":
                return _cmd_doctor(args.config)
            if args.command == "models":
                return _cmd_models(args.config)
            if args.command == "version":
                return _cmd_version(args.config)
            if args.command == "run":
                return _cmd_run(args)
            return 1

        # Old-style flags — prepend "run" for backwards compat
        args = parser.parse_args(["run"] + argv)
        return _cmd_run(args)

    # No args — show usage
    _build_parser().print_help()
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
