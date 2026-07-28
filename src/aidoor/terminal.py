from __future__ import annotations

import os
import sys
import termios
import tty
from abc import ABC, abstractmethod

from aidoor.ansi import CLEAR, CURSOR_SHOW, HOME, UNICODE_BOX, BoxChars, strip_ansi


class Terminal(ABC):
    @abstractmethod
    def write(self, text: str) -> None: ...

    @abstractmethod
    def writeln(self, text: str = "") -> None: ...

    @abstractmethod
    def flush(self) -> None: ...

    @abstractmethod
    def read_key(self) -> str: ...

    @abstractmethod
    def read_line(self) -> str: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def home(self) -> None: ...

    @abstractmethod
    def pause(self, prompt: str = "") -> None: ...

    @property
    @abstractmethod
    def width(self) -> int: ...

    @property
    @abstractmethod
    def height(self) -> int: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def poll_key(self, timeout: float = 0) -> str | None: ...


class StdinStdoutTerminal(Terminal):
    def __init__(
        self,
        width: int = 80,
        height: int = 24,
        enable_ansi: bool = True,
        charset: BoxChars = UNICODE_BOX,
    ) -> None:
        self._width = width
        self._height = height
        self._enable_ansi = enable_ansi
        self._charset = charset
        self._raw_mode = False
        self._fd: int | None = None
        self._old_attr: list[int | list[bytes | int]] | None = None

    def _enter_raw_mode(self) -> None:
        if not sys.stdin.isatty():
            return
        self._fd = sys.stdin.fileno()
        try:
            self._old_attr = termios.tcgetattr(self._fd)
            tty.setraw(self._fd)
            self._raw_mode = True
        except (termios.error, OSError):
            self._raw_mode = False

    def _restore_terminal(self) -> None:
        if self._raw_mode and self._fd is not None and self._old_attr is not None:
            try:
                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_attr)
            except (termios.error, OSError):
                pass
        self._raw_mode = False
        self._fd = None
        self._old_attr = None

    def write(self, text: str) -> None:
        if not self._enable_ansi:
            text = strip_ansi(text)
        sys.stdout.write(text)

    def writeln(self, text: str = "") -> None:
        self.write(text + "\r\n")

    def flush(self) -> None:
        sys.stdout.flush()

    def read_key(self) -> str:
        was_raw = self._raw_mode
        if not was_raw:
            self._enter_raw_mode()
        try:
            data = os.read(sys.stdin.fileno(), 1)
            if not data:
                raise EOFError("EOF on stdin")
            ch = data.decode("utf-8", errors="replace")
            if ch == "\x03":
                raise KeyboardInterrupt()
            return ch
        finally:
            if not was_raw and self._raw_mode:
                self._restore_terminal()

    def read_line(self) -> str:
        try:
            line = sys.stdin.readline()
            if not line:
                raise EOFError("EOF on stdin")
            return line.rstrip("\r\n")
        except KeyboardInterrupt:
            raise

    def clear(self) -> None:
        if self._enable_ansi:
            self.write(CLEAR)
        else:
            self.writeln("\n" * (self._height - 1))

    def home(self) -> None:
        if self._enable_ansi:
            self.write(HOME)
        else:
            self.clear()

    def pause(self, prompt: str = "") -> None:
        if prompt:
            msg = prompt
        else:
            sep = self._charset.h_light * 40
            msg = f"\r\n{sep}\r\n[Press any key to continue] "
        self.write(msg)
        self.flush()
        try:
            self.read_key()
        except EOFError:
            pass

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def poll_key(self, timeout: float = 0) -> str | None:
        was_raw = self._raw_mode
        if not was_raw:
            self._enter_raw_mode()
        try:
            import select

            r, _, _ = select.select([sys.stdin], [], [], timeout)
            if r:
                data = os.read(sys.stdin.fileno(), 1)
                if not data:
                    return None
                ch = data.decode("utf-8", errors="replace")
                if ch == "\x03":
                    raise KeyboardInterrupt()
                return ch
            return None
        finally:
            if not was_raw and self._raw_mode:
                self._restore_terminal()

    def close(self) -> None:
        self._restore_terminal()
        if self._enable_ansi:
            self.write(CURSOR_SHOW)
        self.write("\r\n")
        self.flush()


class FakeTerminal(Terminal):
    def __init__(
        self,
        keys: list[str] | None = None,
        width: int = 80,
        height: int = 24,
        enable_ansi: bool = True,
        charset: BoxChars = UNICODE_BOX,
    ) -> None:
        self._keys = list(keys or [])
        self._key_index = 0
        self._lines: list[str] = []
        self._width = width
        self._height = height
        self._enable_ansi = enable_ansi
        self._charset = charset
        self._closed = False

    def write(self, text: str) -> None:
        if not self._enable_ansi:
            text = strip_ansi(text)
        self._lines.append(text)

    def writeln(self, text: str = "") -> None:
        self.write(text + "\n")

    def flush(self) -> None:
        pass

    def read_key(self) -> str:
        if self._key_index >= len(self._keys):
            raise EOFError("No more keys")
        ch = self._keys[self._key_index]
        self._key_index += 1
        if ch == "\x03":
            raise KeyboardInterrupt()
        return ch

    def read_line(self) -> str:
        if self._key_index >= len(self._keys):
            raise EOFError("No more keys")
        result = self._keys[self._key_index]
        self._key_index += 1
        return result

    def clear(self) -> None:
        if self._enable_ansi:
            self.write(CLEAR)
        else:
            self.writeln("\n" * (self._height - 1))

    def home(self) -> None:
        if self._enable_ansi:
            self.write(HOME)
        else:
            self.clear()

    def pause(self, prompt: str = "") -> None:
        if prompt:
            msg = prompt
        else:
            sep = self._charset.h_light * 40
            msg = f"\n{sep}\n[Press any key to continue] "
        self.write(msg)
        try:
            self.read_key()
        except EOFError:
            pass

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def poll_key(self, timeout: float = 0) -> str | None:
        if self._key_index < len(self._keys):
            ch = self._keys[self._key_index]
            self._key_index += 1
            if ch == "\x03":
                raise KeyboardInterrupt()
            return ch
        return None

    def close(self) -> None:
        self._closed = True

    @property
    def output(self) -> str:
        return "".join(self._lines)

    @property
    def closed(self) -> bool:
        return self._closed
