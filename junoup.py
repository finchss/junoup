#!/usr/bin/env python3
"""
Version checker script that compares local junocashd version
with the latest GitHub release. Downloads and extracts if binary doesn't exist.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import json
from pathlib import Path


def get_local_version(binary_path: str) -> str:
    """Run the binary with '--version' argument and extract version string."""
    try:
        result = subprocess.run(
            [binary_path, "--version"],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip() or result.stderr.strip()

        # Try to extract version pattern (e.g., v1.2.3 or 1.2.3)
        version_match = re.search(r'v?(\d+\.\d+\.\d+)', output)
        if version_match:
            return version_match.group(0)

        # If no pattern found, return the raw output
        return output
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running binary: {e}", file=sys.stderr)
        sys.exit(1)


def get_latest_github_release(repo: str) -> dict:
    """Fetch the latest release info from GitHub API."""
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        request = urllib.request.Request(
            api_url,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: Repository '{repo}' not found or has no releases", file=sys.stderr)
        else:
            print(f"Error fetching GitHub release: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching GitHub release: {e}", file=sys.stderr)
        sys.exit(1)


def normalize_version(version: str) -> str:
    """Normalize version string for comparison (remove 'v' prefix)."""
    return version.lstrip('v').strip()


def find_linux_amd64_asset(assets: list) -> dict | None:
    """Find the Linux amd64/x86_64 asset from release assets, preferring non-debug."""
    candidates = []
    for asset in assets:
        name = asset.get('name', '').lower()
        # Check if it's a Linux amd64 binary (not checksum file)
        if 'linux' in name and ('amd64' in name or 'x86_64' in name or 'linux64' in name):
            if not name.endswith(('.sha256', '.md5', '.sig', '.asc')):
                candidates.append(asset)

    if not candidates:
        return None

    # Prefer non-debug version
    for asset in candidates:
        if 'debug' not in asset.get('name', '').lower():
            return asset

    # Fall back to debug version
    return candidates[0]


def download_and_extract(url: str, dest_dir: str, binary_name: str) -> str:
    """Download and extract the archive, return path to the binary."""
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    archive_name = url.split('/')[-1]
    archive_path = dest_path / archive_name

    print(f"Downloading {archive_name}...")
    try:
        urllib.request.urlretrieve(url, archive_path)
    except Exception as e:
        print(f"Error downloading: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting to {dest_dir}...")
    try:
        if archive_name.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=dest_path)
        elif archive_name.endswith('.tar'):
            with tarfile.open(archive_path, 'r:') as tar:
                tar.extractall(path=dest_path)
        else:
            print(f"Unsupported archive format: {archive_name}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error extracting: {e}", file=sys.stderr)
        sys.exit(1)

    # Clean up archive
    archive_path.unlink()

    # Find the binary in extracted files
    binary_path = find_binary(dest_path, binary_name)
    if binary_path:
        # Make it executable
        os.chmod(binary_path, 0o755)
        print(f"Binary extracted to: {binary_path}")
        return str(binary_path)

    print(f"Error: Could not find {binary_name} in extracted archive", file=sys.stderr)
    sys.exit(1)


def find_binary(search_dir: Path, binary_name: str) -> str | None:
    """Find the binary in the extracted directory."""
    # First check direct path
    direct = search_dir / binary_name
    if direct.exists():
        return str(direct)

    # Search recursively for exact match
    for path in search_dir.rglob(binary_name):
        if path.is_file():
            return str(path)

    # Try with .dbg suffix (debug builds)
    for path in search_dir.rglob(f"{binary_name}.dbg"):
        if path.is_file():
            return str(path)

    # Also try common variations
    for path in search_dir.rglob(f"*{binary_name}*"):
        if path.is_file() and path.suffix in ('', '.dbg'):
            return str(path)

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Compare local junocashd version with latest GitHub release"
    )
    parser.add_argument(
        "binary_path",
        nargs="?",
        default="./junocashd",
        help="Path to the local binary (default: ./junocashd)"
    )
    parser.add_argument(
        "--repo",
        default="juno-cash/junocash",
        help="GitHub repository (default: juno-cash/junocash)"
    )
    parser.add_argument(
        "--binary-name",
        default="junocashd",
        help="Name of the binary to find in archive (default: junocashd)"
    )

    args = parser.parse_args()
    binary_path = args.binary_path

    # Fetch release info first (needed for download if binary missing)
    print(f"Fetching latest release from GitHub ({args.repo})...")
    release_info = get_latest_github_release(args.repo)

    remote_version = release_info.get('tag_name', 'unknown')
    print(f"Latest GitHub release: {remote_version}")

    assets = release_info.get('assets', [])
    linux_asset = find_linux_amd64_asset(assets)

    if linux_asset:
        print(f"Linux amd64 asset: {linux_asset.get('name')}")

    # Check if binary exists, download if not
    if not os.path.exists(binary_path):
        print(f"\nBinary not found at '{binary_path}'")

        if not linux_asset:
            print("Error: No Linux amd64 asset found in release", file=sys.stderr)
            sys.exit(1)

        download_url = linux_asset.get('browser_download_url')
        target_path = Path(binary_path).resolve()

        # Extract to temp directory and copy binary
        with tempfile.TemporaryDirectory() as tmp_dir:
            extracted_binary = download_and_extract(download_url, tmp_dir, args.binary_name)

            # Copy binary to the specified location
            target_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Copying binary to {target_path}...")
            shutil.copy2(extracted_binary, target_path)
            os.chmod(target_path, 0o755)

        print("Cleaned up temporary files.")
        binary_path = str(target_path)

    print(f"\nChecking local binary: {binary_path}")
    local_version = get_local_version(binary_path)
    print(f"Local version: {local_version}")

    # Compare versions
    local_normalized = normalize_version(local_version)
    remote_normalized = normalize_version(remote_version)

    print("\n" + "=" * 50)
    if local_normalized == remote_normalized:
        print("Versions match! You are up to date.")
        return 0
    else:
        print(f"Version mismatch!")
        print(f"  Local:  {local_version}")
        print(f"  Remote: {remote_version}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
