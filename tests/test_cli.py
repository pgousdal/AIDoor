from __future__ import annotations

import os
import tempfile

import pytest

from aidoor.cli import main


class TestCliArgumentParsing:
    def test_version(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0

    def test_help(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_no_mode_specified(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2

    def test_conflicting_modes(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--local", "--door32", "/tmp/test.sys"])
        assert exc.value.code == 2

    def test_door32_missing_file_returns_1(self) -> None:
        result = main(["--door32", "/nonexistent/door32.sys"])
        assert result == 1

    def test_invalid_door32_file_returns_1(self) -> None:
        content = "3\n0\n9600\nTest\n1\nUser\nAlias\n50\n300\nANSI\n1\n"
        fd, path = tempfile.mkstemp(suffix=".sys")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            result = main(["--door32", path])
            assert result == 1
        finally:
            os.unlink(path)
