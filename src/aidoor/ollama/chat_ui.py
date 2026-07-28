from __future__ import annotations

from aidoor.ollama.client import OllamaClient
from aidoor.ollama.errors import OllamaConnectionError, OllamaError
from aidoor.ollama.models import ModelInfo, ModelSelectionResult
from aidoor.terminal import Terminal


def _sort_and_dedupe_models(
    models: list[ModelInfo],
    default_model: str,
) -> tuple[list[ModelInfo], int | None]:
    seen: set[str] = set()
    deduped: list[ModelInfo] = []
    for m in models:
        key = m.name.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(m)

    deduped.sort(key=lambda m: m.name.lower())

    default_index: int | None = None
    for i, m in enumerate(deduped):
        if m.name.lower() == default_model.lower():
            default_index = i
            break

    return deduped, default_index


def show_model_selection(
    term: Terminal,
    models: list[ModelInfo],
    default_model: str,
) -> ModelSelectionResult:
    sorted_models, default_index = _sort_and_dedupe_models(models, default_model)

    while True:
        parts: list[str] = []
        parts.append("\r\n  Installed models\r\n")

        for i, m in enumerate(sorted_models):
            label = f"{i + 1}. {m.name}"
            if i == default_index:
                label += "   (default)"
            parts.append(f"  {label}\r\n")

        if default_index is None:
            parts.append("\r\n")
            parts.append(
                "  Configured default model is not installed.\r\n"
            )
            parts.append("  You may choose any installed model.\r\n")

        parts.append("\r\n  Q. Cancel\r\n")
        parts.append("\r\n  Select: ")
        term.write("".join(parts))
        term.flush()

        choice = term.read_key().lower()
        if choice == "q":
            return ModelSelectionResult(cancelled=True)

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sorted_models):
                return ModelSelectionResult(model=sorted_models[idx].name)
        except ValueError:
            pass


def _show_header(term: Terminal, model_name: str) -> None:
    bw = 42
    header_lines = [
        "\u2554" + "\u2550" * (bw - 2) + "\u2557",
        "\u2551" + " " * (bw - 2) + "\u2551",
        "\u2551" + "            A I D o o r".center(bw - 2) + "\u2551",
        "\u2551" + "           Local AI Chat".center(bw - 2) + "\u2551",
        "\u255a" + "\u2550" * (bw - 2) + "\u255d",
    ]
    info_lines = [
        "  Provider : Ollama",
        f"  Model    : {model_name}",
        "  Status   : LOCAL",
    ]
    term.write("\r\n".join(header_lines + [""] + info_lines) + "\r\n")
    term.flush()


def chat_loop(
    term: Terminal,
    client: OllamaClient,
    config_model: str,
) -> None:
    try:
        models = client.list_models()
    except (OllamaConnectionError, OllamaError):
        term.write(
            "\r\n  Ollama server not available.\r\n"
            "  Please start Ollama and try again.\r\n"
        )
        term.flush()
        term.pause("\r\n[Press any key to continue] ")
        return

    if not models:
        term.write(
            "\r\n  No models installed.\r\n"
            "  Please pull a model with: ollama pull <model>\r\n"
        )
        term.flush()
        term.pause("\r\n[Press any key to continue] ")
        return

    sorted_models, default_index = _sort_and_dedupe_models(models, config_model)

    if len(sorted_models) == 1:
        result = ModelSelectionResult(model=sorted_models[0].name)
    else:
        result = show_model_selection(term, sorted_models, config_model)

    if result.cancelled:
        return

    assert result.model is not None
    _show_header(term, result.model)
    term.writeln()
    term.writeln("  You> ")
    term.flush()
