# Troubleshooting

The top 10 things that break, and how to fix them.

### 1. Tools return `"CSW credentials are not configured."`

Your `.env` is missing or not being found.

- Confirm `.env` exists at the repo root with `CSW_API_URL`, `CSW_API_KEY`,
  `CSW_API_SECRET`.
- Or point explicitly: `export CSW_MCP_ENV=/abs/path/to/.env`.
- Verify: `uv run python -c "from csw_mcp import config; print(config.missing_vars())"`
  → should print `[]`.

### 2. `401 Unauthorized` on every call

Almost always one of:

- **Wrong key/secret**, or secret pasted with surrounding quotes/whitespace.
- **Clock skew** — the HMAC signature includes a timestamp. If your machine's
  clock is off by more than a minute or two, the cluster rejects it. Sync time
  (`sudo sntp -sS time.apple.com` on macOS).
- **Missing capabilities** — the API key needs `sensor_management`,
  `flow_inventory_query`, `app_policy_management`.

### 3. `CERTIFICATE_VERIFY_FAILED`

You're behind a TLS-inspecting corporate proxy, or macOS Python lacks root certs.

- Proper fix: install your org root CA, or run Python's
  *"Install Certificates.command"*.
- Quick unblock (dev only): set `CSW_VERIFY_SSL=false` in `.env`.

### 4. `command not found: uv`

`uv` isn't on your PATH.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env   # or restart your shell
```

### 5. `No module named 'mcp.server.fastmcp'`

You have `mcp` 2.x installed; this project targets the FastMCP (1.x) API.

```bash
uv pip install -e .      # pyproject pins mcp>=1.0.0,<2
```

### 6. `csw-mcp` doesn't appear in Cursor's MCP picker

- Re-run `bash scripts/install-cursor.sh` and **fully restart** Cursor.
- Check `~/.cursor/mcp.json` has a valid `csw-mcp` entry and the `--directory`
  path is correct.
- Make sure `uv` is on the PATH Cursor sees (launch Cursor from a terminal if needed).

### 7. Server starts but every tool errors with a connection failure

- `CSW_API_URL` should be the **base URL only** — no trailing slash, no path.
  ✅ `https://cluster.tetrationcloud.com` ❌ `https://cluster.../openapi/v1`
- Confirm the cluster is reachable from your network (VPN?).

### 8. `csw://snapshots/latest` / `csw://reports/executive-latest` say "not found"

These resources read local files from a `CSW_POV_Template` checkout.

```bash
export CSW_POV_TEMPLATE=/path/to/CSW_POV_Template
```

If unset or the folder has no `snapshots/snapshot-*.json` / `reports/executive-summary-*.md`,
a graceful "not found" is expected.

### 9. Aggregator tools feel slow on a big cluster

`top_vulnerable_hosts` queries per-host vulnerabilities and `top_risky_flows`
queries per-port. Both are capped (250 hosts, 5 pages) but can still take a while.

- Narrow with smaller `limit` / `hours`.
- `scan_truncated: true` / `capped: true` in the result means the cap was hit.

### 10. `sync-vendor.sh` refuses to run

```
ERROR: set CSW_POV_TEMPLATE to the path of the generic CSW_POV_Template.
```

By design — it won't guess, and it will **never** fall back to a customer-named
folder. Point it at the generic template:

```bash
CSW_POV_TEMPLATE=/path/to/CSW_POV_Template bash scripts/sync-vendor.sh
```

---

Still stuck? Open an issue with the output of:

```bash
uv run python -c "from csw_mcp.server import cluster_info; import json; print(json.dumps(cluster_info(), indent=2))"
```

(It prints config/reachability state — no secrets.)
