#!/usr/bin/env python3
"""Live smoke test for every csw-mcp tool.

This is a dependency-free script (not pytest). Run it locally against your own
cluster to confirm each tool executes end-to-end without raising:

    uv run python tests/test_tools_live.py

What it does:
  * Calls every tool with safe default arguments. Where a tool needs an id/uuid,
    it first discovers a real one (from list_workspaces / list_sensors) and
    falls back to a synthetic placeholder so the call still exercises the code
    path gracefully.
  * Prints PASS/FAIL per tool plus the first 200 chars of each result.
  * Exits 0 only if every tool returned without raising an exception.

Output goes to the terminal only — nothing is written to disk, so no live
cluster data is ever committed. Works with or without credentials: unconfigured
tools return a structured error (still a PASS, since no exception is raised).

Placeholder values use RFC 5737 documentation IPs only.
"""

from __future__ import annotations

import json
import sys

from csw_mcp import csw_client
from csw_mcp import server

# RFC 5737 documentation address — safe, non-routable placeholder.
PLACEHOLDER_IP = "203.0.113.10"
PLACEHOLDER_UUID = "00000000-0000-0000-0000-000000000000"
PLACEHOLDER_APP_ID = "000000000000000000000000"


def _first(result: dict, *keys: str):
    """Pull the first record's value for any of `keys` from a results dict."""
    if not isinstance(result, dict):
        return None
    for rec in result.get("results") or []:
        if isinstance(rec, dict):
            for k in keys:
                if rec.get(k):
                    return rec[k]
    return None


def _discover():
    """Best-effort discovery of a real app_id and workload uuid for dependent tools."""
    app_id = PLACEHOLDER_APP_ID
    uuid = PLACEHOLDER_UUID
    try:
        ws = server.list_workspaces()
        app_id = _first(ws, "id") or app_id
    except Exception:  # noqa: BLE001 — discovery is best-effort
        pass
    try:
        sensors = server.list_sensors(limit=5)
        uuid = _first(sensors, "uuid") or uuid
    except Exception:  # noqa: BLE001
        pass
    return app_id, uuid


def main() -> int:
    configured = csw_client.is_configured()
    print("=" * 70)
    print("csw-mcp live tool smoke test")
    print(f"credentials configured: {configured}")
    if not configured:
        print("(running unconfigured — tools should return structured errors, not crash)")
    print("=" * 70)

    app_id, uuid = _discover()
    print(f"using app_id={app_id}  uuid={uuid}\n")

    # (name, callable) — each lambda calls a tool with safe default args.
    cases = [
        ("list_scopes", lambda: server.list_scopes()),
        ("list_sensors", lambda: server.list_sensors(limit=5)),
        ("search_inventory", lambda: server.search_inventory(PLACEHOLDER_IP, field="ip")),
        ("get_workload", lambda: server.get_workload(PLACEHOLDER_IP)),
        ("summarize_cluster_posture", lambda: server.summarize_cluster_posture()),
        ("list_workspaces", lambda: server.list_workspaces()),
        ("get_workspace_policies", lambda: server.get_workspace_policies(app_id)),
        ("list_policies_for_workload", lambda: server.list_policies_for_workload(uuid)),
        ("search_flows", lambda: server.search_flows("", hours=1, limit=5)),
        ("get_conversations", lambda: server.get_conversations(app_id)),
        ("top_risky_flows", lambda: server.top_risky_flows(hours=1, limit=5)),
        ("get_workload_cves", lambda: server.get_workload_cves(uuid)),
        ("get_workload_packages", lambda: server.get_workload_packages(uuid)),
        ("top_vulnerable_hosts", lambda: server.top_vulnerable_hosts(limit=5)),
        ("list_forensic_profiles", lambda: server.list_forensic_profiles()),
        ("list_forensic_rules", lambda: server.list_forensic_rules(limit=5)),
        ("list_forensic_intents", lambda: server.list_forensic_intents()),
        ("summarize_flows", lambda: server.summarize_flows(hours=1, limit=20)),
        ("long_lived_processes", lambda: server.long_lived_processes(days=1, limit_per_day=20, min_days=1)),
        ("audit_risky_policy_ports", lambda: server.audit_risky_policy_ports(limit=5)),
    ]

    failures = 0
    for name, call in cases:
        try:
            result = call()
            snippet = json.dumps(result, default=str)[:200]
            print(f"PASS  {name:28s} {snippet}")
        except Exception as exc:  # noqa: BLE001 — the whole point is to catch & report
            failures += 1
            print(f"FAIL  {name:28s} {type(exc).__name__}: {exc}")

    print("\n" + "=" * 70)
    print(f"{len(cases) - failures}/{len(cases)} tools returned without raising.")
    print("=" * 70)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
