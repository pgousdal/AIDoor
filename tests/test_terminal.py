from __future__ import annotations

import pytest

from aidoor.terminal import FakeTerminal


class TestFakeTerminalWrite:
    def test_write_stores_text(self) -> None:
        term = FakeTerminal()
        term.write("hello")
        assert term.output == "hello"

    def test_writeln_appends_newline(self) -> None:
        term = FakeTerminal()
        term.writeln("hello")
        assert term.output == "hello\n"

    def test_multiple_writes(self) -> None:
        term = FakeTerminal()
        term.write("a")
        term.write("b")
        assert term.output == "ab"


class TestFakeTerminalReadKey:
    def test_reads_keys_in_order(self) -> None:
        term = FakeTerminal(keys=["a", "b", "c"])
        assert term.read_key() == "a"
        assert term.read_key() == "b"
        assert term.read_key() == "c"

    def test_keyboard_interrupt(self) -> None:
        term = FakeTerminal(keys=["\x03"])
        with pytest.raises(KeyboardInterrupt):
            term.read_key()

    def test_eof_raises_error(self) -> None:
        term = FakeTerminal(keys=[])
        with pytest.raises(EOFError):
            term.read_key()


class TestFakeTerminalPause:
    def test_pause_uses_default_prompt_when_not_provided(self) -> None:
        term = FakeTerminal(keys=["x"])
        term.pause()
        assert "Press any key to continue" in term.output

    def test_pause_reads_key(self) -> None:
        term = FakeTerminal(keys=["q"])
        term.pause("[Press Q] ")
        assert term.output.endswith("[Press Q] ")

    def test_pause_handles_eof(self) -> None:
        term = FakeTerminal(keys=[])
        term.pause()
        assert "Press any key" in term.output


class TestFakeTerminalClear:
    def test_ansi_clear(self) -> None:
        term = FakeTerminal(enable_ansi=True)
        term.clear()
        assert "\x1b[2J" in term.output

    def test_non_ansi_clear(self) -> None:
        term = FakeTerminal(enable_ansi=False)
        term.clear()
        assert "\x1b[2J" not in term.output


class TestFakeTerminalSanitization:
    def test_ansi_stripped_when_disabled(self) -> None:
        term = FakeTerminal(enable_ansi=False)
        term.write("\x1b[31mred\x1b[0m")
        assert "\x1b[" not in term.output
        assert "red" in term.output

    def test_ansi_preserved_when_enabled(self) -> None:
        term = FakeTerminal(enable_ansi=True)
        term.write("\x1b[31mred\x1b[0m")
        assert "\x1b[31m" in term.output


class TestFakeTerminalClose:
    def test_close_sets_flag(self) -> None:
        term = FakeTerminal()
        assert not term.closed
        term.close()
        assert term.closed


class TestFakeTerminalHome:
    def test_home_ansi(self) -> None:
        term = FakeTerminal(enable_ansi=True)
        term.home()
        assert "\x1b[H" in term.output

    def test_home_non_ansi(self) -> None:
        term = FakeTerminal(enable_ansi=False)
        term.home()
        assert "\x1b[H" not in term.output


class TestFakeTerminalReadLine:
    def test_read_line(self) -> None:
        term = FakeTerminal(keys=["hello"])
        assert term.read_line() == "hello"

    def test_read_line_eof(self) -> None:
        term = FakeTerminal(keys=[])
        with pytest.raises(EOFError):
            term.read_line()
