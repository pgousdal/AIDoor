from __future__ import annotations

import pytest

from aidoor.ansi import (
    CP437_BOX,
    UNICODE_BOX,
    cursor_pos,
    draw_box,
    draw_box_content_line,
    draw_box_separator,
    resolve_charset,
)


def _box_str(*args: object, **kwargs: object) -> str:
    """Call draw_box and return only the string part."""
    result, _ = draw_box(*args, **kwargs)  # type: ignore[arg-type]
    return result


class TestBoxChars:
    def test_unicode_box_chars(self) -> None:
        assert UNICODE_BOX.tl == "\u2554"
        assert UNICODE_BOX.tr == "\u2557"
        assert UNICODE_BOX.bl == "\u255a"
        assert UNICODE_BOX.br == "\u255d"
        assert UNICODE_BOX.h == "\u2550"
        assert UNICODE_BOX.v == "\u2551"
        assert UNICODE_BOX.lm == "\u2560"
        assert UNICODE_BOX.rm == "\u2563"
        assert UNICODE_BOX.h_light == "\u2500"

    def test_cp437_box_chars(self) -> None:
        assert CP437_BOX.tl == "\xc9"
        assert CP437_BOX.tr == "\xbb"
        assert CP437_BOX.bl == "\xc8"
        assert CP437_BOX.br == "\xbc"
        assert CP437_BOX.h == "\xcd"
        assert CP437_BOX.v == "\xba"
        assert CP437_BOX.lm == "\xcc"
        assert CP437_BOX.rm == "\xb9"
        assert CP437_BOX.h_light == "\xc4"


class TestResolveCharset:
    def test_unicode(self) -> None:
        assert resolve_charset("unicode") is UNICODE_BOX

    def test_cp437(self) -> None:
        assert resolve_charset("cp437") is CP437_BOX

    def test_case_insensitive(self) -> None:
        assert resolve_charset("UNICODE") is UNICODE_BOX
        assert resolve_charset("CP437") is CP437_BOX

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown charset"):
            resolve_charset("utf8")


class TestDrawBox:
    def test_minimum_dimensions(self) -> None:
        result = _box_str(1, 1, 4, 3)
        assert cursor_pos(1, 1) + UNICODE_BOX.tl in result
        assert cursor_pos(3, 1) + UNICODE_BOX.bl in result

    def test_top_border_right_corner(self) -> None:
        result = _box_str(1, 1, 10, 5)
        expected_top = cursor_pos(1, 1) + UNICODE_BOX.tl + UNICODE_BOX.h * 8 + UNICODE_BOX.tr
        assert expected_top in result

    def test_bottom_border_right_corner(self) -> None:
        result = _box_str(1, 1, 10, 5)
        expected_bottom = cursor_pos(5, 1) + UNICODE_BOX.bl + UNICODE_BOX.h * 8 + UNICODE_BOX.br
        assert expected_bottom in result

    def test_vertical_borders(self) -> None:
        result = _box_str(1, 1, 4, 4)
        for row in range(2, 4):
            expected = cursor_pos(row, 1) + UNICODE_BOX.v + "  " + UNICODE_BOX.v
            assert expected in result

    def test_title_centered(self) -> None:
        result = _box_str(1, 1, 20, 5, title="Hello")
        assert "Hello" in result
        # Title line starts with vertical bar then spaces (centered padding)
        title_marker = cursor_pos(2, 1) + UNICODE_BOX.v
        assert title_marker in result

    def test_validates_x(self) -> None:
        with pytest.raises(ValueError, match="x"):
            draw_box(0, 1, 10, 5)

    def test_validates_y(self) -> None:
        with pytest.raises(ValueError, match="y"):
            draw_box(1, 0, 10, 5)

    def test_validates_width_too_small(self) -> None:
        with pytest.raises(ValueError, match="width"):
            draw_box(1, 1, 3, 5)

    def test_validates_height_too_small(self) -> None:
        with pytest.raises(ValueError, match="height"):
            draw_box(1, 1, 10, 2)

    def test_no_title_leaves_row_2_empty(self) -> None:
        result = _box_str(1, 1, 10, 5)
        row2 = cursor_pos(2, 1) + UNICODE_BOX.v + " " * 8 + UNICODE_BOX.v
        assert row2 in result


class TestDrawBoxSeparator:
    def test_uses_lm_and_rm(self) -> None:
        result = draw_box_separator(3, 1, 20)
        assert cursor_pos(3, 1) in result
        assert UNICODE_BOX.lm in result
        assert UNICODE_BOX.rm in result

    def test_validates_width(self) -> None:
        with pytest.raises(ValueError, match="width"):
            draw_box_separator(3, 1, 3)


class TestDrawBoxContentLine:
    def test_content_padded(self) -> None:
        result = draw_box_content_line(4, 1, 20, "Hi")
        assert cursor_pos(4, 1) in result
        assert UNICODE_BOX.v in result
        assert "Hi" in result

    def test_content_truncated(self) -> None:
        result = draw_box_content_line(4, 1, 10, "Hello World Long")
        inner = 10 - 2
        truncated = "Hello Wo"
        assert len(truncated) == inner
        assert truncated in result

    def test_empty_content(self) -> None:
        result = draw_box_content_line(4, 1, 10, "")
        expected = cursor_pos(4, 1) + UNICODE_BOX.v + " " * 8 + UNICODE_BOX.v
        assert expected in result

    def test_validates_width(self) -> None:
        with pytest.raises(ValueError, match="width"):
            draw_box_content_line(4, 1, 3, "x")


class TestBoxDimensions:
    def test_borders_align_perfectly(self) -> None:
        for width in range(4, 20):
            for height in range(3, 10):
                result = _box_str(1, 1, width, height)
                inner = width - 2
                # Top border should have exactly inner h-chars
                top_part = UNICODE_BOX.tl + UNICODE_BOX.h * inner + UNICODE_BOX.tr
                assert top_part in result, f"Top border broken for {width}x{height}"
                # Bottom should match
                bot_part = UNICODE_BOX.bl + UNICODE_BOX.h * inner + UNICODE_BOX.br
                assert bot_part in result, f"Bottom border broken for {width}x{height}"
                # Each content row should have v + inner spaces + v
                for r in range(2, height):
                    row_part = UNICODE_BOX.v + " " * inner + UNICODE_BOX.v
                    pos = cursor_pos(r, 1)
                    assert pos + row_part in result, f"Content row {r} broken for {width}x{height}"

    def test_no_duplicate_border_chars(self) -> None:
        result = _box_str(1, 1, 10, 5)
        for char in (UNICODE_BOX.tl, UNICODE_BOX.tr, UNICODE_BOX.bl, UNICODE_BOX.br):
            assert result.count(char) == 1, f"Duplicate {char!r} in output"

    def test_vertical_bars_count(self) -> None:
        result = _box_str(1, 1, 6, 5)
        # Top and bottom have corner chars (not v), middle 3 rows have 2 v each
        assert result.count(UNICODE_BOX.v) == 6


class TestDrawBoxCP437:
    def test_cp437_borders(self) -> None:
        result = _box_str(1, 1, 10, 5, charset=CP437_BOX)
        top = cursor_pos(1, 1) + CP437_BOX.tl + CP437_BOX.h * 8 + CP437_BOX.tr
        assert top in result

    def test_cp437_bottom_right_correct(self) -> None:
        result = _box_str(1, 1, 10, 5, charset=CP437_BOX)
        bot = cursor_pos(5, 1) + CP437_BOX.bl + CP437_BOX.h * 8 + CP437_BOX.br
        assert bot in result
        # Verify no Unicode box chars leak in
        assert UNICODE_BOX.tl not in result
