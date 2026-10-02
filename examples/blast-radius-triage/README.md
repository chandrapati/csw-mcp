# Example — Blast-Radius Triage

> **All data in this example is synthetic.** Hostnames use the approved
> placeholder vocabulary, IPs are RFC 5737 documentation ranges, and the cluster
> is `demo-cluster.tetrationcloud.com`. It matches no real cluster.

## The question

> *"Which hosts are not under enforcement, and which gaps should I close first?"*

A classic first-week-of-a-POV question. The customer has agents everywhere but
isn't sure how much is actually **enforcing** policy versus just watching.

## How csw-mcp answers it

The model chains three read-only tools:

1. **`list_sensors`** — enumerate the agent fleet and each host's `agent_type`.
2. **`summarize_cluster_posture`** — get the headline KPIs (enforcing vs.
   visibility-only, coverage %).
3. **`search_inventory`** / **`list_sensors`** — identify *which* unenforced
   hosts matter most (crown-jewel databases, jump host, legacy RDP box).

The model then ranks the gap by business impact and drafts three prioritized
recommendations for a security-leadership audience.

## The synthetic cluster

- **50 agents** reporting, **12 enforcing** (24% coverage) → **38 hosts exposed**.
- Of the 38, **7 are high-impact**: `db-prod-01`, `db-prod-02` (crown-jewel
  databases), `legacy-win-01` (RDP exposed), `jump-01` (SSH hub), `app-01`,
  `web-01`, `web-02`.

## The deliverable

- [`report.html`](report.html) — a one-page ranked enforcement-gap report with a
  prioritized remediation plan.
- [`transcript.md`](transcript.md) — the raw question → tool-calls → response flow.

## Headline recommendation

Enforce the **database tier** first (ADM already proposes the ruleset), then
contain **`legacy-win-01`** (RDP → `jump-01` only). Those two moves remove the
top lateral-movement paths in week one and lift coverage well above 24%.
