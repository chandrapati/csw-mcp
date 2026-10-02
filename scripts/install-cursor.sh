#!/usr/bin/env bash
#
# install-cursor.sh — register csw-mcp with Cursor idempotently.
#
# Adds (or updates) a "csw-mcp" entry in ~/.cursor/mcp.json so Cursor launches
# this server over stdio. Safe to run repeatedly: it merges into any existing
# config and overwrites only the csw-mcp entry. Uses only runtime-computed
# paths — nothing personal is hard-coded.
#
# Usage:
#   bash scripts/install-cursor.sh
#
set -euo pipefail

# Resolve the repo root from this script's location (no hard-coded paths).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

MCP_JSON="${HOME}/.cursor/mcp.json"
mkdir -p "$(dirname "${MCP_JSON}")"

# Prefer uv if available (matches the project toolchain); otherwise fall back
# to the virtualenv's console script.
if command -v uv >/dev/null 2>&1; then
  CMD="uv"
  ARGS_JSON="[\"run\", \"--directory\", \"${REPO_DIR}\", \"csw-mcp\"]"
elif [ -x "${REPO_DIR}/.venv/bin/csw-mcp" ]; then
  CMD="${REPO_DIR}/.venv/bin/csw-mcp"
  ARGS_JSON="[]"
else
  echo "ERROR: neither 'uv' nor ${REPO_DIR}/.venv/bin/csw-mcp found." >&2
  echo "Install uv (https://astral.sh/uv) or create the venv first:" >&2
  echo "  cd ${REPO_DIR} && uv venv && uv pip install -e ." >&2
  exit 1
fi

# Merge the entry idempotently using Python (always available with uv/python).
PYTHON_BIN="$(command -v python3 || command -v python)"
"${PYTHON_BIN}" - "${MCP_JSON}" "${CMD}" "${ARGS_JSON}" <<'PY'
import json, sys, os

mcp_json, cmd, args_json = sys.argv[1], sys.argv[2], sys.argv[3]

config = {}
if os.path.isfile(mcp_json):
    try:
        with open(mcp_json, encoding="utf-8") as f:
            config = json.load(f) or {}
    except json.JSONDecodeError:
        print(f"WARNING: {mcp_json} was not valid JSON; starting fresh.", file=sys.stderr)
        config = {}

servers = config.setdefault("mcpServers", {})
servers["csw-mcp"] = {
    "command": cmd,
    "args": json.loads(args_json),
}

with open(mcp_json, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)
    f.write("\n")

print(f"Wrote csw-mcp entry to {mcp_json}")
PY

echo "Done. Restart Cursor (or reload the MCP server) to pick up csw-mcp."
echo "Make sure ${REPO_DIR}/.env is filled in with your cluster credentials."
