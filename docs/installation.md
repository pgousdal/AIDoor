# Installation and Mystic BBS setup

## Prerequisites

- Linux server running Mystic BBS v1.12 or later
- Python 3.11 or later installed on the BBS server
- `uv` (recommended) or `pip`

## 1. Install AIDoor

### Option A: Using uv (recommended)

```bash
git clone https://github.com/your-org/aidoor.git /path/to/aidoor
cd /path/to/aidoor
uv sync --all-groups
```

### Option B: Using pip

```bash
git clone https://github.com/your-org/aidoor.git /path/to/aidoor
cd /path/to/aidoor
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## 2. Configure AIDoor

Copy the example configuration:

```bash
cp /path/to/aidoor/config/aidoor.example.toml /path/to/aidoor/config/aidoor.toml
```

Edit `aidoor.toml` as needed. At minimum, set `log_file` to a writable path if you want file logging instead of stderr.

## 3. Mystic BBS configuration

### Create the door in Mystic

1. Open Mystic Config (usually by typing `CONFIG` at the Mystic prompt, or `cd /path/to/mystic && ./mystic -c`).
2. Navigate to **External Programs** (menu option 4, then 1).
3. Add a new door program with these recommended settings:

| Field | Value |
|-------|-------|
| Program Name | `AIDoor` |
| Internal Code | `AIDOOR` |
| Command Line | `/path/to/aidoor/.venv/bin/aidoor --config /path/to/aidoor/config/aidoor.toml --door32 "%PDOOR32.SYS"` |
| Working Directory | `/path/to/aidoor` |
| Drop File Type | `DOOR32` |
| Access Requirements | Set as appropriate for your board |
| Start Page | None |

> **Important**: Verify the exact `%PDOOR32.SYS` variable name in your Mystic version. Some versions use `%DOOR32.SYS` or `%pdoor32.sys`. Check Mystic's door documentation or menu editor for the correct variable.

### Node temporary path

Mystic creates drop files in each node's temporary path. Ensure the node temp path exists and is writable by the Mystic process.

Typical location: `/path/to/mystic/temp/node1/`

The `%PDOOR32.SYS` variable expands to the full path of `DOOR32.SYS` in the node's temp directory.

### File permissions

The Mystic process and the Python interpreter must both be able to read:
- The AIDoor installation directory
- The `aidoor.toml` config file
- The Python virtual environment
- The log file directory (if file logging is configured)

Ensure the Mystic system user (often the same user running Mystic) has appropriate permissions:

```bash
chmod +x /path/to/aidoor/.venv/bin/aidoor
```

### Logging

If `log_file` is set in `aidoor.toml`, ensure the log directory is writable. Example:

```toml
[general]
log_file = "/var/log/aidoor/aidoor.log"
```

```bash
mkdir -p /var/log/aidoor
chown mysticuser:mysticgroup /var/log/aidoor
```

If `log_file` is empty, logs are written to stderr, which Mystic may capture or discard depending on its configuration.

## 4. Test locally before activating

Before configuring the door in Mystic, test locally on the server:

```bash
cd /path/to/aidoor
uv run aidoor --local
```

This starts AIDoor in test mode with dummy session data. Verify that:
- The splash screen displays
- Menu options work (1=About, 2=Session Info, Q=Quit)
- The goodbye screen appears before exit

Then test with an actual DOOR32.SYS if you have one:

```bash
uv run aidoor --door32 /path/to/DOOR32.SYS
```

## 5. Activate in Mystic

After testing, activate the door in Mystic's External Program menu. Place the door in a menu or make it accessible through your BBS's door list.

## 6. Troubleshooting

| Problem | Likely cause |
|---------|-------------|
| Door exits immediately | Drop file path incorrect; test with `--door32` manually |
| "Drop file not found" | `%PDOOR32.SYS` variable not resolving; check Mystic version |
| "Unsupported communication type" | BBS is not using stdin/stdout mode for the door |
| Permission denied | Python or virtual environment not accessible by Mystic user |
| Log file not written | Log directory not writable by Mystic user |
| ANSI screen garbled | Terminal settings in BBS; try setting terminal to ANSI |
