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
    def test_shows_aidoor_in_output(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        output = term.output
        assert "AIDoor" in output
        assert session.display_name in output

    def test_local_mode_indicated(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        assert "LOCAL TEST" in term.output
        assert "LOCAL TEST MODE" not in term.output

    def test_missing_ansi_asset_uses_fallback(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session, ansi_dir="/nonexistent")
        assert "AIDoor" in term.output


class TestMainMenu:
    def test_contains_all_options(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["q"])
        choice = show_main_menu(term, session)
        output = term.output
        assert "About" in output
        assert "Session" in output
        assert "Return" in output
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

    def test_invalid_choice_does_not_exit(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=["x", "q", "q"])
        result = show_main_menu(term, session)
        assert result == "q"
        assert "Invalid" in term.output


class TestAbout:
    def test_shows_aidoor_and_version(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_about(term, session)
        output = term.output
        assert "AIDoor" in output
        assert "M0" in output
        assert "MIT" in output

    def test_shows_no_ai_provider_message(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_about(term, session)
        assert "AI provider" in term.output


class TestSessionInfo:
    def test_shows_normalized_session_data(self) -> None:
        session = create_local_session(
            alias="TestUser",
            real_name="Test Real",
            node_number=3,
        )
        term = FakeTerminal(keys=[" "])
        show_session_info(term, session)
        output = term.output
        assert "TestUser" in output
        assert "Test Real" in output
        assert "3" in output

    def test_local_mode_yes(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_session_info(term, session)
        assert "Yes" in term.output

    def test_local_mode_no(self) -> None:
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

    def test_missing_ansi_asset_uses_fallback(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term, ansi_dir="/nonexistent")
        assert "AIDoor" in term.output or "BBS" in term.output
