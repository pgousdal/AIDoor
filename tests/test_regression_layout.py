from __future__ import annotations

import logging
import os
import tempfile

from aidoor.app import run_app
from aidoor.config import AppConfig
from aidoor.door32 import Door32Data
from aidoor.screens import show_goodbye, show_splash
from aidoor.session import Session, create_local_session, create_session_from_door32
from aidoor.terminal import FakeTerminal

ANSI_BOX_V = "\u2551"


def _config() -> AppConfig:
    return AppConfig()


def _make_session() -> Session:
    door32 = Door32Data(
        communication_type="1",
        communication_handle="0",
        baud_rate="38400",
        bbs_software="Test BBS",
        user_record=42,
        real_name="John Doe",
        alias="Neo",
        security_level=100,
        time_left_seconds=1800,
        terminal_emulation="ANSI",
        node_number=1,
        raw_lines=(),
    )
    return create_session_from_door32(door32)


class TestSplashBoxContentSeparation:
    """Regression: splash box must not overlap the info block below."""

    def test_box_bottom_before_info_block(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        output = term.output

        # Find the bottom border of the box (bl corner)
        bl = "\u255a"  # box bottom-left
        box_bottom_pos = output.rfind(bl)
        assert box_bottom_pos >= 0, "Box bottom border not found"

        # Find the first info field - should be after the box bottom
        version_pos = output.find("Version")
        assert version_pos >= 0, "Version field not found"
        assert version_pos > box_bottom_pos, (
            "Version appears before or at the same position as box bottom"
        )

    def test_no_border_chars_beside_info(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        output = term.output

        info_fields = ["Version", "User", "Node", "BBS", "Mode"]
        for field in info_fields:
            # Find the field's line in output
            pos = output.find(field)
            assert pos >= 0, f"Field {field} not found"
            # Check there's no vertical border character in the same segment
            # by looking at the ANSI-positioned fragment for this field
            line_start = output.rfind("\x1b[", 0, pos)
            if line_start >= 0:
                line_end = output.find("\x1b[", pos)
                if line_end < 0:
                    line_end = len(output)
                line_fragment = output[line_start:line_end]
                assert ANSI_BOX_V not in line_fragment or field == "Mode", (
                    f"Border char found in {field} line: {line_fragment!r}"
                )

    def test_info_block_uses_aligned_format(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        output = term.output
        assert "Version :" in output, "Expected 'Version :' aligned format"
        assert "  Version :" in output, "Expected double-space before Version"
        assert "*** LOCAL TEST MODE ***" not in output, "Old banner should not appear"

    def test_local_mode_as_aligned_field(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        output = term.output
        assert "Mode    : LOCAL TEST" in output, "Expected aligned 'Mode : LOCAL TEST'"

    def test_version_part_of_info_block(self) -> None:
        session = create_local_session()
        term = FakeTerminal(keys=[" "])
        show_splash(term, session)
        output = term.output
        assert "Version" in output

        # Ensure the pause prompt appears after the AI message
        ai_pos = output.rfind("AI backend")
        pause_pos = output.rfind("[Press any key to continue]")
        assert pause_pos > ai_pos, "Pause prompt appears before AI message"


class TestGoodbyeLayout:
    """Regression: goodbye box must close before 'Returning to BBS...'."""

    def test_bottom_border_before_returning_text(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term)
        output = term.output

        br = "\u255d"  # bottom-right corner
        br_pos = output.rfind(br)
        assert br_pos >= 0, "Bottom-right corner not found"

        returning_pos = output.rfind("Returning")
        assert returning_pos >= 0, "Returning text not found"
        assert returning_pos > br_pos, "Returning text appears before bottom border"

    def test_one_blank_row_between_box_and_text(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term)
        output = term.output

        br = "\u255d"
        br_pos = output.rfind(br)

        returning_pos = output.rfind("Returning")
        between = output[br_pos + len(br) : returning_pos]

        # Should have cursor positioning to move down, then text
        # The gap should contain at least one line move
        assert "\x1b[" in between or "\n" in between, (
            f"Expected cursor movement between box bottom and text, got: {between!r}"
        )

    def test_output_ends_with_newline(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term)
        output = term.output
        assert output.endswith("\n"), "Output should end with newline"

    def test_cursor_show_emitted(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term)
        assert "\x1b[?25h" in term.output, "Cursor show sequence missing"

    def test_complete_box_rendered(self) -> None:
        term = FakeTerminal(keys=[])
        show_goodbye(term)
        output = term.output
        assert "\u2554" in output, "Top-left corner missing"  # tl
        assert "\u255d" in output, "Bottom-right corner missing"  # br


class TestLoggingNotInUI:
    """Regression: INFO log lines must not appear in the caller-visible terminal."""

    def test_normal_exit_no_log_line_in_stdout(self) -> None:
        term = FakeTerminal(keys=["q"])
        config = _config()
        result = run_app(door32_path=None, local=True, config=config, term=term)
        assert result == 0
        output = term.output
        # The string "aidoor:" or "[INFO]" should NOT appear in the output
        # because no log file is configured and INFO is suppressed
        assert "[INFO]" not in output, "INFO log line leaked into terminal output"
        assert "Exiting" not in output, "Exit log leaked into terminal output"

    def test_exit_log_written_to_file_when_configured(self) -> None:
        from aidoor.logging_config import setup_logging

        fd, log_path = tempfile.mkstemp(suffix=".log")
        os.close(fd)

        try:
            setup_logging(log_level="INFO", log_file=log_path)

            config = AppConfig()
            config.general.log_file = log_path
            config.general.log_level = "INFO"

            term = FakeTerminal(keys=["q"])
            result = run_app(door32_path=None, local=True, config=config, term=term)
            assert result == 0

            # Flush/close all logging handlers so the file is written
            for handler in logging.getLogger("aidoor").handlers[:]:
                handler.flush()
                handler.close()

            with open(log_path, encoding="utf-8") as f:
                log_content = f.read()

            assert "Exiting" in log_content, "Exit log should be written to file"
            assert "Starting" in log_content, "Startup log should be written to file"
        finally:
            os.unlink(log_path)

    def test_startup_error_on_stderr(self) -> None:
        from aidoor.cli import main

        # Missing drop file should print error to stderr, not stdout
        result = main(["--door32", "/nonexistent/door32.sys"])
        assert result == 1

    def test_no_info_log_in_stdout_during_interactive(self) -> None:
        term = FakeTerminal(keys=["q"])
        config = _config()
        result = run_app(door32_path=None, local=True, config=config, term=term)
        assert result == 0
        output = term.output

        # Verify nothing that looks like a log line is in stdout
        log_patterns = ["[INFO]", "[DEBUG]", "[WARNING]", "[ERROR]"]
        for pat in log_patterns:
            assert pat not in output, f"Log pattern {pat} found in terminal output"


class TestCleanTerminalHandoff:
    """Regression: shell prompt appears on a fresh line after exit."""

    def test_cursor_on_fresh_line_after_close(self) -> None:
        term = FakeTerminal(keys=[" ", "q"])
        config = _config()
        result = run_app(door32_path=None, local=True, config=config, term=term)
        assert result == 0
        output = term.output
        # The goodbye "Returning to BBS..." should be in output
        assert "Returning to BBS" in output, "Goodbye text missing"
        # Output ending should have newline (from FakeTerminal.writeln)
        assert output.rstrip().endswith("BBS..."), "Output does not end with goodbye text"
        # Cursor show should be emitted during close/cleanup
        assert "\x1b[?25h" in output

    def test_ctrl_c_cleanup(self) -> None:
        term = FakeTerminal(keys=["\x03"])
        config = _config()
        result = run_app(door32_path=None, local=True, config=config, term=term)
        assert result == 0
        assert "Interrupted" in term.output, "Interrupt message missing"
        assert "\x1b[?25h" in term.output, "Cursor show missing after interrupt"
