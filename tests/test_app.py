from __future__ import annotations

import os
import tempfile

from aidoor.app import run_app
from aidoor.config import AppConfig
from aidoor.terminal import FakeTerminal


def _config() -> AppConfig:
    return AppConfig()


class TestRunAppLocal:
    def test_local_exits_cleanly(self) -> None:
        term = FakeTerminal(keys=["q"])
        result = run_app(door32_path=None, local=True, config=_config(), term=term)
        assert result == 0
        assert "AIDoor" in term.output
        assert "Local test mode" in term.output

    def test_local_shows_menu_and_about(self) -> None:
        term = FakeTerminal(keys=["1", " ", "q"])
        result = run_app(door32_path=None, local=True, config=_config(), term=term)
        assert result == 0
        assert "About" in term.output

    def test_local_shows_session_info(self) -> None:
        term = FakeTerminal(keys=["2", " ", "q"])
        result = run_app(door32_path=None, local=True, config=_config(), term=term)
        assert result == 0
        assert "LocalUser" in term.output


class TestRunAppDoor32:
    def test_valid_door32_exits_cleanly(self) -> None:
        content = "1\n0\n9600\nTest BBS\n1\nUser\nAlias\n50\n300\nANSI\n1\n"
        fd, path = tempfile.mkstemp(suffix=".sys")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            term = FakeTerminal(keys=["q"])
            result = run_app(door32_path=path, local=False, config=_config(), term=term)
            assert result == 0
            assert "Test BBS" in term.output
        finally:
            os.unlink(path)


class TestRunAppKeyboardInterrupt:
    def test_ctrl_c_handled(self) -> None:
        term = FakeTerminal(keys=["\x03"])
        result = run_app(door32_path=None, local=True, config=_config(), term=term)
        assert result == 0
        assert "Interrupted" in term.output
