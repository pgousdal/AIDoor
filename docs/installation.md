# Installation

## Requirements

- **Python** 3.11 or later
- **uv** package manager (recommended) or pip
- **Ollama** server (local or network)

## Linux Install

### 1. Install Python

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install python3 python3-venv python3-pip

# RHEL/CentOS/Fedora
sudo dnf install python3 python3-venv python3-pip

# Arch
sudo pacman -S python python-pip
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your shell or run:

```bash
source ~/.bashrc
```

### 3. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 4. Pull a model

```bash
ollama pull llama3.1
```

### 5. Download AIDoor

```bash
git clone https://github.com/your-org/aidoor.git
cd aidoor
uv sync
```

### 6. Verify Installation

```bash
uv run aidoor doctor
```

If everything is configured correctly, you should see:

```
  ✓ package version
      ✓ AIDoor 0.2.1
  ✓ python version
      ✓ Python 3.12
  ...
  All checks passed.
```

### 7. Start Ollama (if not running)

```bash
ollama serve
```

### 8. Run in local mode

```bash
uv run aidoor run --local
```

## Alternative: pip install

If you don't have git, you can install directly from the release archive:

```bash
# Download the wheel from the releases page
pip install aidoor-0.2.1-py3-none-any.whl

# Or install from source
pip install aidoor-0.2.1.tar.gz
```

After pip install, the `aidoor` command is available globally:

```bash
aidoor run --local
aidoor doctor
aidoor models
aidoor version
```

## Configuration

AIDoor works without configuration, but for custom settings:

```bash
mkdir -p /etc/aidoor
cp examples/example-config.toml /etc/aidoor/config.toml
# Edit the file to suit your environment
```

Pass the config file when running:

```bash
uv run aidoor run --local --config /etc/aidoor/config.toml
```
