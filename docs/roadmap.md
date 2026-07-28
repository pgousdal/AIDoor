# Roadmap

## M0 — Door Skeleton

- DOOR32.SYS drop-file parser
- Normalized user session
- ANSI terminal abstraction
- Local test mode
- Splash, Main Menu, About, Session Info, Goodbye screens
- TOML configuration
- Logging
- Tests and CI
- Mystic documentation

## M1 — Local Ollama-compatible chat

- Session management for conversation flow
- Ollama client integration
- Prompt input screen with character-by-character input
- Streaming response display
- Basic conversation loop
- Error handling for offline/unreachable LLM

## M2 — Provider abstraction and OpenAI-compatible API

- Abstract provider interface (`generate`, `stream`, `list_models`)
- OpenAI-compatible API client
- Multi-model selection per session or per user
- Provider configuration in TOML (no secrets in repo)
- Per-provider timeout and retry

## M3 — Quotas, security levels, and access control

- Token/usage quotas per user
- Security-level gating for providers and models
- Configurable rate limiting
- Per-user daily/monthly limits
- Admin commands to reset or adjust quotas

## M4 — Profiles and local knowledge base

- User profiles with preferences (default model, theme, prompt style)
- Local document/context store (file-based, no external database dependency)
- Custom system prompts per user or per security level
- Persistent settings across sessions

## M5 — History and deeper BBS integration

- Session history with search (file-based storage)
- Integration with BBS message bases (if supported by Mystic API)
- FARSCOPE / GlobalMSG compatibility for cross-BBS chat
- Full-screen ANSI text viewer for long outputs
- Statistics and usage reporting
