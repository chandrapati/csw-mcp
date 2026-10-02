"""Configuration + .env loading for csw-mcp.

The vendored `csw_api` module reads credentials from environment variables
(`CSW_API_URL`, `CSW_API_KEY`, `CSW_API_SECRET`, optional `CSW_VERIFY_SSL`).
It only auto-loads a `.env` that sits next to the vendored file, which is not
where we want operators to put their credentials.

This module loads a project-level `.env` into `os.environ` (without overriding
anything already set) so the server picks up credentials no matter the working
directory. Resolution order for the `.env` location:

  1. `$CSW_MCP_ENV` — explicit path to an env file, if set.
  2. The current working directory's `.env`.
  3. A `.env` found by walking up from this file toward the repo root.

Credentials are never logged and never written anywhere by this module.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

REQUIRED_VARS = ("CSW_API_URL", "CSW_API_KEY", "CSW_API_SECRET")


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a simple KEY=value .env file. Mirrors the vendored loader's rules."""
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return values
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        # Values may legitimately contain '=' (e.g. base64); only strip wrapping quotes.
        val = val.strip().strip('"').strip("'")
        if key:
            values[key] = val
    return values


def _find_env_file() -> Optional[Path]:
    explicit = os.environ.get("CSW_MCP_ENV")
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None

    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        return cwd_env

    # Walk up from this file: src/csw_mcp/config.py -> repo root.
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
        # Stop once we pass the repo root (where pyproject.toml lives).
        if (parent / "pyproject.toml").is_file():
            break
    return None


def load_env() -> Optional[Path]:
    """Load a project `.env` into os.environ without overriding existing vars.

    Returns the path that was loaded, or None if no file was found.
    """
    env_path = _find_env_file()
    if env_path is None:
        return None
    for key, val in _parse_env_file(env_path).items():
        os.environ.setdefault(key, val)
    return env_path


def missing_vars() -> list[str]:
    """Return the list of required credential vars that are not set/non-empty."""
    return [v for v in REQUIRED_VARS if not os.environ.get(v)]


def cluster_url() -> str:
    """Return the configured cluster base URL (may be empty if unconfigured)."""
    return os.environ.get("CSW_API_URL", "").rstrip("/")


def verify_ssl() -> bool:
    return os.environ.get("CSW_VERIFY_SSL", "true").lower() != "false"
