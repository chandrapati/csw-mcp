# Transcript — Executive Summary

> Synthetic walkthrough. Tool outputs are illustrative and fictional.

---

**User:**
> Give me a one-page CISO summary for demo-cluster.

**Assistant → tool call:** `summarize_cluster_posture()`

```json
{ "total_agents": 50, "enforcing_agents": 12, "enforcement_coverage_pct": 24.0,
  "agents_by_type": { "VISIBILITY": 38, "ENFORCER": 12 }, "scope_count": 6 }
```

**Assistant → tool call:** `top_vulnerable_hosts(limit=10)`

```json
{ "hosts_scanned": 50, "scan_truncated": false,
  "results": [
    { "hostname": "legacy-win-01", "risk_score": 42, "critical": 4, "high": 2 },
    { "hostname": "db-prod-01",    "risk_score": 31, "critical": 3, "high": 1 },
    { "hostname": "app-01",        "risk_score": 24, "critical": 2, "high": 4 }
    // … 5 more affected hosts; 31 criticals total across 8 hosts
  ] }
```

**Assistant → tool call:** `top_risky_flows(hours=24, limit=50)`

```json
{ "window_hours": 24, "ports_with_activity": 4,
  "results": [
    { "port": 3389, "service": "RDP",   "flow_count": 180, "capped": false },
    { "port": 445,  "service": "SMB",   "flow_count": 96,  "capped": false },
    { "port": 1433, "service": "MSSQL", "flow_count": 54,  "capped": false },
    { "port": 6379, "service": "Redis", "flow_count": 12,  "capped": false }
  ] }
```

**Assistant → tool call:** `list_workspaces()`
```json
{ "count": 6, "results": [ { "name": "WebTier" }, { "name": "Production" }, { "name": "Databases" }, { "name": "Internal:Apps" } /* +2 */ ] }
```

**Assistant (final answer):**

> **Bottom line:** full visibility (50/50 agents), but enforcement is only **24%**
> and **31 critical CVEs** sit on 8 hosts. The fix is low-risk — ADM policy is
> ready to roll out tier-by-tier, starting with the databases.
>
> | Area | State | Headline |
> |---|---|---|
> | Visibility | Good | All 50 agents reporting; 6 workspaces mapped |
> | Segmentation | At risk | 24% enforcing; crown-jewel DBs unprotected |
> | Vulnerabilities | Attention | 31 criticals on 8 hosts (BlueKeep, EternalBlue) |
> | Risky services | Attention | RDP/SMB/MSSQL/Redis on flat paths |
>
> Full briefing: [`report.html`](report.html).
