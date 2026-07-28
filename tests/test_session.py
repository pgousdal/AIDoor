from __future__ import annotations

import pytest

from aidoor.door32 import Door32Data
from aidoor.session import (
    create_local_session,
    create_session_from_door32,
)


class TestCreateLocalSession:
    def test_default_values(self) -> None:
        session = create_local_session()
        assert session.user_id == 0
        assert session.alias == "LocalUser"
        assert session.display_name == "LocalUser"
        assert session.local_mode

    def test_custom_values(self) -> None:
        session = create_local_session(
            alias="Test",
            real_name="Test User",
            node_number=2,
        )
        assert session.alias == "Test"
        assert session.display_name == "Test"
        assert session.node_number == 2

    def test_display_name_uses_alias(self) -> None:
        session = create_local_session(alias="AliasOnly", real_name="Real Name")
        assert session.display_name == "AliasOnly"

    def test_display_name_falls_back_to_real_name(self) -> None:
        session = create_local_session(alias="", real_name="RealName")
        assert session.display_name == "RealName"

    def test_display_name_falls_back_to_guest(self) -> None:
        session = create_local_session(alias="", real_name="")
        assert session.display_name == "Guest"


class TestCreateSessionFromDoor32:
    def test_converts_door32_data(self) -> None:
        data = Door32Data(
            communication_type="1",
            communication_handle="0",
            baud_rate="9600",
            bbs_software="Test BBS",
            user_record=42,
            real_name="John",
            alias="JohnD",
            security_level=100,
            time_left_seconds=3600,
            terminal_emulation="ANSI",
            node_number=3,
            raw_lines=(),
        )
        session = create_session_from_door32(data)
        assert session.user_id == 42
        assert session.alias == "JohnD"
        assert session.display_name == "JohnD"
        assert session.node_number == 3
        assert session.time_left_minutes == 60
        assert not session.local_mode

    def test_no_local_mode(self) -> None:
        data = Door32Data(
            communication_type="1",
            communication_handle="0",
            baud_rate="9600",
            bbs_software="BBS",
            user_record=1,
            real_name="User",
            alias="U",
            security_level=50,
            time_left_seconds=300,
            terminal_emulation="ANSI",
            node_number=1,
            raw_lines=(),
        )
        session = create_session_from_door32(data)
        assert not session.local_mode


class TestSessionDataclass:
    def test_frozen(self) -> None:
        session = create_local_session()
        with pytest.raises(AttributeError):  # type: ignore[unused-ignore]
            session.alias = "new"  # type: ignore[misc]
