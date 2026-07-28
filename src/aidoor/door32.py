from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from aidoor.errors import DropFileError, UnsupportedCommunicationModeError

_COMMUNICATION_TYPES: dict[str, str] = {
    "1": "stdin/stdout",
    "2": "COM port",
    "3": "Telnet socket",
    "4": "SSH",
    "5": "Local/Named pipe",
}

_SUPPORTED_COMM_TYPES = {"1"}

# Number of required lines in DOOR32.SYS
_REQUIRED_LINES = 11


@dataclasses.dataclass(frozen=True)
class Door32Data:
    communication_type: str
    communication_handle: str
    baud_rate: str
    bbs_software: str
    user_record: int
    real_name: str
    alias: str
    security_level: int
    time_left_seconds: int
    terminal_emulation: str
    node_number: int
    raw_lines: tuple[str, ...]


def parse_door32_file(path: str | Path) -> Door32Data:
    filepath = Path(path)
    if not filepath.exists():
        raise DropFileError(f"Drop file not found: {filepath}")
    if not filepath.is_file():
        raise DropFileError(f"Not a regular file: {filepath}")

    try:
        raw_text = filepath.read_bytes()
    except OSError as exc:
        raise DropFileError(f"Cannot read drop file: {exc}") from exc

    if not raw_text.strip():
        raise DropFileError("Drop file is empty")

    return _parse_door32_lines(raw_text.decode("utf-8", errors="replace").splitlines())


def _parse_door32_lines(lines: list[str]) -> Door32Data:
    if len(lines) < _REQUIRED_LINES:
        raise DropFileError(
            f"Drop file has {len(lines)} line(s), expected at least {_REQUIRED_LINES}"
        )

    comm_type = lines[0].strip()

    if comm_type not in _SUPPORTED_COMM_TYPES:
        label = _COMMUNICATION_TYPES.get(comm_type, f"unknown ({comm_type})")
        raise UnsupportedCommunicationModeError(
            f"Unsupported communication type: {label}. "
            f"Only stdin/stdout (type 1) is supported in M0."
        )

    comm_handle = lines[1].strip()
    baud_rate = lines[2].strip()
    bbs_software = _sanitize_text(lines[3])

    user_record = _parse_int_field(lines[4], "user record")

    real_name = _sanitize_text(lines[5])
    alias = _sanitize_text(lines[6])

    security_level = _parse_int_field(lines[7], "security level")
    time_left_seconds = _parse_int_field(lines[8], "time left")
    if time_left_seconds < 0:
        raise DropFileError(f"Negative time left value: {time_left_seconds}")

    terminal_emulation = _sanitize_text(lines[9])
    node_number = _parse_int_field(lines[10], "node number")

    return Door32Data(
        communication_type=comm_type,
        communication_handle=comm_handle,
        baud_rate=baud_rate,
        bbs_software=bbs_software,
        user_record=user_record,
        real_name=real_name,
        alias=alias,
        security_level=security_level,
        time_left_seconds=time_left_seconds,
        terminal_emulation=terminal_emulation,
        node_number=node_number,
        raw_lines=tuple(lines),
    )


def _parse_int_field(value: str, field_name: str) -> int:
    stripped = value.strip()
    if not stripped:
        raise DropFileError(f"Empty {field_name} field")
    try:
        return int(stripped)
    except ValueError as exc:
        raise DropFileError(f"Invalid {field_name}: {value!r} is not a valid integer") from exc


_REMOVE_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _sanitize_text(value: str) -> str:
    result = _REMOVE_CONTROL.sub("", value)
    return result.strip().replace("\r", "").replace("\n", " ").replace("\t", " ")
