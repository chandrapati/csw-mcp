# Transcript — Weekly Posture Review

> Synthetic walkthrough. Tool/resource outputs are illustrative and fictional.

---

**User:**
> What changed in our CSW posture since last week? Keep it short.

**Assistant → reads resource:** `csw://snapshots/latest`  *(last week's snapshot)*

```json
{ "source": "snapshot-2026-06-24.json",
  "data": { "enforcing_agents": 10, "coverage_pct": 20.0, "critical_cves": 36,
            "risky_ports": [3389, 445, 1433] } }
```

**Assistant → tool call:** `summarize_cluster_posture()`  *(this week, live)*

```json
{ "total_agents": 50, "enforcing_agents": 12, "enforcement_coverage_pct": 24.0 }
```

**Assistant → tool call:** `top_risky_flows(hours=168, limit=50)`

```json
{ "window_hours": 168, "ports_with_activity": 4,
  "results": [
    { "port": 3389, "service": "RDP", "flow_count": 210 },
    { "port": 445,  "service": "SMB", "flow_count": 88 },
    { "port": 1433, "service": "MSSQL", "flow_count": 51 },
    { "port": 6379, "service": "Redis", "flow_count": 12 }
  ] }
```

**Assistant (final answer, <200 words):**

> **Posture summary:** 50/50 agents reporting; enforcement up to **24%** (12/50).
> Momentum is positive.
>
> **What changed vs last week:**
> - ⬆ Enforcing agents **10 → 12** (`db-prod-01`, `db-prod-02` promoted).
> - ⬆ Coverage **20% → 24%**.
> - ⬆ Critical CVEs **36 → 31** (5 patched on `app-01`).
> - ⚠ **Regression:** Redis (6379) newly exposed on `app-01` — not in the ADM baseline.
>
> **Top 3 actions this week:**
> 1. **Mon** — close the new Redis exposure on `app-01` (confirm intent, else enforce-deny).
> 2. **Tue–Thu** — promote `app-01` to ENFORCER after a 72h observation window.
> 3. **Fri** — re-run `get_workload_cves` on `app-01` to confirm the 5 fixes stuck.
>
> Full delta: [`report.html`](report.html).
