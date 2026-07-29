from __future__ import annotations

from aidoor.screens import (
    show_about,
    show_goodbye,
    show_main_menu,
    show_session_info,
    show_splash,
)
from aidoor.session import create_local_session
from aidoor.terminal import FakeTerminal


class TestSplash:
    def test_shows_app_name_in_output(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        output = term.output
        assert "AIDoor" in output
        assert session.display_name in output

    def test_shows_node_number(self) -> None:
        session = create_local_session(node_number=5)
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        assert "5" in term.output


class TestMainMenu:
    def test_contains_chat_option(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["q"])
        choice = show_main_menu(term, session)
        output = term.output
        assert "Chat" in output
        assert "About" in output
        assert "Session information" in output
        assert "Return to BBS" in output
        assert choice == "q"

    def test_accepts_lowercase_q(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["q"])
        assert show_main_menu(term, session) == "q"

    def test_accepts_uppercase_q(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["Q"])
        assert show_main_menu(term, session) == "q"

    def test_accepts_1(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["1"])
        assert show_main_menu(term, session) == "1"

    def test_accepts_2(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["2"])
        assert show_main_menu(term, session) == "2"

    def test_accepts_3(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["3"])
        assert show_main_menu(term, session) == "3"

    def test_invalid_choice_does_not_exit(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["x", " ", "q"])
        result = show_main_menu(term, session)
        assert result == "q"
        assert "Invalid" in term.output


class TestAbout:
    def test_shows_app_name_and_version(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_about(term, session)
        output = term.output
        assert "AIDoor" in output
        assert "0.2.1" in output
        assert "M1" in output
        assert "MIT" in output
        assert "Ollama" in output


class TestSessionInfo:
    def test_shows_session_data(self) -> None:
        session = create_local_session(
            alias="TestUser",
            real_name="Test Real",
            node_number=3,
        )
        term = FakeTerminal(keys=[" "])
        show_session_info(term, session)
        output = term.output
        assert "TestUser" in output
        assert "3" in output
        assert "Local" in output

    def test_shows_local_mode(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_session_info(term, session)
        assert "Local" in term.output

    def test_door32_mode(self) -> None:
        from aidoor.door32 import Door32Data
        from aidoor.session import create_session_from_door32

        door32 = Door32Data(
            communication_type="1",
            communication_handle="0",
            baud_rate="9600",
            bbs_software="Test",
            user_record=1,
            real_name="User",
            alias="Alias",
            security_level=50,
            time_left_seconds=300,
            terminal_emulation="ANSI",
            node_number=1,
            raw_lines=(),
        )
        session = create_session_from_door32(door32)
        term = FakeTerminal(keys=[" "])
        show_session_info(term, session)
        assert "No" in term.output


class TestGoodbye:
    def test_shows_farewell(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term)
        assert "AIDoor" in term.output or "BBS" in term.output

    def test_shows_return_message(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term)
        assert "Returning to BBS" in term.output


class TestTerminalSizeCheck:
    def test_too_small_splash(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "], width=30, height=10)
        show_splash(term, session)
        assert "too small" in term.output

    def test_too_small_menu(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "], width=30, height=10)
        result = show_main_menu(term, session)
        assert result == "q"
        assert "too small" in term.output
