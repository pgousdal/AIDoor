from __future__ import annotations

import os
import tempfile

import pytest

from aidoor.door32 import parse_door32_file
from aidoor.errors import DropFileError, UnsupportedCommunicationModeError

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _write_sys(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".sys")
    os.write(fd, content.encode("utf-8"))
    os.close(fd)
    return path


class TestParseDoor32Stdio:
    def test_valid_stdio(self) -> None:
        path = os.path.join(FIXTURES, "door32_stdio.sys")
        data = parse_door32_file(path)
        assert data.communication_type == "1"
        assert data.communication_handle == "0"
        assert data.baud_rate == "38400"
        assert data.bbs_software == "Mystic BBS v1.12 A39"
        assert data.user_record == 42
        assert data.real_name == "John Doe"
        assert data.alias == "Neo"
        assert data.security_level == 100
        assert data.time_left_seconds == 1800
        assert data.terminal_emulation == "ANSI"
        assert data.node_number == 1

    def test_crlf_handling(self) -> None:
        content = "1\r\n0\r\n9600\r\nTest BBS\r\n1\r\nUser\r\nAlias\r\n50\r\n300\r\nANSI\r\n2\r\n"
        path = _write_sys(content)
        try:
            data = parse_door32_file(path)
            assert data.communication_type == "1"
            assert data.alias == "Alias"
        finally:
            os.unlink(path)

    def test_lf_handling(self) -> None:
        content = "1\n0\n9600\nTest BBS\n1\nUser\nAlias\n50\n300\nANSI\n2\n"
        path = _write_sys(content)
        try:
            data = parse_door32_file(path)
            assert data.communication_type == "1"
            assert data.alias == "Alias"
        finally:
            os.unlink(path)

    def test_extra_lines_preserved(self) -> None:
        content = "1\n0\n9600\nTest BBS\n1\nUser\nAlias\n50\n300\nANSI\n1\nextra1\nextra2\n"
        path = _write_sys(content)
        try:
            data = parse_door32_file(path)
            assert len(data.raw_lines) == 13
            assert data.raw_lines[11] == "extra1"
            assert data.raw_lines[12] == "extra2"
        finally:
            os.unlink(path)

    def test_socket_file_raises_error(self) -> None:
        path = os.path.join(FIXTURES, "door32_socket.sys")
        with pytest.raises(UnsupportedCommunicationModeError) as exc:
            parse_door32_file(path)
        assert "Telnet socket" in str(exc.value)

    def test_missing_required_lines(self) -> None:
        content = "1\n0\n9600\nTest BBS\n1\nUser\n"
        path = _write_sys(content)
        try:
            with pytest.raises(DropFileError, match="expected at least"):
                parse_door32_file(path)
        finally:
            os.unlink(path)

    def test_invalid_integer(self) -> None:
        path = os.path.join(FIXTURES, "door32_invalid.sys")
        with pytest.raises(DropFileError, match="not a valid integer"):
            parse_door32_file(path)

    def test_missing_file(self) -> None:
        with pytest.raises(DropFileError, match="not found"):
            parse_door32_file("/nonexistent/door32.sys")

    def test_empty_file(self) -> None:
        path = _write_sys("")
        try:
            with pytest.raises(DropFileError, match="empty"):
                parse_door32_file(path)
        finally:
            os.unlink(path)

    def test_control_chars_in_text(self) -> None:
        content = "1\n0\n9600\nTest\n1\n\x00Us\x1ber\nAli\x00as\n50\n300\nANSI\n1\n"
        path = _write_sys(content)
        try:
            data = parse_door32_file(path)
            assert "\x00" not in data.real_name
            assert "\x00" not in data.alias
        finally:
            os.unlink(path)

    def test_negative_time_left(self) -> None:
        content = "1\n0\n9600\nTest\n1\nUser\nAlias\n50\n-100\nANSI\n1\n"
        path = _write_sys(content)
        try:
            with pytest.raises(DropFileError, match="Negative"):
                parse_door32_file(path)
        finally:
            os.unlink(path)
