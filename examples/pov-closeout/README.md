# Example — Proof-of-Value Closeout

> **All data in this example is synthetic.** Hostnames use the approved
> placeholder vocabulary, IPs are RFC 5737 ranges, cluster is
> `demo-cluster.tetrationcloud.com`.

## The question

> *"Write the POV closeout — what we built, what we measured, and what's next."*

The final deliverable of an engagement: the artifact that turns a successful
proof-of-value into a purchase decision and a 30-day rollout plan.

## How csw-mcp answers it

The `csw/pov-closeout` prompt drives a three-part structure:

1. **Executive narrative** — a 3-paragraph arc (built → measured → next).
2. **KPI scorecard** — start-vs-end numbers that quantify the win
   (from `summarize_cluster_posture`, `top_vulnerable_hosts`, `top_risky_flows`).
3. **Next-30-days plan** — a prioritized, owner-assigned action list.

## The synthetic outcome (6-week POV)

| KPI | Start | End | Delta |
|---|---|---|---|
| Enforcement coverage | 20% (10/50) | 72% (36/50) | +52 pts |
| Critical CVEs | 36 | 14 | −61% |
| Crown-jewel hosts enforcing | 0/7 | 7/7 | complete |
| Risky ports on flat paths | 4 | 1 | −75% |
| Mean time to policy (new app) | ~3 days | ~2 hours | ADM-driven |

## The deliverable

- [`report.html`](report.html) — the full closeout: narrative, KPI scorecard,
  and prioritized next-30-days plan.
- [`transcript.md`](transcript.md) — the question → tool-calls → response flow.

## Headline

In six weeks the cluster went from **20% → 72% enforcement**, protected all 7
crown-jewel hosts, and cut critical CVEs **61%**. A weekly review cadence and
ADM-driven onboarding keep the gains durable without adding headcount.
