#!/usr/bin/env bash
#
# sync-vendor.sh — refresh the vendored CSW client from the upstream template.
#
# The files in src/csw_mcp/vendor/ (csw_api.py, csw_helpers.py) are copied
# verbatim from the generic CSW_POV_Template project so that project stays the
# single source of truth. Run this to re-sync after the template changes.
#
# The template location is taken from the CSW_POV_TEMPLATE environment variable.
# No customer-named or personal path is baked into this script.
#
# Usage:
#   CSW_POV_TEMPLATE=/path/to/CSW_POV_Template bash scripts/sync-vendor.sh
#
set -euo pipefail

if [ -z "${CSW_POV_TEMPLATE:-}" ]; then
  echo "ERROR: set CSW_POV_TEMPLATE to the path of the generic CSW_POV_Template." >&2
  echo "  e.g. CSW_POV_TEMPLATE=/path/to/CSW_POV_Template bash scripts/sync-vendor.sh" >&2
  exit 1
fi

if [ ! -d "${CSW_POV_TEMPLATE}" ]; then
  echo "ERROR: CSW_POV_TEMPLATE directory not found: ${CSW_POV_TEMPLATE}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENDOR_DIR="${REPO_DIR}/src/csw_mcp/vendor"

for f in csw_api.py csw_helpers.py; do
  src="${CSW_POV_TEMPLATE}/${f}"
  if [ ! -f "${src}" ]; then
    echo "ERROR: expected vendor file not found: ${src}" >&2
    echo "Refusing to sync — do not fall back to any customer-named folder." >&2
    exit 1
  fi
  cp "${src}" "${VENDOR_DIR}/${f}"
  echo "synced ${f}"
done

echo "Vendor refresh complete -> ${VENDOR_DIR}"
