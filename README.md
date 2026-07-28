# AIDoor

A terminal-based BBS door for local AI chat via Ollama.

## Status

**M1 Local Ollama Chat** — v0.2.0

Chat with local LLMs through a BBS terminal interface. Supports streaming
responses, conversation history, model switching, and slash commands.

## Features

- Launch from Mystic via DOOR32 or run locally for testing
- ANSI terminal UI with CP437/Unicode box drawing
- Chat with any Ollama model installed on your server
- Streaming responses — see text as it's generated
- Slash commands: `/help`, `/clear`, `/model`, `/model list`, `/model select`, `/quit`
- Cancel generation with ESC or Ctrl+C
- Conversation history maintained during session
- Model selection on first launch
- Clean exit back to BBS

## Installation

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and a running
[Ollama](https://ollama.com) server.

### Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Pull a model

```bash
ollama pull llama3.1
```

### Install AIDoor

```bash
git clone <repo>
cd aidoor
uv sync
```

## Usage

### Start Ollama (if not already running)

```bash
ollama serve
```

### Local test mode

```bash
uv run aidoor --local
```

Select **Chat** from the main menu to start chatting.

### Mystic door mode

Configure your BBS to run:

```bash
uv run aidoor --door32 /path/to/DOOR32.SYS
```

### Example chat session

```
╔══════════════════════════════════════════════╗
║              A I D o o r                     ║
║           Local AI Chat                      ║
╚══════════════════════════════════════════════╝

  Provider : Ollama
  Model    : llama3.1
  Status   : LOCAL

  You> What is the capital of France?

  AI> The capital of France is Paris.

  You> /quit
```

### Slash commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/model` | Show current model |
| `/model list` | List installed models |
| `/model select` | Change model |
| `/quit` | Return to main menu |

### Configuration

Optional TOML config file:

```toml
[general]
log_level = "INFO"
log_file = "/var/log/aidoor.log"
ansi = true

[terminal]
width = 80
height = 24

[ollama]
enabled = true
host = "http://localhost:11434"
model = "llama3.1"
timeout = 120
```

Pass with `--config /path/to/config.toml`.

## Mystic Setup

1. Install Python 3.11+ and uv on your BBS system.
2. Copy the project to your Mystic door directory.
3. Create a door in Mystic pointing to `uv run aidoor --door32 %DROP%`.
4. The `%DROP%` variable will resolve to the DOOR32.SYS path.

## Development

```bash
uv sync --group dev
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

## Known Limitations

- Ollama only — no OpenAI, Anthropic, Gemini, or other providers
- No provider abstraction layer
- No conversation persistence (history is lost on exit)
- Synchronous I/O — no asyncio
- No RAG, embeddings, tools, or function calling
- No image generation or vision support
- No built-in ANSI editor or gallery

## License

MIT
