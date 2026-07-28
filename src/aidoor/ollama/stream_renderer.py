from __future__ import annotations

from collections.abc import Iterator

from aidoor.ansi import strip_ansi
from aidoor.terminal import Terminal


class StreamRenderer:
    def __init__(self, term: Terminal, width: int) -> None:
        self._term = term
        self._width = width

    def render(
        self,
        stream: Iterator[str],
    ) -> str:
        response_text = ""
        col = 0

        for raw_token in stream:
            maybe_token = self._intercept_cancellation(raw_token)
            if maybe_token is None:
                break
            token: str = maybe_token

            visible = strip_ansi(token)
            for ch in visible:
                if ch == "\n":
                    self._term.writeln()
                    col = 0
                elif ch == "\r":
                    pass
                elif col >= self._width:
                    self._term.writeln()
                    col = 0

                if ch not in ("\n", "\r"):
                    self._term.write(ch)
                    col += 1

            response_text += visible
            self._term.flush()

            key = self._term.poll_key(0)
            if key in ("\x1b", "\x03"):
                cancel_msg = "\r\n\n[Generation cancelled]"
                self._term.write(cancel_msg)
                self._term.flush()
                response_text += cancel_msg
                break

        return response_text

    def _intercept_cancellation(self, token: str) -> str | None:
        return token
