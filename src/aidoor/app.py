from __future__ import annotations

import logging

from aidoor.ansi import UNICODE_BOX, BoxChars, resolve_charset
from aidoor.config import AppConfig
from aidoor.door32 import parse_door32_file
from aidoor.errors import AIDoorError
from aidoor.ollama.chat_ui import chat_loop
from aidoor.ollama.client import OllamaClient
from aidoor.screens import (
    show_about,
    show_goodbye,
    show_main_menu,
    show_session_info,
    show_splash,
)
from aidoor.session import Session, create_local_session, create_session_from_door32
from aidoor.terminal import StdinStdoutTerminal, Terminal
from aidoor.version import __app_name__, __version__

logger = logging.getLogger("aidoor")


def run_app(
    door32_path: str | None,
    local: bool,
    config: AppConfig,
    term: Terminal | None = None,
) -> int:
    logger.info(
        "Starting %s v%s (local=%s, door32=%s)",
        __app_name__,
        __version__,
        local,
        door32_path,
    )

    session: Session
    if local:
        session = create_local_session()
    elif door32_path:
        door32_data = parse_door32_file(door32_path)
        session = create_session_from_door32(door32_data)
        logger.info(
            "Session created for user %s (node %d, security %d)",
            session.display_name,
            session.node_number,
            session.security_level,
        )
    else:
        raise AIDoorError("No run mode specified. Use --local or --door32.")

    charset: BoxChars = UNICODE_BOX
    try:
        charset = resolve_charset(config.general.charset)
    except ValueError:
        logger.warning("Unknown charset %r, falling back to Unicode", config.general.charset)

    own_term = term is None
    if term is None:
        term = StdinStdoutTerminal(
            width=config.terminal.width,
            height=config.terminal.height,
            enable_ansi=config.general.ansi,
            charset=charset,
        )

    if not config.general.log_file and own_term:
        logging.getLogger("aidoor").setLevel(logging.WARNING)

    try:
        _run_interactive(term, session, charset, config)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        term.writeln("\r\n\r\nInterrupted by user.")
        term.flush()
    except EOFError:
        logger.info("Received EOF")
        term.writeln("\r\n\r\nConnection closed.")
        term.flush()
    finally:
        if own_term:
            try:
                term.close()
            except Exception:
                pass

    logger.info("Exiting AIDoor")
    return 0


def _run_interactive(
    term: Terminal,
    bbs_session: Session,
    charset: BoxChars,
    config: AppConfig,
) -> None:
    ansi_dir: str | None = None

    show_splash(term, bbs_session, ansi_dir, charset)

    if config and config.ollama.enabled:
        ollama_client = OllamaClient(
            host=config.ollama.host,
            timeout=config.ollama.timeout,
        )
    else:
        ollama_client = None

    while True:
        choice = show_main_menu(term, bbs_session, charset)

        if choice == "1":
            if ollama_client is not None:
                chat_loop(term, ollama_client, config.ollama.model)
            else:
                show_about(term, bbs_session, charset)
        elif choice == "2":
            show_about(term, bbs_session, charset)
        elif choice == "3":
            show_session_info(term, bbs_session, charset)
        elif choice == "q":
            break

    show_goodbye(term, ansi_dir, charset)
