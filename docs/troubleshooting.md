# Troubleshooting

## Quick Diagnosis

Run the doctor command:

```bash
uv run aidoor doctor
```

This checks Python version, configuration, terminal size, log file writability,
Ollama connectivity, and model availability.

## Common Issues

### "Cannot connect to Ollama"

**Cause:** Ollama server is not running or not reachable.

**Solution:**

```bash
# Check if Ollama is running
systemctl status ollama

# Start Ollama
ollama serve

# Verify connectivity
curl http://localhost:11434/api/version
```

If Ollama is on a different host, update `ollama.host` in the config file.

### "Configured model 'llama3.1' not installed"

**Cause:** The model specified in the configuration is not available on the server.

**Solution:**

```bash
# List installed models
uv run aidoor models

# Pull the model
ollama pull llama3.1

# Or change the model in the config file
```

### "Configuration error"

**Cause:** Invalid TOML syntax or invalid field values.

**Solution:** Check the configuration file for:
- Invalid TOML syntax (run `python3 -m tomllib your-config.toml`)
- Invalid log level (must be: DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Invalid charset (must be: unicode, cp437)
- Terminal width outside 40-999 range
- Terminal height outside 10-200 range
- Ollama timeout outside 1-600 range
- Invalid Ollama URL (must start with http:// or https://)
- Empty model name

### "Terminal width below minimum"

**Cause:** The terminal (or the DOOR32.SYS file) reports a width below 40 columns.

**Solution:** Ensure the telnet/SSH client is set to at least 80 columns. For
Mystic, check the terminal emulation settings.

### "Log file not writable"

**Cause:** The configured log file path is not writable by the AIDoor process.

**Solution:**

```bash
# Create log directory with correct permissions
sudo mkdir -p /var/log/aidoor
sudo chown mystic:mystic /var/log/aidoor

# Or disable logging by setting log_file to empty in the config
```

### "Drop file not found"

**Cause:** The DOOR32.SYS path passed with `--door32` does not exist.

**Solution:** Verify the door configuration in Mystic. The `%DROP%` variable
must resolve to a valid path. Run the door manually to test:

```bash
uv run aidoor run --door32 /path/to/DOOR32.SYS
```

### "Unsupported communication type"

**Cause:** The DOOR32.SYS file specifies a communication type other than
stdin/stdout (type 1).

**Solution:** Ensure Mystic is configured for stdin/stdout communication.
Types 2-5 (COM port, Telnet socket, SSH, Named pipe) are not supported.

### "Connection refused"

**Cause:** Ollama is not listening on the expected port.

**Solution:**

```bash
# Check if Ollama is listening
ss -tlnp | grep 11434

# If not, start Ollama
ollama serve
```

### No output in terminal

**Cause:** Terminal emulation issues or ANSI support problems.

**Solution:**
- Ensure your terminal supports ANSI escape sequences
- Try setting `ansi = false` in the config file
- Check that the BBS software passes through ANSI codes

## Logs

When `log_file` is configured in the config file, AIDoor writes debug and
error information to the log file. Check the log for detailed error messages:

```bash
tail -f /var/log/aidoor.log
```

## Getting Help

If you encounter issues not covered here, please open an issue on the
project repository with:
- The output of `uv run aidoor doctor`
- The AIDoor version (`uv run aidoor version`)
- Relevant log file entries
- Your configuration (with secrets removed)
- Steps to reproduce the problem
