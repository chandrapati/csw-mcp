# Contributing

Thanks for improving `csw-mcp`. The most common contribution is **adding a new
read-only tool**. Here's the pattern.

## Ground rules (non-negotiable)

1. **Read-only.** Only `GET` and read-only *search* POSTs. No create/update/delete.
2. **No customer data.** No real hostnames, IPs, scope names, or cluster URLs in
   code, docs, tests, or examples. Use the placeholder vocabulary below.
3. **No secrets.** Nothing credential-shaped in the repo. `.env` stays ignored.
4. **Don't hand-edit `vendor/`.** Re-sync it from `CSW_POV_Template` instead.
5. **Validate inputs; bound outputs.** Clamp limits, cap fan-out, project results.

### Placeholder vocabulary

| Thing | Use only |
|-------|----------|
| Hostnames | `web-01`, `web-02`, `app-01`, `db-prod-01`, `db-prod-02`, `jump-01`, `legacy-win-01` |
| IPs | RFC 5737: `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` |
| Cluster URL | `demo-cluster.tetrationcloud.com` |
| Scope | `demo-root` / `root-scope` |
| Secrets | `your_api_key_here`, `your_api_secret_here` |

CVE IDs may be real (they're public); any host tied to them must be synthetic.

## Adding a tool

Tools live in `src/csw_mcp/server.py`. The pattern:

```python
@mcp.tool()
def get_workload_services(uuid: str) -> dict:
    """One-line summary the model reads to decide when to call this.

    Args:
        uuid: The workload/sensor UUID (from `list_sensors`).

    Longer description of what it returns and when to use it.
    """
    if not uuid:
        return {"error": "`uuid` is required (get it from list_sensors)."}
    # Use the read-only helpers in csw_client — never call out directly.
    return csw_client.results_or_error(
        csw_client.get(f"/openapi/v1/workload/{uuid}/services")
    )
```

Guidelines:

- **Docstrings are the tool's UX.** The LLM uses them to choose and call tools —
  write them for that reader. State required args and what the result contains.
- **Go through `csw_client`.** Use `csw_client.get(path, params)` or
  `csw_client.search(path, body)`; return `csw_client.results_or_error(resp)` so
  errors are normalized and the no-credentials case degrades gracefully.
- **Validate args** up front; return a helpful `{"error": …, "hint": …}` dict.
- **Clamp numeric inputs** with `_clamp_limit` / `_clamp_hours`.
- **Project outputs** — don't return giant raw payloads; keep the model's context lean.

## Adding a resource or prompt

```python
@mcp.resource("csw://your/uri")
def your_resource() -> dict: ...

@mcp.prompt(name="csw/your-workflow")
def your_prompt() -> str: ...
```

Resources that read local files must resolve paths via an env var (see
`_template_dir`) — never hard-code a personal/absolute path.

## Testing

Add your tool to the live smoke harness so it's exercised end-to-end:

```python
# tests/test_tools_live.py
("get_workload_services", lambda: server.get_workload_services(uuid)),
```

Then run:

```bash
uv run python tests/test_tools_live.py        # against a real cluster
uv run python -c "from csw_mcp.server import mcp; print(len(mcp._tool_manager._tools), 'tools')"
```

The harness passes if every tool returns without raising — including the
no-credentials path (which should return a structured error, not crash).

## Before you open a PR

Run the pre-publish safety checks (see the repo's publish checklist):

```bash
# no real credentials
grep -riE 'api_?secret|api_?key' --include='*.py' --include='*.md' . | grep -vE '(your_|example|placeholder|\.env\.example)'
# no customer references (substitute your own org's customer tokens)
grep -riE 'CUSTOMER_NAME|CUSTOMER_CODE' --include='*.py' --include='*.md' --include='*.html' .
# only documentation IPs
grep -rhoE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' --include='*.md' --include='*.py' . | grep -vE '^(192\.0\.2\.|198\.51\.100\.|203\.0\.113\.|127\.0\.0\.1)'
```

All three should come back empty (ignoring `__pycache__/`). Thanks!
