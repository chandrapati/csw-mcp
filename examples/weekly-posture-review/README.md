# Example — Weekly Posture Review (week-over-week delta)

> **All data in this example is synthetic.** Hostnames use the approved
> placeholder vocabulary, IPs are RFC 5737 ranges, cluster is
> `demo-cluster.tetrationcloud.com`.

## The question an SE asks

> *"What changed in our posture since last week?"*

The Monday-standup question. Leadership doesn't want the full picture every week
— they want the **delta**: what got better, what regressed, what to do about it.

## How csw-mcp answers it

1. Read **this week's** live posture via **`summarize_cluster_posture`** +
   **`top_risky_flows`**.
2. Read **last week's** state from the **`csw://snapshots/latest`** resource.
3. Diff the two and surface the changes, then draft the top-3 actions for the
   week — all kept under 200 words (the `csw/weekly-posture-review` prompt
   enforces this).

## The synthetic deltas

| Metric | Last week | This week | Trend |
|---|---|---|---|
| Enforcing agents | 10 | 12 | ⬆ improved |
| Coverage | 20% | 24% | ⬆ +4 pts |
| Critical CVEs | 36 | 31 | ⬆ 5 patched |
| Risky ports | 3 | 4 | ⬇ **Redis appeared** |

## The deliverable

- [`report.html`](report.html) — the week-over-week delta table + top-3 actions.
- [`transcript.md`](transcript.md) — the question → tool-calls → response flow.

## Headline

Good momentum (databases now enforcing, criticals down), but one regression:
**Redis (6379) is newly exposed on `app-01`** — that's this week's top fix.
