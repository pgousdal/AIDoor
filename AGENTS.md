# AGENTS.md — AIDoor

AIDoor is a terminal-based BBS door for local AI chat via Ollama. M1 implements local Ollama chat with streaming, cancellation, and slash commands.

## Architecture

```
src/aidoor/
    __init__.py
    __main__.py
    cli.py              Argument parsing and entry point
    config.py           TOML configuration with validation
    door32.py           DOOR32.SYS drop-file parser (isolated from domain)
    terminal.py         Terminal abstraction (real and fake)
    ansi.py             ANSI escape codes, box drawing helpers
    screens.py          Screen rendering (splash, menu, about, session info)
    app.py              Application orchestration
    session.py          Session dataclass and factory functions
    logging_config.py   Logging setup (warnings/errors only in terminal)
    version.py          Version constants
    errors.py           Domain exceptions
    ollama/
        __init__.py     Public API exports
        client.py       HTTP client for Ollama /api/chat (streaming)
        chat_session.py Conversation session with message history
        chat_ui.py      Interactive chat loop with commands
        errors.py       Ollama-specific exceptions
        models.py       Data models (Message, ModelInfo, etc.)
        stream_renderer.py  Streaming response renderer with word wrap
```

## Rules

- Terminal I/O must go through `Terminal` abstraction in `terminal.py`; never write to `sys.stdout` or read `sys.stdin` directly.
- All dynamic text (usernames, BBS names, drop-file data) must be sanitized with `ansi.sanitize_text()` before display.
- Drop-file parsers (`door32.py`) must stay isolated from domain logic.
- Mystic-specific details must not leak into domain layers (`session.py`, `app.py`, `screens.py`).
- All HTTP details must be hidden inside `OllamaClient`; the UI never constructs URLs or parses JSON.
- Type hints are required on all public functions and methods.
- Tests must cover error cases, not just happy paths.
- Expected errors (config, drop-file, Ollama) must never show a traceback to the caller.
- Before submitting, run: `uv run ruff check .`, `uv run mypy src`, `uv run pytest`.
- No INFO logging in interactive terminal (warnings/errors only via log file).
- Never commit secrets, API keys, or credentials.
- Do not extend scope beyond the active milestone.
- No asyncio. Everything is synchronous.

## Terminal Rules

- `StdinStdoutTerminal` for real usage; `FakeTerminal` for testing.
- `FakeTerminal` captures output via `output` property and supports key injection.
- Always call `term.close()` to restore terminal state.
- Use `term.pause()` for "press any key" prompts.
- Use `term.write()` with ANSI escape sequences (cursor_pos, colors, etc.).

## Ollama Rules

- `OllamaClient` uses `urllib` only (no `requests` dependency).
- All streaming is synchronous via `Iterator[str]`.
- The `StreamRenderer` wraps output to `term.width`, flushes continuously, and handles ESC/Ctrl+C cancellation.
- `ChatSession` owns message history; formatted with `to_api_format()` for API calls.
- The chat UI verifies Ollama health and model availability on entry.
- Model selection is interactive when multiple models are installed; auto-selects single models.

## Testing Philosophy

- Use `FakeTerminal` to test screen rendering without a real terminal.
- Mock all HTTP in `OllamaClient` tests; never require a running Ollama server.
- Mock Door32 files with tempfiles for drop-file parsing tests.
- Test config validation with invalid inputs.
- Test session creation from both Door32 data and local defaults.
- Test ANSI helpers for correctness and edge cases.
- Test menu navigation by injecting key sequences.
- Error conditions must produce sensible error messages (no tracebacks).

## Future Milestones

- M2: Gallery browsing and ANSI file management
- M3: AnsiForge integration and advanced editing tools
