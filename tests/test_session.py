from __future__ import annotations

from aidoor.door32 import Door32Data
from aidoor.session import (
    create_local_session,
    create_session_from_door32,
)


def _make_door32(
    alias: str = "Neo",
    real_name: str = "John Doe",
    user_record: int = 42,
) -> Door32Data:
    return Door32Data(
        communication_type="1",
        communication_handle="0",
        baud_rate="38400",
        bbs_software="Mystic BBS",
        user_record=user_record,
        real_name=real_name,
        alias=alias,
        security_level=100,
        time_left_seconds=1800,
        terminal_emulation="ANSI",
        node_number=1,
        raw_lines=(),
    )


class TestCreateSessionFromDoor32:
    def test_uses_alias_as_display_name(self) -> None:
        door32 = _make_door32(alias="Neo", real_name="John Doe")
        session = create_session_from_door32(door32)
        assert session.display_name == "Neo"
        assert session.alias == "Neo"
        assert session.real_name == "John Doe"

    def test_fallback_to_real_name(self) -> None:
        door32 = _make_door32(alias="", real_name="John Doe")
        session = create_session_from_door32(door32)
        assert session.display_name == "John Doe"

    def test_fallback_to_guest(self) -> None:
        door32 = _make_door32(alias="", real_name="")
        session = create_session_from_door32(door32)
        assert session.display_name == "Guest"

    def test_converts_time_left_correctly(self) -> None:
        door32 = _make_door32()
        session = create_session_from_door32(door32)
        assert session.time_left_minutes == 30

    def test_sets_local_mode_false(self) -> None:
        door32 = _make_door32()
        session = create_session_from_door32(door32)
        assert not session.local_mode

    def test_passes_through_fields(self) -> None:
        door32 = _make_door32(
            alias="TestAlias",
            real_name="Test Real",
            user_record=99,
        )
        session = create_session_from_door32(door32)
        assert session.user_id == 99
        assert session.security_level == 100
        assert session.node_number == 1
        assert session.bbs_software == "Mystic BBS"
        assert session.terminal_emulation == "ANSI"

    def test_session_is_immutable(self) -> None:
        door32 = _make_door32()
        session = create_session_from_door32(door32)
        import dataclasses

        assert dataclasses.is_dataclass(session)
        assert session.__dataclass_params__.frozen


class TestCreateLocalSession:
    def test_default_values(self) -> None:
        session = create_local_session()
        assert session.alias == "LocalUser"
        assert session.real_name == "Local User"
        assert session.display_name == "LocalUser"
        assert session.security_level == 255
        assert session.time_left_minutes == 60
        assert session.node_number == 0
        assert session.bbs_software == "Local test mode"
        assert session.terminal_emulation == "ANSI"
        assert session.local_mode

    def test_custom_values(self) -> None:
        session = create_local_session(
            alias="Tester",
            time_left_minutes=30,
            node_number=5,
        )
        assert session.alias == "Tester"
        assert session.display_name == "Tester"
        assert session.time_left_minutes == 30
        assert session.node_number == 5
