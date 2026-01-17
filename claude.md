# upjunod

A Python script that checks if a local `junocashd` binary version matches the latest GitHub release from [juno-cash/junocash](https://github.com/juno-cash/junocash/releases).

## Features

- Compares local binary version with latest GitHub release
- Automatically downloads and extracts the Linux amd64 binary if not present
- Prefers non-debug releases over debug builds
- Uses only Python standard library (no external dependencies)

## Usage

```bash
# Default (looks for ./junocashd)
python version_checker.py

# Specify a binary path
python version_checker.py /path/to/junocashd
```

---

## Claude Code Instructions

- Do not add Claude as co-author in git commit messages
