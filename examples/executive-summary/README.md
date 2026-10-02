# Example — Executive Summary (one-page CISO briefing)

> **All data in this example is synthetic.** Hostnames use the approved
> placeholder vocabulary, IPs are RFC 5737 ranges, cluster is
> `demo-cluster.tetrationcloud.com`.

## The question

> *"Give me the one-page CISO summary for this cluster."*

The ask every POV ends with: a single page a security leader can read in two
minutes and forward to their boss.

## How csw-mcp answers it

The model gathers posture signals, then synthesizes — it does not dump raw JSON:

1. **`summarize_cluster_posture`** — enforcement coverage, agents by type.
2. **`top_vulnerable_hosts`** — concentration of critical CVEs.
3. **`top_risky_flows`** — risky service exposure (RDP/SMB/MSSQL/Redis).
4. **`list_workspaces`** — how much ADM policy modeling already exists.

The output is organized into three posture scores (Segmentation, Vulnerability
Hygiene, Visibility) plus a plain-English narrative.

## The synthetic cluster

- **50 agents**, **24% enforcing**, **31 critical CVEs** on 8 hosts.
- **4 risky ports** on flat paths; **6 workspaces** modeled by ADM.
- Posture: Visibility **100%** (good), Vulnerability hygiene **62%** (amber),
  Segmentation **24%** (at risk).

## The deliverable

- [`report.html`](report.html) — the one-page executive briefing.
- [`transcript.md`](transcript.md) — the question → tool-calls → response flow.

## Headline story

Visibility is complete and ADM policy is ready; the gap is **enforcement**, and
closing it is low-risk because the policy is already written. Start with the
databases.
