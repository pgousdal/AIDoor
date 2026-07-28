from __future__ import annotations

import argparse
import logging
import sys

from aidoor.app import run_app
from aidoor.config import parse_config
from aidoor.errors import AIDoorError, ConfigurationError, DropFileError
from aidoor.logging_config import setup_logging
from aidoor.version import __app_name__, __version__

logger = logging.getLogger("aidoor")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=__app_name__.lower(),
        description=f"{__app_name__} — {__version__} — ANSI-based BBS door",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--door32",
        metavar="PATH",
        help="Path to DOOR32.SYS drop file",
    )
    mode.add_argument(
        "--local",
        action="store_true",
        help="Run in local test mode without Mystic",
    )

    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def _format_error(message: str) -> str:
    return f"Error: {message}"


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.local and not args.door32:
        parser.error("Specify --local or --door32")

    try:
        config = parse_config(args.config)
    except ConfigurationError as exc:
        print(_format_error(str(exc)), file=sys.stderr)
        return 1

    setup_logging(
        log_level=config.general.log_level,
        log_file=config.general.log_file,
    )

    if config.general.log_file:
        logger.info("%s v%s starting", __app_name__, __version__)

    try:
        return run_app(
            door32_path=args.door32,
            local=args.local,
            config=config,
        )
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


if __name__ == "__main__":
    sys.exit(main())
