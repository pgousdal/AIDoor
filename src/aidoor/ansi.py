from __future__ import annotations

import dataclasses
import re

_CSI = "\x1b["

RESET = f"{_CSI}0m"
BOLD = f"{_CSI}1m"
CLEAR = f"{_CSI}2J"
HOME = f"{_CSI}H"
CURSOR_HIDE = f"{_CSI}?25l"
CURSOR_SHOW = f"{_CSI}?25h"

BLACK = f"{_CSI}30m"
RED = f"{_CSI}31m"
GREEN = f"{_CSI}32m"
YELLOW = f"{_CSI}33m"
BLUE = f"{_CSI}34m"
MAGENTA = f"{_CSI}35m"
CYAN = f"{_CSI}36m"
WHITE = f"{_CSI}37m"


def cursor_pos(row: int, col: int) -> str:
    return f"{_CSI}{row};{col}H"


def colorize(text: str, color_code: str, bold: bool = False) -> str:
    prefix = BOLD if bold else ""
    return f"{prefix}{color_code}{text}{RESET}"


_STRIP_SEQUENCES = re.compile(r"\x1b\[[\d;]*[A-Za-z]")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_ansi(text: str) -> str:
    return _STRIP_SEQUENCES.sub("", text)


def sanitize_text(text: str) -> str:
    result = _STRIP_SEQUENCES.sub("", text)
    result = _CONTROL_CHARS.sub("", result)
    result = result.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in result.split("\n"):
        lines.append(line.replace("\t", " ").rstrip())
    return "\n".join(lines)


@dataclasses.dataclass(frozen=True)
class BoxChars:
    tl: str
    tr: str
    bl: str
    br: str
    h: str
    v: str
    lm: str
    rm: str
    h_light: str


UNICODE_BOX = BoxChars(
    tl="\u2554",
    tr="\u2557",
    bl="\u255a",
    br="\u255d",
    h="\u2550",
    v="\u2551",
    lm="\u2560",
    rm="\u2563",
    h_light="\u2500",
)

CP437_BOX = BoxChars(
    tl="\xc9",
    tr="\xbb",
    bl="\xc8",
    br="\xbc",
    h="\xcd",
    v="\xba",
    lm="\xcc",
    rm="\xb9",
    h_light="\xc4",
)

VALID_CHARSETS: dict[str, BoxChars] = {
    "unicode": UNICODE_BOX,
    "cp437": CP437_BOX,
}


def resolve_charset(name: str) -> BoxChars:
    result = VALID_CHARSETS.get(name.lower())
    if result is None:
        raise ValueError(f"Unknown charset: {name!r}. Valid: {', '.join(VALID_CHARSETS)}")
    return result


def _pad_to(content: str, width: int) -> str:
    if len(content) >= width:
        return content[:width]
    return content + " " * (width - len(content))


@dataclasses.dataclass(frozen=True)
class RenderBounds:
    top: int
    left: int
    width: int
    height: int

    @property
    def bottom(self) -> int:
        return self.top + self.height - 1

    @property
    def next_row(self) -> int:
        return self.bottom + 1


def draw_box(
    x: int,
    y: int,
    width: int,
    height: int,
    title: str = "",
    charset: BoxChars = UNICODE_BOX,
) -> tuple[str, RenderBounds]:
    if x < 1:
        raise ValueError(f"Box x must be >= 1, got {x}")
    if y < 1:
        raise ValueError(f"Box y must be >= 1, got {y}")
    if width < 4:
        raise ValueError(f"Box width must be >= 4, got {width}")
    if height < 3:
        raise ValueError(f"Box height must be >= 3, got {height}")

    inner = width - 2
    parts: list[str] = []

    for row in range(height):
        parts.append(cursor_pos(y + row, x))
        if row == 0:
            parts.append(charset.tl + charset.h * inner + charset.tr)
        elif row == height - 1:
            parts.append(charset.bl + charset.h * inner + charset.br)
        else:
            parts.append(charset.v + " " * inner + charset.v)

    if title:
        title_row = y + 1
        centered = _pad_to(title.center(inner), inner)
        parts.append(cursor_pos(title_row, x) + charset.v + centered + charset.v)

    bounds = RenderBounds(top=y, left=x, width=width, height=height)
    return ("".join(parts), bounds)


def draw_box_separator(
    y: int,
    x: int,
    width: int,
    charset: BoxChars = UNICODE_BOX,
) -> str:
    if width < 4:
        raise ValueError(f"Separator width must be >= 4, got {width}")
    inner = width - 2
    return cursor_pos(y, x) + charset.lm + charset.h * inner + charset.rm


def draw_box_content_line(
    y: int,
    x: int,
    width: int,
    content: str,
    charset: BoxChars = UNICODE_BOX,
) -> str:
    if width < 4:
        raise ValueError(f"Content line width must be >= 4, got {width}")
    inner = width - 2
    padded = _pad_to(content, inner)
    return cursor_pos(y, x) + charset.v + padded + charset.v


def draw_box_title_line(
    y: int,
    x: int,
    width: int,
    title: str,
    charset: BoxChars = UNICODE_BOX,
) -> str:
    return draw_box_content_line(y, x, width, title.center(width - 2), charset)
