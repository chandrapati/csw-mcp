#!/usr/bin/env python3
"""Generate the Stage B example reports for csw-mcp.

Each of the five SE scenarios produces an `examples/<name>/report.html` rendered
in the same visual style as the CSW_POV_Template executive report. Run:

    python3 examples/build_examples.py

ALL data in this file is 100% synthetic:
  * Hostnames come only from the approved placeholder vocabulary
    (web-01, web-02, app-01, db-prod-01, db-prod-02, jump-01, legacy-win-01).
  * IPs are RFC 5737 documentation ranges only.
  * Cluster URL is demo-cluster.tetrationcloud.com; root scope is demo-root.
  * Numbers are believable but invented — they match no real cluster.
  * CVE IDs are real (public information); the hosts they affect are synthetic.

Nothing here is derived from any live or customer cluster.
"""

from __future__ import annotations

import os
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent

CLUSTER = "demo-cluster.tetrationcloud.com"
ROOT_SCOPE = "demo-root"
PREPARED_BY = "Cisco Secure Workload SE (demo)"

# ---------------------------------------------------------------------------
# Shared CSS — mirrors CSW_POV_Template/generate_executive_report.py
# ---------------------------------------------------------------------------
CSS = """
:root {
  --bg:#F8FAFC; --card:#fff; --border:#E2E8F0;
  --cisco:#00bceb; --cisco-dark:#005073;
  --green:#059669; --red:#dc2626; --amber:#d97706; --blue:#0369A1;
  --text:#020617; --text2:#475569; --text3:#94A3B8;
  --shadow-sm:0 1px 3px rgba(0,0,0,.06); --shadow-md:0 4px 6px rgba(0,0,0,.06);
  --radius:10px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);
     color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}
.header{background:linear-gradient(135deg,#00bceb 0%,#005073 100%);
         color:#fff;padding:2.5rem 2rem 2rem}
.header .inner{max-width:1140px;margin:0 auto}
.header h1{font-size:1.85rem;font-weight:800;letter-spacing:-.3px}
.header .sub{opacity:.92;margin-top:.4rem;font-size:.95rem}
.header .meta{margin-top:1.2rem;display:flex;flex-wrap:wrap;gap:.6rem;font-size:.8rem}
.header .meta span{background:rgba(255,255,255,.14);padding:4px 12px;
                    border-radius:99px;backdrop-filter:blur(4px)}
.tldr{background:#0c4a6e;color:#e0f2fe;padding:1.25rem 2rem}
.tldr .inner{max-width:1140px;margin:0 auto}
.tldr h2{font-size:.78rem;text-transform:uppercase;letter-spacing:1px;
         color:#bae6fd;margin-bottom:.6rem;font-weight:700}
.tldr p{font-size:1rem;line-height:1.65}
.kpi-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
            gap:1px;background:var(--border);border-bottom:1px solid var(--border)}
.kpi{background:var(--card);padding:1.4rem 1rem;text-align:center}
.kpi .val{font-size:2.05rem;font-weight:800;line-height:1}
.kpi .val.ok{color:var(--green)}
.kpi .val.warn{color:var(--red)}
.kpi .val.warn-amber{color:var(--amber)}
.kpi .lbl{font-size:.7rem;color:var(--text3);margin-top:.4rem;
          text-transform:uppercase;letter-spacing:.7px;font-weight:600}
.kpi .sub{font-size:.72rem;color:var(--text3);margin-top:.25rem}
.content{max-width:1140px;margin:2rem auto;padding:0 1.5rem;display:grid;gap:1.5rem}
.card{background:var(--card);border:1px solid var(--border);
       border-radius:var(--radius);box-shadow:var(--shadow-sm);overflow:hidden}
.card-header{padding:.95rem 1.5rem;border-bottom:1px solid var(--border);
              display:flex;align-items:center;gap:.75rem;background:#FAFBFC}
.card-header h2{font-size:1rem;font-weight:700}
.card-icon{width:32px;height:32px;border-radius:8px;display:flex;
            align-items:center;justify-content:center;font-size:1rem}
.card-body{padding:1.4rem 1.5rem}
.card-body p{margin-bottom:.75rem}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem}
@media(max-width:720px){.two-col{grid-template-columns:1fr}}
.posture-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
               gap:1rem;margin-top:.5rem}
.posture-card{padding:1rem;border:1px solid var(--border);border-radius:8px;
              background:#FAFBFC}
.posture-card .score{font-size:1.7rem;font-weight:800;line-height:1}
.posture-card .score.ok{color:var(--green)}
.posture-card .score.warn{color:var(--red)}
.posture-card .score.warn-amber{color:var(--amber)}
.posture-card .label{font-size:.72rem;text-transform:uppercase;
                     letter-spacing:.6px;color:var(--text3);margin-top:.3rem}
.posture-card .desc{font-size:.78rem;color:var(--text2);margin-top:.5rem;line-height:1.4}
.bar{height:6px;background:#E2E8F0;border-radius:99px;overflow:hidden;margin-top:.4rem}
.bar-fill{height:100%;border-radius:99px}
.bar-fill.ok{background:var(--green)}
.bar-fill.warn{background:var(--red)}
.bar-fill.warn-amber{background:var(--amber)}
.rec{padding:1rem 1.25rem;border-left:4px solid #94A3B8;background:#fff;
      border-bottom:1px solid var(--border)}
.rec:last-child{border-bottom:none}
.rec.crit{border-left-color:var(--red)}
.rec.high{border-left-color:var(--amber)}
.rec.med{border-left-color:var(--blue)}
.rec .top{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap}
.rec h3{font-size:.96rem;font-weight:700;color:var(--text)}
.rec dl{display:grid;grid-template-columns:max-content 1fr;gap:.4rem 1rem;
        margin-top:.6rem;font-size:.85rem}
.rec dt{color:var(--text3);font-weight:600;text-transform:uppercase;
        letter-spacing:.4px;font-size:.7rem;align-self:start;padding-top:.15rem}
.rec dd{color:var(--text2)}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.84rem}
thead{background:#F1F5F9}
th{padding:.55rem .9rem;text-align:left;font-size:.7rem;text-transform:uppercase;
   letter-spacing:.5px;color:var(--text2);border-bottom:2px solid var(--border);font-weight:600}
td{padding:.55rem .9rem;border-bottom:1px solid #F1F5F9}
tbody tr:nth-child(even) td{background:#FAFBFC}
.badge{display:inline-block;padding:2px 10px;border-radius:99px;font-size:.72rem;font-weight:700}
.callout{background:#FFFBEB;border-left:4px solid var(--amber);
         padding:.85rem 1.25rem;font-size:.85rem;color:#78350f;border-radius:6px}
.callout.info{background:#EFF6FF;border-left-color:var(--blue);color:#1e40af}
footer{text-align:center;padding:2.5rem 1rem;font-size:.75rem;
        color:var(--text3);border-top:1px solid var(--border);margin-top:2rem}
@media print{
  body{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .header,.tldr{-webkit-print-color-adjust:exact}
  .card,.rec{break-inside:avoid}
}
"""

SEV_BADGE = {
    "Critical": "background:#fee2e2;color:#991b1b",
    "High":     "background:#fef3c7;color:#92400e",
    "Medium":   "background:#dbeafe;color:#1e40af",
    "Low":      "background:#f1f5f9;color:#475569",
}


def badge(text: str, style: str) -> str:
    return f'<span class="badge" style="{style}">{text}</span>'


def kpi(val: str, lbl: str, sub: str = "", cls: str = "") -> str:
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi"><div class="val {cls}">{val}</div>'
        f'<div class="lbl">{lbl}</div>{sub_html}</div>'
    )


def card(icon: str, icon_bg: str, title: str, body_html: str) -> str:
    return (
        '<div class="card">'
        f'<div class="card-header"><div class="card-icon" style="background:{icon_bg}">{icon}</div>'
        f'<h2>{title}</h2></div>'
        f'<div class="card-body">{body_html}</div></div>'
    )


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def rec(level: str, title: str, tag: str, fields: dict[str, str]) -> str:
    dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in fields.items())
    return (
        f'<div class="rec {level}"><div class="top"><h3>{title}</h3>'
        f'<span style="font-size:.72rem;color:var(--text3);font-weight:700">{tag}</span></div>'
        f'<dl>{dl}</dl></div>'
    )


def render(title: str, subtitle: str, snapshot_ts: str, generated: str,
           tldr: str, kpis: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {CLUSTER}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <div class="inner">
    <div style="font-size:.75rem;font-weight:700;letter-spacing:2px;opacity:.9;margin-bottom:.3rem">CISCO SECURE WORKLOAD</div>
    <h1>{title}</h1>
    <div class="sub">{subtitle}</div>
    <div class="meta">
      <span>Snapshot: {snapshot_ts}</span>
      <span>Generated: {generated}</span>
      <span>Root Scope: {ROOT_SCOPE}</span>
      <span>Prepared by: {PREPARED_BY}</span>
    </div>
  </div>
</div>
<div class="tldr"><div class="inner"><h2>Bottom line</h2><p>{tldr}</p></div></div>
<div class="kpi-strip">{kpis}</div>
<div class="content">{content}</div>
<footer>Synthetic demonstration report · csw-mcp examples · {CLUSTER} · all data fictional (RFC 5737 / placeholder vocabulary)</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Scenario 1 — blast-radius-triage
# ---------------------------------------------------------------------------
def blast_radius() -> str:
    kpis = (
        kpi("50", "Total Agents", "across demo-root")
        + kpi("12", "Enforcing", "ENFORCER mode", "ok")
        + kpi("24%", "Enforcement Coverage", "38 hosts exposed", "warn")
        + kpi("7", "Unenforced Crown-Jewels", "DB + jump + legacy", "warn")
    )
    gap_rows = [
        ["db-prod-01", "198.51.100.21", "Databases", "VISIBILITY", badge("Critical", SEV_BADGE["Critical"]), "MSSQL open to 9 subnets"],
        ["db-prod-02", "198.51.100.22", "Databases", "VISIBILITY", badge("Critical", SEV_BADGE["Critical"]), "MySQL reachable from WebTier"],
        ["legacy-win-01", "203.0.113.40", "Internal:Apps", "VISIBILITY", badge("Critical", SEV_BADGE["Critical"]), "RDP (3389) exposed broadly"],
        ["jump-01", "192.0.2.10", "Internal:Apps", "VISIBILITY", badge("High", SEV_BADGE["High"]), "SSH hub, no east-west limits"],
        ["app-01", "192.0.2.31", "Production", "VISIBILITY", badge("High", SEV_BADGE["High"]), "Talks to both DB hosts"],
        ["web-01", "203.0.113.11", "WebTier", "VISIBILITY", badge("Medium", SEV_BADGE["Medium"]), "Internet-facing, egress wide"],
        ["web-02", "203.0.113.12", "WebTier", "VISIBILITY", badge("Medium", SEV_BADGE["Medium"]), "Internet-facing, egress wide"],
    ]
    gap_table = table(
        ["Host", "IP", "Scope", "Mode", "Risk", "Why it matters"], gap_rows
    )
    recs = (
        rec("crit", "1 · Enforce the database tier first", "Week 1",
            {"Action": "Move db-prod-01 / db-prod-02 to ENFORCER with a deny-by-default policy allowing only app-01.",
             "Impact": "Cuts the two highest-value targets off from 9 unnecessary subnets.",
             "Effort": "Low — ADM already proposes the ruleset in the Databases workspace."})
        + rec("high", "2 · Contain the legacy RDP host", "Week 1–2",
            {"Action": "Scope legacy-win-01 RDP (3389) to jump-01 only; enable enforcement.",
             "Impact": "Removes the single most-probed lateral-movement path in the cluster.",
             "Effort": "Low."})
        + rec("med", "3 · Phase enforcement across WebTier + app tier", "Week 2–4",
            {"Action": "Promote app-01, web-01, web-02 from VISIBILITY to ENFORCER after a 7-day observation window.",
             "Impact": "Raises coverage from 24% toward 80%+ without breaking app flows.",
             "Effort": "Medium — stage by workspace, verify with flow search before enforce."})
    )
    content = (
        card("📊", "#dbeafe", "What we asked", "<p><strong>“Which hosts are not under enforcement?”</strong> "
             "The agent inventoried the fleet (<code>list_sensors</code>), pulled headline posture "
             "(<code>summarize_cluster_posture</code>), then ranked the enforcement gap.</p>")
        + card("🎯", "#fee2e2", "Enforcement gap — ranked", gap_table
               + '<div class="callout">38 of 50 agents are visibility-only. The 7 hosts above are '
                 'the highest-impact gaps because they are crown-jewel or lateral-movement nodes.</div>')
        + card("🛡", "#dbeafe", "Prioritized recommendations", recs)
    )
    return render(
        "Blast-Radius Triage", f"Enforcement-gap analysis · Cluster {CLUSTER}",
        "2026-07-01 02:00 UTC", "2026-07-01 09:14 UTC",
        "Only <strong>12 of 50 agents (24%)</strong> are enforcing policy. Seven of the 38 unenforced "
        "hosts are crown-jewel databases, the jump host, or a legacy RDP box — a wide blast radius. "
        "Enforcing the database tier and containing legacy-win-01 removes the top lateral-movement paths in week one.",
        kpis, content,
    )


# ---------------------------------------------------------------------------
# Scenario 2 — executive-summary
# ---------------------------------------------------------------------------
def executive_summary() -> str:
    kpis = (
        kpi("50", "Agents Reporting", "100% of fleet")
        + kpi("24%", "Enforcement Coverage", "12 enforcing", "warn")
        + kpi("31", "Critical CVEs", "across 8 hosts", "warn")
        + kpi("4", "Risky Ports Exposed", "RDP/SMB/MSSQL/Redis", "warn-amber")
        + kpi("6", "Workspaces", "ADM proposed", "ok")
    )
    posture = (
        '<div class="posture-grid">'
        '<div class="posture-card"><div class="score warn">24%</div><div class="label">Segmentation</div>'
        '<div class="bar"><div class="bar-fill warn" style="width:24%"></div></div>'
        '<div class="desc">12/50 hosts enforcing. Database and legacy tiers still open.</div></div>'
        '<div class="posture-card"><div class="score warn-amber">62%</div><div class="label">Vulnerability Hygiene</div>'
        '<div class="bar"><div class="bar-fill warn-amber" style="width:62%"></div></div>'
        '<div class="desc">31 criticals concentrated on 8 hosts; most are patchable.</div></div>'
        '<div class="posture-card"><div class="score ok">100%</div><div class="label">Visibility</div>'
        '<div class="bar"><div class="bar-fill ok" style="width:100%"></div></div>'
        '<div class="desc">Every workload is reporting flows — full east-west telemetry.</div></div>'
        '</div>'
    )
    findings = table(
        ["Area", "State", "Headline"],
        [
            ["Visibility", badge("Good", SEV_BADGE["Low"]), "All 50 agents reporting; ADM has mapped 6 workspaces."],
            ["Segmentation", badge("At risk", SEV_BADGE["Critical"]), "Only 24% enforcing; crown-jewel DBs unprotected."],
            ["Vulnerabilities", badge("Attention", SEV_BADGE["High"]), "31 critical CVEs on 8 hosts, incl. BlueKeep & EternalBlue."],
            ["Risky services", badge("Attention", SEV_BADGE["High"]), "RDP, SMB, MSSQL, Redis observed on flat paths."],
        ],
    )
    content = (
        card("📊", "#dbeafe", "Posture at a glance", posture)
        + card("🎯", "#fee2e2", "Key findings", findings)
        + card("🛡", "#dbeafe", "The one-page story",
               "<p>The cluster has <strong>complete visibility</strong> — every workload reports flows and "
               "ADM has already proposed policy for six workspaces. The gap is <strong>enforcement</strong>: "
               "only a quarter of the fleet actively blocks traffic, and the unprotected hosts are the ones "
               "that matter most (databases, the jump host, a legacy Windows box).</p>"
               "<p>Closing the gap is low-risk: the policy is already written by ADM and can be rolled out "
               "tier-by-tier behind a short observation window. The recommended first move is the database "
               "tier, which removes the largest blast-radius exposure immediately.</p>")
    )
    return render(
        "Executive Security Posture Summary", f"One-page CISO briefing · Cluster {CLUSTER}",
        "2026-07-01 02:00 UTC", "2026-07-01 09:20 UTC",
        "Visibility is complete (50/50 agents), but <strong>enforcement is only 24%</strong> and "
        "<strong>31 critical CVEs</strong> sit on 8 hosts. The fix is low-risk — ADM policy is ready to "
        "roll out tier-by-tier, starting with the databases.",
        kpis, content,
    )


# ---------------------------------------------------------------------------
# Scenario 3 — cve-prioritization
# ---------------------------------------------------------------------------
def cve_prioritization() -> str:
    kpis = (
        kpi("20", "Hosts in Scope", "Production + Databases")
        + kpi("48", "Critical CVEs", "across 8 hosts", "warn")
        + kpi("11", "Actively Exploited", "on CISA KEV", "warn")
        + kpi("3", "Exploitable + Exposed", "patch first", "warn")
    )
    cve_rows = [
        ["CVE-2019-0708", "db-prod-01, legacy-win-01", "RDP (BlueKeep)", badge("Critical", SEV_BADGE["Critical"]), "Yes (KEV)", "Exposed on 3389"],
        ["CVE-2017-0144", "legacy-win-01", "SMB (EternalBlue)", badge("Critical", SEV_BADGE["Critical"]), "Yes (KEV)", "Exposed on 445"],
        ["CVE-2021-44228", "app-01, web-01", "Log4Shell", badge("Critical", SEV_BADGE["Critical"]), "Yes (KEV)", "Reachable via web tier"],
        ["CVE-2022-22965", "app-01", "Spring4Shell", badge("Critical", SEV_BADGE["Critical"]), "Yes (KEV)", "Internal only"],
        ["CVE-2021-34527", "legacy-win-01", "PrintNightmare", badge("Critical", SEV_BADGE["Critical"]), "Yes (KEV)", "Internal only"],
        ["CVE-2014-0160", "web-02", "Heartbleed", badge("High", SEV_BADGE["High"]), "Yes (KEV)", "Internet-facing"],
    ]
    cve_table = table(
        ["CVE", "Affected hosts", "Component", "Severity", "Exploited?", "Exposure"], cve_rows
    )
    recs = (
        rec("crit", "Patch BlueKeep + EternalBlue on legacy-win-01 now", "Immediate",
            {"CVEs": "CVE-2019-0708, CVE-2017-0144",
             "Why": "Both are on CISA KEV, wormable, and the host exposes 3389/445 on flat paths.",
             "Compensating control": "If patch window is blocked, enforce legacy-win-01 to jump-01-only immediately."})
        + rec("crit", "Remediate Log4Shell on the web→app path", "24–48h",
            {"CVEs": "CVE-2021-44228 (app-01, web-01)",
             "Why": "Internet-reachable through the web tier; trivially exploitable.",
             "Compensating control": "Block outbound from app-01 except to db-prod-01 while patching."})
        + rec("high", "Schedule the remaining 42 criticals by exposure", "This sprint",
            {"Approach": "Rank by (actively-exploited × internet-exposed). Internal-only criticals follow after KEV-exposed ones.",
             "Tooling": "get_workload_cves per host; top_vulnerable_hosts to re-rank after each patch wave."})
    )
    content = (
        card("📊", "#dbeafe", "What we asked",
             "<p><strong>“Which hosts have Critical CVEs that are also actively exploitable?”</strong> "
             "The agent ran <code>top_vulnerable_hosts</code>, then <code>get_workload_cves</code> on the "
             "worst offenders, and cross-referenced the CISA KEV catalog for active exploitation.</p>")
        + card("🎯", "#fee2e2", "Exploitable criticals — ranked by exposure", cve_table
               + '<div class="callout">Of 48 critical CVEs, 11 are actively exploited (KEV). Three of those '
                 'are <strong>both exploited and network-exposed</strong> — those are the patch-first set.</div>')
        + card("🛡", "#dbeafe", "Remediation plan", recs)
    )
    return render(
        "CVE Prioritization", f"Exploitable + exposed triage · Cluster {CLUSTER}",
        "2026-07-01 02:00 UTC", "2026-07-01 09:33 UTC",
        "Of <strong>48 critical CVEs</strong>, <strong>11 are actively exploited</strong> and 3 are also "
        "network-exposed. BlueKeep and EternalBlue on legacy-win-01 are the top priority — patch now, or "
        "enforce the host to jump-01-only as an immediate compensating control.",
        kpis, content,
    )


# ---------------------------------------------------------------------------
# Scenario 4 — weekly-posture-review
# ---------------------------------------------------------------------------
def weekly_posture_review() -> str:
    kpis = (
        kpi("+2", "Enforcing Agents", "10 → 12", "ok")
        + kpi("24%", "Coverage", "up from 20%", "warn-amber")
        + kpi("-5", "Critical CVEs", "36 → 31", "ok")
        + kpi("+1", "Risky Port", "Redis appeared", "warn")
    )
    delta_rows = [
        ["Enforcing agents", "10", "12", badge("Improved", SEV_BADGE["Low"]), "db-prod-01, db-prod-02 promoted"],
        ["Enforcement coverage", "20%", "24%", badge("Improved", SEV_BADGE["Low"]), "+4 points"],
        ["Critical CVEs", "36", "31", badge("Improved", SEV_BADGE["Low"]), "5 patched on app-01"],
        ["Risky ports exposed", "3", "4", badge("Regressed", SEV_BADGE["Critical"]), "Redis (6379) now open on app-01"],
        ["Agents reporting", "50", "50", badge("Flat", SEV_BADGE["Low"]), "Full visibility maintained"],
    ]
    delta_table = table(
        ["Metric", "Last week", "This week", "Trend", "Note"], delta_rows
    )
    content = (
        card("📊", "#dbeafe", "What changed since last week",
             "<p>The agent read this week's live posture and diffed it against last week's "
             "<code>csw://snapshots/latest</code> snapshot.</p>" + delta_table)
        + card("🎯", "#fef3c7", "Top 3 actions for the week",
               rec("crit", "Close the new Redis exposure on app-01", "Mon",
                   {"What": "Redis (6379) opened on app-01 this week — not in the ADM baseline.",
                    "Action": "Confirm intent with app owner; if unneeded, enforce-deny and remove."})
               + rec("high", "Keep the enforcement wave moving", "Tue–Thu",
                   {"What": "Databases are now enforcing; app-01 is next.",
                    "Action": "Promote app-01 to ENFORCER after a 72h observation window."})
               + rec("med", "Verify the 5 CVE fixes stuck", "Fri",
                   {"What": "app-01 dropped from 36→31 criticals.",
                    "Action": "Re-run get_workload_cves on app-01 to confirm, update the tracker."}))
    )
    return render(
        "Weekly Posture Review", f"Week-over-week delta · Cluster {CLUSTER}",
        "2026-07-01 02:00 UTC", "2026-07-01 09:05 UTC",
        "Good momentum: enforcement rose <strong>20% → 24%</strong> (databases now protected) and criticals "
        "fell <strong>36 → 31</strong>. One regression — <strong>Redis (6379) newly exposed on app-01</strong> — "
        "is this week's top fix.",
        kpis, content,
    )


# ---------------------------------------------------------------------------
# Scenario 5 — pov-closeout
# ---------------------------------------------------------------------------
def pov_closeout() -> str:
    kpis = (
        kpi("50", "Workloads Secured", "100% visibility")
        + kpi("20% → 72%", "Enforcement", "over 6 weeks", "ok")
        + kpi("36 → 14", "Critical CVEs", "-61%", "ok")
        + kpi("6", "Workspaces Modeled", "ADM policy live", "ok")
    )
    kpi_table = table(
        ["KPI", "POV start", "POV end", "Delta"],
        [
            ["Enforcement coverage", "20% (10/50)", "72% (36/50)", badge("+52 pts", SEV_BADGE["Low"])],
            ["Critical CVEs", "36", "14", badge("-61%", SEV_BADGE["Low"])],
            ["Crown-jewel hosts enforcing", "0 / 7", "7 / 7", badge("Complete", SEV_BADGE["Low"])],
            ["Risky ports on flat paths", "4", "1", badge("-75%", SEV_BADGE["Low"])],
            ["Mean time to policy (new app)", "~3 days", "~2 hours", badge("ADM-driven", SEV_BADGE["Medium"])],
        ],
    )
    plan = (
        rec("high", "Extend enforcement to the remaining 14 hosts", "Days 1–14",
            {"Owner": "Platform + SecOps", "Outcome": "Reach 95%+ coverage; only break-glass hosts remain in visibility."})
        + rec("high", "Operationalize the weekly posture review", "Days 1–7",
            {"Owner": "SecOps", "Outcome": "Adopt csw/weekly-posture-review prompt; snapshot diff every Monday."})
        + rec("med", "Wire CVE→patch workflow", "Days 7–21",
            {"Owner": "Vuln mgmt", "Outcome": "top_vulnerable_hosts feeds the patch queue; re-score weekly."})
        + rec("med", "Automate policy for new workspaces", "Days 14–30",
            {"Owner": "App teams", "Outcome": "New apps onboard via ADM; policy live in hours, not days."})
    )
    content = (
        card("📊", "#dbeafe", "Executive narrative",
             "<p><strong>What was built.</strong> Over a six-week proof-of-value we deployed agents to all "
             "50 workloads in <code>demo-root</code>, achieved full east-west visibility, and let ADM model "
             "policy across six workspaces (WebTier, Production, Databases, Internal:Apps and two more).</p>"
             "<p><strong>What was measured.</strong> Enforcement coverage climbed from 20% to 72%, all seven "
             "crown-jewel hosts moved to enforce-deny, critical CVEs dropped 61% as the patch queue was driven "
             "by exploitability ranking, and risky-service exposure on flat paths fell from four ports to one.</p>"
             "<p><strong>What's next.</strong> The remaining 14 hosts are low-risk and ready to enforce; a "
             "weekly posture-review rhythm and an ADM-driven onboarding flow make the gains durable without "
             "adding headcount.</p>")
        + card("🎯", "#d1fae5", "KPI scorecard", kpi_table)
        + card("🛡", "#dbeafe", "Next 30 days — prioritized", plan)
    )
    return render(
        "Proof-of-Value Closeout", f"6-week outcome summary · Cluster {CLUSTER}",
        "2026-07-01 02:00 UTC", "2026-07-01 10:00 UTC",
        "In six weeks the cluster went from <strong>20% to 72% enforcement</strong>, protected all 7 "
        "crown-jewel hosts, and cut critical CVEs <strong>61%</strong>. A weekly review cadence and "
        "ADM-driven onboarding keep the gains durable.",
        kpis, content,
    )


SCENARIOS = {
    "blast-radius-triage": blast_radius,
    "executive-summary": executive_summary,
    "cve-prioritization": cve_prioritization,
    "weekly-posture-review": weekly_posture_review,
    "pov-closeout": pov_closeout,
}


def main() -> None:
    for name, builder in SCENARIOS.items():
        out_dir = EXAMPLES_DIR / name
        out_dir.mkdir(parents=True, exist_ok=True)
        html = builder()
        (out_dir / "report.html").write_text(html, encoding="utf-8")
        print(f"wrote {name}/report.html ({len(html):,} bytes)")
    print(f"\n{len(SCENARIOS)} reports generated under {EXAMPLES_DIR}")


if __name__ == "__main__":
    main()
