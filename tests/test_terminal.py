from __future__ import annotations

import pytest

from aidoor.terminal import FakeTerminal


class TestFakeTerminalWrite:
    def test_write_stores_text(self) -> None:
        term = FakeTerminal()
        term.write("hello")
        assert "hello" in term.output

    def test_writeln_appends_newline(self) -> None:
        term = FakeTerminal()
        term.writeln("hello")
        assert "hello\n" in term.output

    def test_writeln_without_arg(self) -> None:
        term = FakeTerminal()
        term.writeln()
        assert term.output == "\n"

    def test_flush_does_not_raise(self) -> None:
        term = FakeTerminal()
        term.flush()

    def test_multiple_writes(self) -> None:
        term = FakeTerminal()
        term.write("abc")
        term.write("def")
        assert term.output == "abcdef"


class TestFakeTerminalRead:
    def test_read_key_returns_next_key(self) -> None:
        term = FakeTerminal(keys=["a"])
        assert term.read_key() == "a"

    def test_read_key_multiple_keys(self) -> None:
        term = FakeTerminal(keys=["a", "b"])
        assert term.read_key() == "a"
        assert term.read_key() == "b"

    def test_read_key_raises_eof(self) -> None:
        term = FakeTerminal(keys=[])
        with pytest.raises(EOFError):
            term.read_key()

    def test_read_key_ctrl_c_raises_keyboard_interrupt(self) -> None:
        term = FakeTerminal(keys=["\x03"])
        with pytest.raises(KeyboardInterrupt):
            term.read_key()

    def test_read_line_returns_line(self) -> None:
        term = FakeTerminal(keys=["hello world"])
        assert term.read_line() == "hello world"

    def test_read_line_multiple_entries(self) -> None:
        term = FakeTerminal(keys=["first", "second"])
        assert term.read_line() == "first"
        assert term.read_line() == "second"

    def test_read_line_empty_string(self) -> None:
        term = FakeTerminal(keys=[""])
        assert term.read_line() == ""

    def test_read_line_eof(self) -> None:
        term = FakeTerminal(keys=[])
        with pytest.raises(EOFError):
            term.read_line()


class TestPause:
    def test_pause_waits_for_key(self) -> None:
        term = FakeTerminal(keys=[" "])
        term.pause("Press any key")
        assert "Press any key" in term.output

    def test_pause_with_default_prompt(self) -> None:
        term = FakeTerminal(keys=[" "])
        term.pause()
        assert "Press any key" in term.output


class TestClear:
    def test_clear_with_ansi(self) -> None:
        term = FakeTerminal(enable_ansi=True)
        term.clear()
        assert "\x1b[2J" in term.output

    def test_clear_without_ansi(self) -> None:
        term = FakeTerminal(enable_ansi=False, height=24)
        term.clear()
        assert "\n" * 23 in term.output


class TestDimensions:
    def test_default_width(self) -> None:
        term = FakeTerminal()
        assert term.width == 80

    def test_default_height(self) -> None:
        term = FakeTerminal()
        assert term.height == 24

    def test_custom_dimensions(self) -> None:
        term = FakeTerminal(width=100, height=50)
        assert term.width == 100
        assert term.height == 50


class TestClose:
    def test_close_sets_flag(self) -> None:
        term = FakeTerminal()
        assert not term.closed
        term.close()
        assert term.closed

    def test_close_no_error(self) -> None:
        term = FakeTerminal()
        term.close()


class TestPollKey:
    def test_poll_key_none_when_no_key(self) -> None:
        term = FakeTerminal(keys=["x"])
        result = term.poll_key(0)
        assert result is None

    def test_poll_key_escape(self) -> None:
        term = FakeTerminal(keys=["\x1b"])
        result = term.poll_key(0)
        assert result == "\x1b"

    def test_poll_key_ctrl_c(self) -> None:
        term = FakeTerminal(keys=["\x03"])
        result = term.poll_key(0)
        assert result == "\x03"

    def test_poll_key_esc_consumes_key(self) -> None:
        term = FakeTerminal(keys=["\x1b", "a"])
        term.poll_key(0)
        assert term.read_key() != "\x1b"
