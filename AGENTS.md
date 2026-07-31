# AGENTS.md — AIDoor

AIDoor is a terminal-based BBS door for local AI chat via Ollama. M2 implements the provider abstraction layer for future LLM integrations.

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
    providers/
        __init__.py     Public API exports
        base.py         Abstract Provider and ProviderInfo
        errors.py       Generic provider errors
        models.py       Shared data models (Message, ModelInfo, etc.)
        registry.py     Provider registry
        factory.py      Provider factory (reads config, returns Provider)
        ollama.py       OllamaProvider wrapping OllamaClient
    ollama/
        __init__.py     Public API exports
        client.py       HTTP client for Ollama /api/chat (streaming)
        chat_session.py Conversation session with message history
        chat_ui.py      Interactive chat loop with commands
        errors.py       Ollama-specific exceptions (inherit from provider errors)
        models.py       Ollama-specific data models (re-exports shared models)
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
- Expected errors (config, drop-file, provider) must never show a traceback to the caller.
- Before submitting, run: `uv run ruff check .`, `uv run mypy src`, `uv run pytest`.
- No INFO logging in interactive terminal (warnings/errors only via log file).
- Never commit secrets, API keys, or credentials.
- Do not extend scope beyond the active milestone.
- No asyncio. Everything is synchronous.

## Provider Architecture

All chat operations go through the `Provider` abstract interface in `providers/base.py`.

### Provider Interface

```
health() -> bool
list_models() -> list[ModelInfo]
chat_stream(model: str, messages: list[dict]) -> Iterator[str]
provider_name() -> str
provider_type() -> str
supports_streaming() -> bool  (default False)
supports_tools() -> bool       (default False)
supports_images() -> bool      (default False)
supports_embeddings() -> bool  (default False)
```

### ProviderInfo

```
id: str
display_name: str
local: bool
streaming: bool
tools: bool
vision: bool
embeddings: bool
```

### Provider Lifecycle

1. `ProviderFactory.create_provider(config)` reads `config.provider.type` (defaults to `"ollama"`)
2. Registry maps type string to provider class
3. Factory instantiates provider with `config.ollama` section
4. Provider is passed to `chat_loop()` and doctor checks
5. Errors are caught as `ProviderUnavailable`, `ProviderResponseError`, `ProviderModelNotFoundError`

### Adding a New Provider

1. Create `providers/<name>.py` with a class implementing `Provider`
2. Register in `factory.py` via `registry.register("<type>", <Name>Provider)`
3. Add `<name>` to valid types in `config.py` `ProviderConfig.__post_init__`
4. Add config section to `AppConfig` if new settings are needed
5. Update `factory.py` `create_provider()` to pass the correct config section
6. Write tests using `MagicMock(spec=Provider)` or by mocking HTTP

## Terminal Rules

- `StdinStdoutTerminal` for real usage; `FakeTerminal` for testing.
- `FakeTerminal` captures output via `output` property and supports key injection.
- Always call `term.close()` to restore terminal state.
- Use `term.pause()` for "press any key" prompts.
- Use `term.write()` with ANSI escape sequences (cursor_pos, colors, etc.).

## Ollama Rules

- `OllamaClient` uses `urllib` only (no `requests` dependency) and is wrapped by `OllamaProvider`.
- All streaming is synchronous via `Iterator[str]`.
- The `StreamRenderer` wraps output to `term.width`, flushes continuously, and handles ESC/Ctrl+C cancellation.
- `ChatSession` owns message history; formatted with `to_api_format()` for API calls.
- The chat UI verifies provider health and model availability on entry.
- Model selection is interactive when multiple models are installed; auto-selects single models.
- All chat operations go through `Provider` interface — no direct `OllamaClient` usage outside providers.

## Testing Philosophy

- Use `FakeTerminal` to test screen rendering without a real terminal.
- Mock all HTTP in `OllamaClient` tests; never require a running Ollama server.
- Mock providers with `MagicMock(spec=Provider)` for chat UI and doctor tests.
- Mock Door32 files with tempfiles for drop-file parsing tests.
- Test config validation with invalid inputs.
- Test session creation from both Door32 data and local defaults.
- Test ANSI helpers for correctness and edge cases.
- Test menu navigation by injecting key sequences.
- Error conditions must produce sensible error messages (no tracebacks).

## Future Milestones

- M3: Gallery browsing and ANSI file management
- M4: AnsiForge integration and advanced editing tools
