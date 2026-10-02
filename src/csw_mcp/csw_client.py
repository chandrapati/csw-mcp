"""Thin integration layer over the vendored CSW API client.

Everything the MCP tools need to talk to the cluster goes through here, so the
server module stays focused on tool definitions. This module:

  * loads the project `.env` once on import (via `config.load_env`),
  * re-exports the vendored `make_request` and the helper utilities, and
  * adds small, well-typed convenience wrappers (safe GET, result extraction)
    with defensive error handling so a single bad call never crashes the server.

Read-only contract: this module only ever issues GET requests and the specific
read-only POST *search* endpoints (inventory/flow search). It exposes no
create/update/delete capability.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import config
from .vendor import csw_api, csw_helpers

# Load credentials from the project .env (no-op if already set in the env).
config.load_env()

# Re-export the pieces callers need.
make_request = csw_api.make_request
extract_results = csw_helpers.extract_results
paginate = csw_helpers.paginate
fetch_all_sensors = csw_helpers.fetch_all_sensors
build_sensor_map = csw_helpers.build_sensor_map
AGENT_TYPES = csw_helpers.AGENT_TYPES


class CswError(Exception):
    """Raised when a CSW request fails in a way the caller should surface."""


def is_configured() -> bool:
    """True when all required credentials are present in the environment."""
    return not config.missing_vars()


def config_error() -> Dict[str, Any]:
    """A structured, user-facing error describing missing configuration."""
    return {
        "error": "CSW credentials are not configured.",
        "missing": config.missing_vars(),
        "hint": "Copy .env.example to .env and fill in CSW_API_URL / CSW_API_KEY / CSW_API_SECRET.",
    }


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Issue a read-only GET and return the parsed response dict.

    Always returns a dict with at least a `status` key. Network/credential
    problems are reported as structured errors rather than raised, so tools
    can hand a clean message back to the LLM.
    """
    if not is_configured():
        return {"status": 0, **config_error()}
    return make_request("GET", path, params=params)


def search(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Issue a read-only search POST (inventory/flow search) and return the response."""
    if not is_configured():
        return {"status": 0, **config_error()}
    return make_request("POST", path, body=body)


def results_or_error(response: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw response into either {"results": [...], "count": n} or an error.

    Keeps tool outputs small and predictable for the model.
    """
    status = response.get("status")
    if status != 200:
        return {
            "error": response.get("error") or f"CSW returned HTTP {status}",
            "status": status,
            "detail": _truncate(response.get("data")),
        }
    items = extract_results(response)
    return {"count": len(items), "results": items}


def _truncate(value: Any, limit: int = 500) -> Any:
    """Shorten long error bodies so we never flood the model's context."""
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "…"
    return value
