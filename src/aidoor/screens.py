from __future__ import annotations

from pathlib import Path

from aidoor.ansi import (
    CLEAR,
    CURSOR_HIDE,
    CURSOR_SHOW,
    HOME,
    RESET,
    UNICODE_BOX,
    BoxChars,
    cursor_pos,
    draw_box,
    draw_box_content_line,
    draw_box_separator,
    sanitize_text,
)
from aidoor.session import Session
from aidoor.terminal import Terminal
from aidoor.version import __app_name__, __milepost__, __version__

_MIN_TERM_WIDTH = 40
_MIN_TERM_HEIGHT = 10


def _load_ansi_asset(path: str | Path) -> str | None:
    p = Path(path)
    if p.exists() and p.is_file():
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    return None


def _check_terminal_size(term: Terminal) -> bool:
    if term.width < _MIN_TERM_WIDTH or term.height < _MIN_TERM_HEIGHT:
        term.clear()
        term.writeln()
        term.writeln(f"  Terminal too small ({term.width}x{term.height}).")
        term.writeln(f"  Minimum required: {_MIN_TERM_WIDTH}x{_MIN_TERM_HEIGHT}.")
        term.pause("\r\n[Press any key to exit] ")
        return False
    return True


def _write_at(term: Terminal, row: int, col: int, text: str) -> None:
    term.write(cursor_pos(row, col) + text)


def show_splash(
    term: Terminal,
    session: Session,
    ansi_dir: str | Path | None = None,
    charset: BoxChars = UNICODE_BOX,
) -> None:
    if not _check_terminal_size(term):
        return

    content: str | None = None
    if ansi_dir is not None:
        content = _load_ansi_asset(Path(ansi_dir) / "splash.ans")

    if content:
        term.write(CLEAR + HOME + CURSOR_HIDE + RESET + content)
        info_start = 9
    else:
        bw = 50
        bh = 7
        inner = bw - 2
        box_str, bounds = draw_box(1, 1, bw, bh, charset=charset)
        parts = [
            CLEAR + HOME + CURSOR_HIDE + RESET,
            box_str,
            draw_box_content_line(3, 1, bw, __app_name__.center(inner), charset),
            draw_box_content_line(5, 1, bw, __milepost__.center(inner), charset),
        ]
        term.write("".join(parts))
        info_start = bounds.next_row + 1

    _write_at(term, info_start, 1, f"  Version : {__version__}")
    _write_at(term, info_start + 1, 1, f"  User    : {sanitize_text(session.display_name)}")
    _write_at(term, info_start + 2, 1, f"  Node    : {session.node_number}")
    _write_at(term, info_start + 3, 1, f"  BBS     : {sanitize_text(session.bbs_software)}")
    mode_label = "LOCAL TEST" if session.local_mode else "NORMAL"
    _write_at(term, info_start + 4, 1, f"  Mode    : {mode_label}")
    _write_at(term, info_start + 5, 1, "")
    _write_at(term, info_start + 6, 1, "  Select Chat to start a local AI session.")
    term.write(CURSOR_SHOW)
    term.flush()
    term.pause("\r\n[Press any key to continue] ")
    term.flush()


def show_main_menu(
    term: Terminal,
    session: Session,
    charset: BoxChars = UNICODE_BOX,
) -> str:
    if not _check_terminal_size(term):
        return "q"

    while True:
        bw = 38
        bh = 10

        box_str, bounds = draw_box(1, 1, bw, bh, title=f"{__app_name__} Main Menu", charset=charset)
        parts = [
            CLEAR + HOME + CURSOR_HIDE + RESET,
            box_str,
            draw_box_separator(3, 1, bw, charset),
            draw_box_content_line(5, 1, bw, "  1. Chat", charset),
            draw_box_content_line(6, 1, bw, "  2. About " + __app_name__, charset),
            draw_box_content_line(7, 1, bw, "  3. Session information", charset),
            draw_box_content_line(8, 1, bw, "  Q. Return to BBS", charset),
        ]
        term.write("".join(parts))

        prompt_row = bounds.next_row + 1
        _write_at(term, prompt_row, 1, CURSOR_SHOW + "  Choice: ")
        term.flush()

        choice = term.read_key().lower()

        if choice in ("\r", "\n"):
            continue
        if choice in ("1", "2", "3", "q"):
            return choice

        _write_at(term, prompt_row + 1, 1, f"\r\n  Invalid choice: '{sanitize_text(choice)}'")
        term.pause("\r\n[Press any key to try again] ")


def show_about(
    term: Terminal,
    session: Session,
    charset: BoxChars = UNICODE_BOX,
) -> None:
    if not _check_terminal_size(term):
        return

    bw = 50
    bh = 12

    box_str, bounds = draw_box(1, 1, bw, bh, title=f"About {__app_name__}", charset=charset)
    parts = [
        CLEAR + HOME + CURSOR_HIDE + RESET,
        box_str,
        draw_box_separator(3, 1, bw, charset),
        draw_box_content_line(4, 1, bw, f"  Version: {__version__}", charset),
        draw_box_content_line(5, 1, bw, f"  {__milepost__}", charset),
        draw_box_content_line(6, 1, bw, "", charset),
        draw_box_content_line(7, 1, bw, "  Ollama: local AI chat available.", charset),
        draw_box_content_line(8, 1, bw, "  Select Chat from the main menu.", charset),
        draw_box_content_line(9, 1, bw, "", charset),
        draw_box_content_line(10, 1, bw, f"  Project: {__app_name__}", charset),
        draw_box_content_line(11, 1, bw, "  License: MIT", charset),
    ]
    term.write("".join(parts))
    _write_at(term, bounds.next_row + 1, 1, CURSOR_SHOW)
    term.flush()
    term.pause()


def show_session_info(
    term: Terminal,
    session: Session,
    charset: BoxChars = UNICODE_BOX,
) -> None:
    if not _check_terminal_size(term):
        return

    bw = 50
    bh = 14

    items = [
        ("Display name:", sanitize_text(session.display_name)),
        ("Alias:", sanitize_text(session.alias)),
        ("Real name:", sanitize_text(session.real_name)),
        ("User ID:", str(session.user_id)),
        ("Security level:", str(session.security_level)),
        ("Time left (min):", str(session.time_left_minutes)),
        ("Node:", str(session.node_number)),
        ("BBS software:", sanitize_text(session.bbs_software)),
        ("Terminal:", sanitize_text(session.terminal_emulation)),
        ("Local mode:", "Yes" if session.local_mode else "No"),
    ]

    box_str, bounds = draw_box(1, 1, bw, bh, title="Session Information", charset=charset)
    parts = [
        CLEAR + HOME + CURSOR_HIDE + RESET,
        box_str,
        draw_box_separator(3, 1, bw, charset),
    ]

    for i, (label, value) in enumerate(items):
        row = 4 + i
        content = f"  {label:<19} {value:<27}"
        parts.append(draw_box_content_line(row, 1, bw, content, charset))

    term.write("".join(parts))
    _write_at(term, bounds.next_row + 1, 1, CURSOR_SHOW)
    term.flush()
    term.pause()


def show_goodbye(
    term: Terminal,
    ansi_dir: str | Path | None = None,
    charset: BoxChars = UNICODE_BOX,
) -> None:
    content: str | None = None
    if ansi_dir is not None:
        content = _load_ansi_asset(Path(ansi_dir) / "goodbye.ans")

    if content:
        term.write(CURSOR_HIDE + RESET + CLEAR + HOME + content)
        next_row = 8
    else:
        bw = 50
        bh = 5
        inner = bw - 2
        box_str, bounds = draw_box(1, 1, bw, bh, charset=charset)
        parts = [
            CLEAR + HOME + CURSOR_HIDE + RESET,
            box_str,
            draw_box_content_line(3, 1, bw, "Thank you for using AIDoor".center(inner), charset),
        ]
        term.write("".join(parts))
        next_row = bounds.next_row + 1

    _write_at(term, next_row, 1, CURSOR_SHOW)
    term.writeln("  Returning to BBS...")
    term.writeln()
    term.flush()
