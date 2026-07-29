# Changelog

## 0.2.1 — 2026-07-28 — Deployment and Release Hardening

- Added `aidoor doctor` CLI command for system diagnostics
- Added `aidoor models` CLI command to list installed Ollama models
- Added `aidoor version` CLI command showing version, Python, platform, and Ollama info
- Changed CLI to subcommand-based structure (`aidoor run`, `aidoor doctor`, etc.)
- Improved configuration validation with friendly error messages
- Added release assets: example config, Mystic/launcher scripts, systemd service example
- Added documentation: installation guide, Mystic integration, troubleshooting
- Updated package build to include docs/ and examples/ in source distribution
- Added comprehensive tests for doctor, models, and version commands
- Version 0.2.0 → 0.2.1

## 0.2.0 — 2026-07-28 — M1 Local Ollama Chat

- Implemented Ollama HTTP client with streaming support
- Added interactive chat loop with conversation history
- Added slash commands: /help, /clear, /model, /model list, /model select, /quit
- Added StreamRenderer with word-wrapping and ESC/Ctrl+C cancellation
- Added model selection UI for multi-model environments
- Integrated Ollama into main menu and about screen
- Added ChatSession with message history management
- All HTTP details hidden inside OllamaClient
- Synchronous I/O throughout
- Package version updated to 0.2.0

## 0.1.2 — 2026-07-28 — Terminal Layout Bugfix

- Fixed splash-screen box/content overlap — explicit cursor positioning between absolute box drawing and sequential info block output
- Fixed goodbye-screen layout — box closes completely before "Returning to BBS..." with one intentional blank row
- Added `RenderBounds` dataclass to track box boundaries; `draw_box()` now returns box dimensions alongside the render string
- Suppressed INFO/DEBUG log output during interactive sessions when no `log_file` is configured (prevents `[INFO] aidoor: Exiting AIDoor` from corrupting the terminal)
- Startup errors remain visible on stderr; normal-exit log goes to configured log file only
- Clean terminal handoff: terminal mode restored, cursor shown, cursor moved to column 1 on fresh line, output flushed before exit
- Normalized local-mode display: "Mode : LOCAL TEST" replaces old `*** LOCAL TEST MODE ***` banner
- Added `_write_at()` helper for explicit cursor-positioned output; removes mixed rendering model risk
- 16 new regression tests covering splash/goodbye layout, logging isolation, and clean terminal handoff

## 0.1.1 — 2026-07-28 — M0 Polish Release

- Fixed right-border rendering — all screens now use ANSI cursor positioning with validated dimensions, eliminating off-by-one border errors
- Fixed goodbye fallback — bottom-right corner was using top-right character (`╗` instead of `╝`)
- Centralized box drawing — `draw_box()`, `draw_box_content_line()`, `draw_box_separator()`, `draw_box_title_line()` in `ansi.py`; all screens reuse them
- Character set abstraction — `BoxChars` dataclass with `UNICODE_BOX` and `CP437_BOX` instances; `charset` config option
- Terminal robustness — narrow terminal detection (`< 40x10` shows friendly message), cursor visibility always restored in `close()`, `pause()` uses charset-aware separator
- ANSI safety review — no `print()` in screen code, all I/O through `Terminal`, cursor visibility and raw mode always restored
- Config extended with `charset` field (validated, defaults to `"unicode"`)
- 27 new tests covering box dimensions, charset rendering, cursor restoration, border alignment, minimum terminal size

## 0.1.0 — 2026-07-28 — M0 Door Skeleton

- DOOR32.SYS parser with validation
- Normalized user session model
- ANSI terminal abstraction with raw-mode key reading
- Local test mode (`--local`)
- Splash, main menu, About, Session info, and Goodbye screens
- TOML configuration with typed dataclasses
- Structured logging
- pytest test suite with FakeTerminal
- GitHub Actions CI (Python 3.11, 3.12, 3.13)
- Ruff, mypy, and build verification
- Installation and local-run scripts
- Mystic BSS installation documentation
