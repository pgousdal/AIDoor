# Architecture

## Layered design

```
CLI
 └── Application
      ├── Configuration
      ├── Drop-file parser
      ├── Session
      ├── Screens
      └── Terminal
```

### Layer responsibilities

| Module      | Responsibility |
|-------------|----------------|
| `cli.py`    | Argument parsing, error display, exit codes. Thin layer. |
| `app.py`    | Program flow orchestration. |
| `config.py` | TOML parsing, validation, typed dataclasses. Depends on `tomllib`. |
| `door32.py` | DOOR32.SYS parsing only. Returns `Door32Data`. |
| `session.py`| Normalized `Session` dataclass. Converter from `Door32Data`. |
| `ansi.py`   | ANSI escape constants, text sanitization. |
| `terminal.py`| Terminal I/O abstraction. `StdinStdoutTerminal` and `FakeTerminal`. |
| `screens.py`| UI screen builders. Use `Terminal` for all I/O. |
| `errors.py` | Exception hierarchy. |
| `logging_config.py` | logging setup. |

### Key rules

1. `door32.py` handles only drop-file parsing.
2. `session.py` normalises raw drop-file data into domain types.
3. All other code uses `Session`, never raw `Door32Data`.
4. `terminal.py` owns all terminal I/O.
5. Other modules never write to `sys.stdout` or read `sys.stdin` directly.
6. `ansi.py` contains only constants and formatting functions.
7. `screens.py` uses only the `Terminal` abstraction.
8. `app.py` coordinates, not controls screens directly.
9. CLI code has no domain or screen logic.
10. No module except `door32.py` and Mystic documentation references Mystic.

## Error handling

- Domain layers raise custom exceptions (`AIDoorError`, `DropFileError`, etc.).
- CLI catches known exceptions, prints user-friendly messages, returns non-zero exit codes.
- Unexpected exceptions are logged with traceback but shown as a generic error to the user.
- Terminal state is restored in `finally` blocks.

## Test strategy

- Use `FakeTerminal` for screen and app tests — no real terminal needed.
- Door32 tests use fixture files and temporary files.
- Session tests are pure data transformations.
- Config tests use temporary TOML files.
