from __future__ import annotations

import logging

from aidoor.ollama.chat_session import ChatSession
from aidoor.ollama.stream_renderer import StreamRenderer
from aidoor.providers import (
    ModelInfo,
    ModelSelectionResult,
    Provider,
    ProviderModelNotFoundError,
    ProviderResponseError,
    ProviderUnavailable,
)
from aidoor.terminal import Terminal

logger = logging.getLogger("aidoor")


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


def _show_header(term: Terminal, model_name: str, provider: Provider) -> None:
    bw = 42
    header_lines = [
        "\u2554" + "\u2550" * (bw - 2) + "\u2557",
        "\u2551" + " " * (bw - 2) + "\u2551",
        "\u2551" + "            A I D o o r".center(bw - 2) + "\u2551",
        "\u2551" + "           Local AI Chat".center(bw - 2) + "\u2551",
        "\u255a" + "\u2550" * (bw - 2) + "\u255d",
    ]
    info_lines = [
        f"  Provider : {provider.provider_name()}",
        f"  Model    : {model_name}",
        "  Status   : LOCAL",
    ]
    term.write("\r\n".join(header_lines + [""] + info_lines) + "\r\n")
    term.flush()


def _show_commands(term: Terminal) -> None:
    help_text = (
        "\r\n  Available commands:\r\n"
        "  /help          Show this help\r\n"
        "  /clear         Clear conversation\r\n"
        "  /model         Show current model\r\n"
        "  /model list    List installed models\r\n"
        "  /model select  Change model\r\n"
        "  /quit          Return to main menu\r\n"
    )
    term.write(help_text)
    term.flush()


def _confirm(term: Terminal, prompt: str) -> bool:
    term.write(f"\r\n  {prompt} (Y/N) ")
    term.flush()
    while True:
        key = term.read_key().lower()
        if key == "y":
            term.write("\r\n")
            term.flush()
            return True
        if key == "n":
            term.write("\r\n")
            term.flush()
            return False


def chat_loop(
    term: Terminal,
    provider: Provider,
    config_model: str,
) -> None:
    try:
        models = provider.list_models()
    except ProviderUnavailable:
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
    selected_model = result.model
    session = ChatSession(model=selected_model)
    _show_header(term, selected_model, provider)
    term.writeln()

    while True:
        term.write("  You> ")
        term.flush()

        try:
            line = term.read_line()
        except EOFError:
            return

        line = line.strip()

        if not line:
            continue

        if line.startswith("/"):
            cmd = line.lower().split()
            command = cmd[0] if cmd else "/help"

            if command == "/quit":
                return

            if command == "/help":
                _show_commands(term)
                continue

            if command == "/clear":
                if session.messages and not _confirm(term, "Clear conversation?"):
                    continue
                session.clear()
                term.write("\r\n  Conversation cleared.\r\n")
                term.flush()
                continue

            if command == "/model":
                if len(cmd) == 1:
                    term.write(
                        f"\r\n  Current model: {session.model}\r\n"
                    )
                    term.flush()
                    continue
                sub = cmd[1]
                if sub == "list":
                    for m in models:
                        label = m.name
                        if m.name.lower() == session.model.lower():
                            label += "   (active)"
                        term.write(f"  {label}\r\n")
                    term.flush()
                    continue
                if sub == "select":
                    if session.messages:
                        if not _confirm(
                            term, "Changing model will clear the conversation. Continue?"
                        ):
                            continue
                    if len(sorted_models) == 1:
                        new_model = sorted_models[0].name
                    else:
                        sel = show_model_selection(term, sorted_models, session.model)
                        if sel.cancelled:
                            continue
                        assert sel.model is not None
                        new_model = sel.model
                    if new_model != session.model:
                        session.clear()
                        session.model = new_model
                        term.write(f"\r\n  Switched to model: {new_model}\r\n")
                        term.flush()
                    continue

                term.write("\r\n  Usage: /model, /model list, /model select\r\n")
                term.flush()
                continue

            term.write(
                f"\r\n  Unknown command: {cmd[0]}\r\n"
                "  Type /help for available commands.\r\n"
            )
            term.flush()
            continue

        session.add_user_message(line)

        term.write("\r\n  AI> ")
        term.flush()

        try:
            stream = provider.chat_stream(
                model=session.model,
                messages=session.to_api_format(),
            )
            renderer = StreamRenderer(term, width=term.width)
            response = renderer.render(stream)
            session.add_assistant_message(
                _strip_cancel_suffix(response)
            )
        except ProviderModelNotFoundError:
            term.write(
                f"\r\n  Model '{session.model}' not found on server.\r\n"
            )
            term.flush()
            session._messages.pop()
            continue
        except (ProviderUnavailable) as exc:
            term.write(f"\r\n  Connection error: {exc}\r\n")
            term.flush()
            session._messages.pop()
            continue
        except ProviderResponseError:
            term.write(
                "\r\n  Invalid response from Ollama.\r\n"
            )
            term.flush()
            session._messages.pop()
            continue

        term.writeln()
        term.flush()


def _strip_cancel_suffix(text: str) -> str:
    marker = "[Generation cancelled]"
    if text.endswith(marker):
        return text[: -len(marker)]
    return text
