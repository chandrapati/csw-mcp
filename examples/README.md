# csw-mcp examples

Five realistic SE scenarios showing how `csw-mcp` turns a natural-language
question into a chain of read-only tool calls and a polished deliverable.

> **Everything here is synthetic.** Hostnames use the approved placeholder
> vocabulary (`web-01`, `app-01`, `db-prod-01`, `legacy-win-01`, …), IPs are
> RFC 5737 documentation ranges, and the cluster is
> `demo-cluster.tetrationcloud.com`. CVE IDs are real (public) but the hosts they
> affect are fictional. None of this is derived from any live or customer cluster.

| Scenario | The question | Deliverable |
|----------|--------------|-------------|
| [`blast-radius-triage`](blast-radius-triage/) | "Which hosts aren't under enforcement?" | Ranked enforcement-gap report |
| [`executive-summary`](executive-summary/) | "Give me the one-page CISO summary." | Executive posture briefing |
| [`cve-prioritization`](cve-prioritization/) | "Which critical CVEs are exploitable *and* exposed?" | Patch-first triage |
| [`weekly-posture-review`](weekly-posture-review/) | "What changed since last week?" | Week-over-week delta |
| [`pov-closeout`](pov-closeout/) | "Write the POV closeout + 30-day plan." | Outcome summary + roadmap |

Each folder contains:

- **`README.md`** — the scenario walkthrough (question, tools used, synthetic data).
- **`transcript.md`** — the raw question → tool-calls → response flow.
- **`report.html`** — the rendered deliverable (open in a browser).

## Regenerating the HTML reports

The reports are generated from a single data-driven script:

```bash
python3 examples/build_examples.py
```

All synthetic data and the shared CSS live in that one file, so the reports stay
consistent and are trivially repeatable.
