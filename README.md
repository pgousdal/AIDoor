# AIDoor

**AIDoor** is an ANSI-based BBS door that gives users access to local and remote language models. Built for Mystic BBS on Linux, with an architecture that avoids direct framework dependencies.

## Status: M0.1 — Polish Release

M0.1 improves terminal rendering robustness with centralized box drawing, Unicode/CP437 character set support, and stronger ANSI safety. No AI or network code.

### M0 features

- DOOR32.SYS drop-file parser with validation
- Normalized user session model
- ANSI terminal abstraction (supports ANSI on/off, raw-mode key reading)
- TOML configuration via `tomllib`
- Structured logging to stderr or file
- Local test mode for development without Mystic
- Splash, Main Menu, About, Session Info, and Goodbye screens
- Graceful Ctrl+C, EOF, and error handling
- Centralized box drawing with ANSI cursor positioning (no off-by-one border errors)
- Unicode and CP437 character set support
- Narrow terminal detection and friendly error

### What M0 does NOT include

- No AI provider (Ollama, OpenAI, etc.)
- No HTTP or network code
- No database or persistence
- No chat functionality
- No user profiles
- No quotas or access control

## Requirements

- Python 3.11 or later
- `uv` (recommended) or `pip`

## Quick start

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and enter the repo
git clone https://github.com/your-org/aidoor.git
cd aidoor

# Sync environment
uv sync --all-groups

# Run in local test mode
uv run aidoor --local
```

## Usage

```bash
# Local test mode
uv run aidoor --local

# With a DOOR32.SYS drop file
uv run aidoor --door32 /path/to/DOOR32.SYS

# With explicit config
uv run aidoor --config /path/to/aidoor.toml --door32 /path/to/DOOR32.SYS

# Version
uv run aidoor --version

# Help
uv run aidoor --help
```

## Development

```bash
# Sync all dev dependencies
uv sync --all-groups

# Lint and format
uv run ruff check .
uv run ruff format --check .

# Type checking
uv run mypy src

# Tests
uv run pytest

# Build
uv build
```

## Mystic BBS setup

See [docs/installation.md](docs/installation.md) for detailed Mystic configuration.

**Important**: AI chat functionality is not available in M0. Do not deploy M0 expecting it to function as a chat door.

## Project structure

```
aidoor/
├── assets/ansi/        # ANSI art assets with built-in fallback
├── config/             # Example configuration
├── docs/               # Architecture, installation, roadmap
├── scripts/            # Install and run helpers
├── src/aidoor/         # Python package
├── tests/              # pytest suite with fixtures
├── pyproject.toml      # Project metadata and tool config
└── ...
```

## Roadmap

| Milestone | Focus |
|-----------|-------|
| M0        | Door skeleton (this release) |
| M1        | Local Ollama-compatible chat |
| M2        | Provider abstraction + OpenAI API |
| M3        | Quotas, security levels, access control |
| M4        | Profiles and local knowledge base |
| M5        | History and deeper BBS integration |

## Logging

- Production use should configure `log_file` in `aidoor.toml` to capture routine INFO/DEBUG logs.
- Without a `log_file`, routine INFO and DEBUG messages are suppressed during interactive sessions to prevent log lines from corrupting the ANSI terminal display.
- Startup configuration errors and CLI-level failures are always reported on stderr, regardless of log configuration.
- Expected interactive errors (e.g., drop-file parse failures) are shown through the terminal UI, not as raw log output.

## Security

- All dynamic text (usernames, BBS names) is sanitized before display to prevent ANSI injection.
- Terminal state is always restored on exit, error, or interrupt.
- Drop-file parsing uses controlled conversion — no raw `IndexError` or `ValueError` exposed to callers.
- Future versions will add quotas, access control, and encrypted provider configuration.

## License

MIT
