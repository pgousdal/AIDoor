# Mystic BBS Integration

## Overview

AIDoor runs as a Mystic door using the standard DOOR32.SYS drop file interface.
When a user selects the door from Mystic's menu, Mystic creates a DOOR32.SYS file
with session information and launches AIDoor.

## Mystic Menu Entry

1. Log in to Mystic as the SysOp.
2. Navigate to **Main Menu Editor** (MEdit).
3. Add a new menu entry or edit an existing one.
4. Set the **Command** to:

```bash
/path/to/aidoor/examples/run-mystic.sh %DROP%
```

Or, if `aidoor` is installed globally via pip:

```bash
aidoor run --door32 %DROP%
```

5. Set **Drop File** to `DOOR32.SYS` (or the path Mystic uses).
6. Set **Door Type** to `Door` or `StdI/O` depending on Mystic version.
7. Set **Access Requirements** as needed.
8. Save and test.

## DOOR32.SYS

The DOOR32.SYS drop file provides:
- Communication type (must be `1` for stdin/stdout)
- Node number
- User alias and real name
- Security level
- Time remaining
- BBS software name
- Terminal emulation

AIDoor validates these fields on startup. If any field is invalid,
an error message is displayed and the door exits cleanly.

## Permissions

The user running AIDoor must have:
- Read access to the DOOR32.SYS file
- Read/write access to the log file directory (if configured)
- Network access to the Ollama server
- Execute access to the Python environment

For Mystic installations:

```bash
# Ensure the Mystic user can access the project
chown -R mystic:mystic /path/to/aidoor

# Create log directory
mkdir -p /var/log/aidoor
chown mystic:mystic /var/log/aidoor
```

## Environment Variables

- `AIDOOR_CONFIG` — Path to configuration file (optional)

## Troubleshooting Mystic Integration

**Door starts but shows no output**
: Verify the drop file path. Mystic must expand `%DROP%` correctly.

**"Unsupported communication type"**
: Ensure Mystic is configured for stdin/stdout communication.

**"Drop file not found"**
: The DOOR32.SYS path is incorrect. Check Mystic's door configuration.
