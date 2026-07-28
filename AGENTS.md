# AGENTS.md — AIDoor

AIDoor is a terminal-based BBS door for AI chat. M0 has no AI or network code.

## Rules

- Terminal I/O must go through `Terminal` abstraction in `terminal.py`; never write to `sys.stdout` or read `sys.stdin` directly.
- All dynamic text (usernames, BBS names, drop-file data) must be sanitized with `ansi.sanitize_text()` before display.
- Drop-file parsers (`door32.py`) must stay isolated from domain logic.
- Mystic-specific details must not leak into domain layers (`session.py`, `app.py`, `screens.py`).
- Type hints are required on all public functions and methods.
- Tests must cover error cases, not just happy paths.
- Expected errors (config, drop-file) must never show a traceback to the caller.
- Before submitting, run: `uv run ruff check .`, `uv run mypy src`, `uv run pytest`.
- Never commit secrets, API keys, or credentials.
- Do not extend scope beyond the active milestone.
