# junoup

A Python script that keeps `junocashd` up to date with the latest GitHub release from [juno-cash/junocash](https://github.com/juno-cash/junocash/releases).

## Features

- Compares local binary version with latest GitHub release
- Automatically downloads and updates the binary when outdated
- Prefers non-debug releases over debug builds
- Uses only Python standard library (no external dependencies)

## Usage

```bash
# Default (looks for ./junocashd)
python junoup.py

# Specify a binary path
python junoup.py /path/to/junocashd
```

## Systemd Service Installation

To install junocashd as a systemd service with auto-update on startup:

```bash
sudo ./setup.sh
```

This will:
- Create a `juno` system user
- Download junoup.py and junocashd to `/home/juno/bin/`
- Create and enable a systemd service that auto-updates before starting

Service management:
```bash
sudo systemctl status juno    # Check status
sudo systemctl stop juno      # Stop service
sudo systemctl restart juno   # Restart (and update)
sudo journalctl -u juno -f    # View logs
```

---

## Claude Code Instructions

- Do not add Claude as co-author in git commit messages
