from __future__ import annotations

import dataclasses

from aidoor.door32 import Door32Data


@dataclasses.dataclass(frozen=True)
class Session:
    user_id: int
    alias: str
    real_name: str
    display_name: str
    security_level: int
    time_left_minutes: int
    node_number: int
    bbs_software: str
    terminal_emulation: str
    local_mode: bool


def _resolve_display_name(alias: str, real_name: str) -> str:
    if alias:
        return alias
    if real_name:
        return real_name
    return "Guest"


def create_session_from_door32(data: Door32Data) -> Session:
    return Session(
        user_id=data.user_record,
        alias=data.alias,
        real_name=data.real_name,
        display_name=_resolve_display_name(data.alias, data.real_name),
        security_level=data.security_level,
        time_left_minutes=data.time_left_seconds // 60,
        node_number=data.node_number,
        bbs_software=data.bbs_software,
        terminal_emulation=data.terminal_emulation,
        local_mode=False,
    )


def create_local_session(
    alias: str = "LocalUser",
    real_name: str = "Local User",
    security_level: int = 255,
    time_left_minutes: int = 60,
    node_number: int = 0,
    bbs_software: str = "Local test mode",
    terminal_emulation: str = "ANSI",
) -> Session:
    return Session(
        user_id=0,
        alias=alias,
        real_name=real_name,
        display_name=_resolve_display_name(alias, real_name),
        security_level=security_level,
        time_left_minutes=time_left_minutes,
        node_number=node_number,
        bbs_software=bbs_software,
        terminal_emulation=terminal_emulation,
        local_mode=True,
    )
