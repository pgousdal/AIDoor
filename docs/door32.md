# DOOR32.SYS format

## Overview

`DOOR32.SYS` is the standard drop-file format used by Mystic BBS (and other BBS software) to pass session information to external door programs. AIDoor reads this file on startup when not in local mode.

## File format

The file is a plain text file with **11 required lines**, each terminated by CRLF or LF:

| Line | Field               | Type    | Description |
|------|----------------------|---------|-------------|
| 1    | Communication type   | int     | 1=stdin/stdout, 2=COM port, 3=Telnet socket, 4=SSH, 5=Local pipe |
| 2    | Communication handle | string  | Socket descriptor, COM handle, or similar |
| 3    | Baud rate            | string  | Connection speed (e.g. 38400, 115200) |
| 4    | BBS software         | string  | BBS name and version |
| 5    | User record          | int     | Internal user number |
| 6    | Real name            | string  | User's real name |
| 7    | Alias                | string  | User's handle / alias |
| 8    | Security level       | int     | Access level (higher = more access) |
| 9    | Time left            | int     | Time remaining in **seconds** |
| 10   | Terminal emulation   | string  | "ANSI", "VT100", etc. |
| 11   | Node number          | int     | Current BBS node |

Additional lines beyond line 11 are preserved in `Door32Data.raw_lines` for diagnostic purposes.

## Communication types

AIDoor M0 supports only type 1 (stdin/stdout). Attempting to use another type raises `UnsupportedCommunicationModeError`.

## Example

```
1
0
38400
Mystic BBS v1.12 A39
42
John Doe
Neo
100
1800
ANSI
1
```

## Implementation notes

- The file is read as bytes and decoded as UTF-8 with replacement for invalid sequences.
- All text fields are sanitised: control characters (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, 0x7F) are removed, CR/LF are replaced with spaces, tabs are replaced with spaces, and leading/trailing whitespace is stripped.
- Integer fields are parsed with explicit validation; empty or non-integer values produce a `DropFileError`.
- Negative values in the time-left field are rejected.
