"""csw-mcp FastMCP server — Stage A1 tool surface.

Read-only MCP server for Cisco Secure Workload (CSW / Tetration). Exposes a
small set of query tools and one cluster-info resource. Every tool only reads
from the cluster; none create, update, or delete anything.

Security posture (see codeguard MCP guidance):
  * stdio transport only — no network listener, no DNS-rebinding surface.
  * Single-purpose tools with explicit arguments; no "run arbitrary request" tool.
  * Inputs are validated/clamped before use (e.g. limits are bounded).
  * Outputs are projected down to the fields a user needs, keeping sensitive
    payloads and context bloat to a minimum.
  * The server never makes an authorization decision on the user's behalf — it
    simply surfaces what the credentialed API key is allowed to read.
"""

from __future__ import annotations

import glob
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from . import config, csw_client

mcp = FastMCP("csw-mcp")

# Bounds for user-supplied result limits, so a bad value can't trigger a
# runaway pagination loop against the cluster.
_MIN_LIMIT = 1
_MAX_LIMIT = 1000
_DEFAULT_LIMIT = 100

# Safety caps for aggregator tools that fan out across the fleet, so a huge
# cluster can't turn one tool call into thousands of API requests.
_MAX_HOURS = 24 * 30            # flow queries: cap the look-back window
_MAX_HOSTS_SCANNED = 250        # top_vulnerable_hosts: cap hosts examined
_MAX_FLOW_PAGES = 5             # pagination safety cap for flow/conversation walks

# Risky service ports surfaced by top_risky_flows (port -> label).
RISKY_PORTS: Dict[int, str] = {
    3389: "RDP",
    445: "SMB",
    23: "telnet",
    1433: "MSSQL",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    27017: "MongoDB",
}


def _clamp_limit(limit: int) -> int:
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    return max(_MIN_LIMIT, min(_MAX_LIMIT, limit))


def _clamp_hours(hours: int) -> int:
    try:
        hours = int(hours)
    except (TypeError, ValueError):
        return 24
    return max(1, min(_MAX_HOURS, hours))


def _iso(dt: datetime) -> str:
    """CSW-friendly ISO 8601 UTC timestamp (matches the vendored client's format)."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S+0000")


def _time_window(hours: int) -> tuple[str, str]:
    """Return (t0, t1) ISO timestamps for a look-back window ending now."""
    now = datetime.now(timezone.utc)
    return _iso(now - timedelta(hours=hours)), _iso(now)


def _template_dir() -> Optional[Path]:
    """Locate the generic CSW_POV_Template via $CSW_POV_TEMPLATE (never hard-coded).

    Snapshot/report resources read from the template's output folders when the
    operator points us at them. If the env var is unset or the dir is missing,
    callers degrade gracefully to a "not found" response.
    """
    raw = os.environ.get("CSW_POV_TEMPLATE")
    if not raw:
        return None
    p = Path(raw).expanduser()
    return p if p.is_dir() else None


def _latest_file(directory: Optional[Path], pattern: str) -> Optional[Path]:
    """Return the most recently modified file matching `pattern` under `directory`."""
    if directory is None or not directory.is_dir():
        return None
    matches = glob.glob(str(directory / pattern))
    if not matches:
        return None
    return Path(max(matches, key=os.path.getmtime))


# Minimal TTL cache for the scopes resource (cluster topology changes slowly).
_CACHE_TTL_SECONDS = 60.0
_cache: Dict[str, tuple[float, Any]] = {}


def _cached(key: str, producer) -> Any:
    now = time.monotonic()
    hit = _cache.get(key)
    if hit is not None and (now - hit[0]) < _CACHE_TTL_SECONDS:
        return hit[1]
    value = producer()
    _cache[key] = (now, value)
    return value


def _count_by_severity(cves: List[Dict[str, Any]]) -> Dict[str, int]:
    """Tally CVE records by severity, tolerant of field-name/scoring variations."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for cve in cves:
        if not isinstance(cve, dict):
            continue
        sev = str(cve.get("severity") or cve.get("v3_severity") or "").lower()
        if sev in counts:
            counts[sev] += 1
            continue
        # Fallback: derive severity from a CVSS score when no label is present.
        score = cve.get("cvss_v3_score") or cve.get("cvss_score") or cve.get("score")
        try:
            score = float(score)
        except (TypeError, ValueError):
            continue
        if score >= 9.0:
            counts["critical"] += 1
        elif score >= 7.0:
            counts["high"] += 1
        elif score >= 4.0:
            counts["medium"] += 1
        elif score > 0:
            counts["low"] += 1
    return counts


def _sensor_summary(sensor: Dict[str, Any]) -> Dict[str, Any]:
    """Project a raw sensor record down to the fields users actually ask about."""
    return {
        "uuid": sensor.get("uuid"),
        "hostname": sensor.get("host_name") or sensor.get("hostname"),
        "agent_type": sensor.get("agent_type"),
        "platform": sensor.get("platform"),
        "ips": [
            iface.get("ip")
            for iface in (sensor.get("interfaces") or [])
            if isinstance(iface, dict) and iface.get("ip")
        ],
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_scopes() -> Dict[str, Any]:
    """List the CSW scopes (the hierarchy that organizes workloads and policy).

    Returns a count and the raw scope records from `GET /openapi/v1/app_scopes`.
    Use this to understand how the cluster is segmented before drilling in.
    """
    return csw_client.results_or_error(csw_client.get("/openapi/v1/app_scopes"))


@mcp.tool()
def list_sensors(limit: int = _DEFAULT_LIMIT) -> Dict[str, Any]:
    """List the agents/sensors registered on the cluster (summarized).

    Each entry includes uuid, hostname, agent_type (ENFORCER / VISIBILITY / …),
    platform, and the host's IPs. `limit` caps how many records are returned
    (1–1000). Use this to inventory the fleet and spot which hosts run an
    enforcing agent vs. visibility-only.
    """
    limit = _clamp_limit(limit)
    if not csw_client.is_configured():
        return csw_client.config_error()
    sensors = csw_client.fetch_all_sensors()
    summarized = [_sensor_summary(s) for s in sensors[:limit] if isinstance(s, dict)]
    return {
        "count": len(summarized),
        "total_available": len(sensors),
        "results": summarized,
    }


@mcp.tool()
def search_inventory(
    value: str,
    field: str = "ip",
    match: str = "eq",
    limit: int = _DEFAULT_LIMIT,
) -> Dict[str, Any]:
    """Search cluster inventory for workloads matching a field/value filter.

    Args:
        value:  The value to match (e.g. an IP, hostname fragment, OS string).
        field:  The inventory dimension to filter on (default "ip"). Common
                fields: "ip", "hostname", "os", "user_annotations".
        match:  CSW filter operator — "eq" (exact), "contains", "subnet", etc.
                Defaults to "eq".
        limit:  Max results to return (1–1000).

    Runs a read-only `POST /openapi/v1/inventory/search`. Returns a count and
    the matching inventory records.
    """
    if not value:
        return {"error": "`value` is required.", "hint": "Pass the value to match, e.g. an IP or hostname."}
    body = {
        "filter": {"type": match, "field": field, "value": value},
        "limit": _clamp_limit(limit),
    }
    return csw_client.results_or_error(
        csw_client.search("/openapi/v1/inventory/search", body)
    )


@mcp.tool()
def get_workload(address: str) -> Dict[str, Any]:
    """Fetch the inventory record for a single workload by IP address.

    Looks up the workload via a read-only inventory search for the exact IP.
    Returns the full record if found, or a graceful not-found message. Use this
    to inspect one host's annotations, scopes, and attributes.
    """
    if not address:
        return {"error": "`address` is required (an IP address)."}
    body = {
        "filter": {"type": "eq", "field": "ip", "value": address},
        "limit": 1,
    }
    response = csw_client.search("/openapi/v1/inventory/search", body)
    if response.get("status") != 200:
        return csw_client.results_or_error(response)
    items = csw_client.extract_results(response)
    if not items:
        return {"found": False, "address": address, "message": "No workload found for that address."}
    return {"found": True, "address": address, "workload": items[0]}


@mcp.tool()
def summarize_cluster_posture() -> Dict[str, Any]:
    """Summarize the cluster's security posture at a glance.

    Returns headline KPIs for a security-leadership audience: total agents,
    how many are enforcing policy vs. visibility-only, the enforcement
    coverage percentage, and a breakdown of agents by type. This is the
    fastest way to gauge blast-radius exposure.
    """
    if not csw_client.is_configured():
        return csw_client.config_error()

    sensors = csw_client.fetch_all_sensors()
    total = len(sensors)

    by_type: Dict[str, int] = {}
    for s in sensors:
        if not isinstance(s, dict):
            continue
        agent_type = s.get("agent_type") or "UNKNOWN"
        by_type[agent_type] = by_type.get(agent_type, 0) + 1

    enforcing = by_type.get(csw_client.AGENT_TYPES.ENFORCER, 0)
    visibility = by_type.get(csw_client.AGENT_TYPES.VISIBILITY, 0)
    coverage_pct = round((enforcing / total) * 100, 1) if total else 0.0

    scopes_resp = csw_client.get("/openapi/v1/app_scopes")
    scope_count = (
        len(csw_client.extract_results(scopes_resp))
        if scopes_resp.get("status") == 200
        else None
    )

    return {
        "cluster_url": config.cluster_url(),
        "total_agents": total,
        "enforcing_agents": enforcing,
        "visibility_only_agents": visibility,
        "enforcement_coverage_pct": coverage_pct,
        "agents_by_type": dict(sorted(by_type.items(), key=lambda kv: -kv[1])),
        "scope_count": scope_count,
        "headline": (
            f"{enforcing}/{total} agents enforcing "
            f"({coverage_pct}% coverage)"
            if total
            else "No agents reported by this cluster."
        ),
    }


# ---------------------------------------------------------------------------
# Tools — policy & workspaces
# ---------------------------------------------------------------------------

@mcp.tool()
def list_workspaces() -> Dict[str, Any]:
    """List application workspaces (policy folders / ADM scopes).

    Returns the workspaces from `GET /openapi/v1/applications`. Each workspace
    groups policy rules and ADM versions. Use the returned `id` with
    `get_workspace_policies` or `get_conversations`.
    """
    return csw_client.results_or_error(csw_client.get("/openapi/v1/applications"))


@mcp.tool()
def get_workspace_policies(app_id: str) -> Dict[str, Any]:
    """List the policies defined in a workspace.

    Args:
        app_id: The workspace/application id (from `list_workspaces`).

    Returns the policy records from
    `GET /openapi/v1/applications/{app_id}/policies`.
    """
    if not app_id:
        return {"error": "`app_id` is required (get it from list_workspaces)."}
    return csw_client.results_or_error(
        csw_client.get(f"/openapi/v1/applications/{app_id}/policies")
    )


@mcp.tool()
def list_policies_for_workload(uuid: str) -> Dict[str, Any]:
    """List the policies that currently apply to a single workload.

    Args:
        uuid: The workload/sensor UUID (from `list_sensors`).

    Returns the policies from `GET /openapi/v1/workload/{uuid}/policies` — useful
    to understand exactly what a given host is allowed to talk to.
    """
    if not uuid:
        return {"error": "`uuid` is required (get it from list_sensors)."}
    return csw_client.results_or_error(
        csw_client.get(f"/openapi/v1/workload/{uuid}/policies")
    )


# ---------------------------------------------------------------------------
# Tools — flows & conversations
# ---------------------------------------------------------------------------

@mcp.tool()
def search_flows(filter_json: str = "", hours: int = 24, limit: int = _DEFAULT_LIMIT) -> Dict[str, Any]:
    """Search network flows over a recent time window.

    Args:
        filter_json: A CSW flow filter as a JSON string, e.g.
                     '{"type":"eq","field":"dst_port","value":3389}'. Pass an
                     empty string for no filter (all flows in the window).
        hours:       Look-back window in hours (1–720, default 24).
        limit:       Max flow records to return (1–1000).

    Runs a read-only `POST /openapi/v1/flowsearch` with t0 = now-hours, t1 = now.
    """
    hours = _clamp_hours(hours)
    flt: Any = {}
    if filter_json:
        try:
            flt = json.loads(filter_json)
        except json.JSONDecodeError as exc:
            return {"error": f"Invalid filter_json: {exc}", "hint": 'Example: {"type":"eq","field":"dst_port","value":3389}'}
    t0, t1 = _time_window(hours)
    body = {"t0": t0, "t1": t1, "filter": flt, "limit": _clamp_limit(limit)}
    result = csw_client.results_or_error(csw_client.search("/openapi/v1/flowsearch", body))
    if "results" in result:
        result["window_hours"] = hours
    return result


@mcp.tool()
def get_conversations(app_id: str, version: Optional[int] = None) -> Dict[str, Any]:
    """List ADM conversations (observed talker pairs) for a workspace.

    Args:
        app_id:  The workspace/application id (from `list_workspaces`).
        version: Optional ADM version; omit for the latest.

    Reads `GET /openapi/v1/conversations/{app_id}`, paginating up to a safety cap.
    Conversations are the raw src→dst:port pairs ADM used to propose policy.
    """
    if not app_id:
        return {"error": "`app_id` is required (get it from list_workspaces)."}
    if not csw_client.is_configured():
        return csw_client.config_error()

    params: Dict[str, Any] = {}
    if version is not None:
        params["version"] = version

    collected: List[Any] = []
    for _page, results in csw_client.paginate(
        "GET",
        f"/openapi/v1/conversations/{app_id}",
        params=params or None,
        batch_size=100,
        max_pages=_MAX_FLOW_PAGES,
    ):
        collected.extend(results)

    return {
        "count": len(collected),
        "truncated": len(collected) >= 100 * _MAX_FLOW_PAGES,
        "results": collected,
    }


@mcp.tool()
def top_risky_flows(hours: int = 24, limit: int = 20) -> Dict[str, Any]:
    """Rank risky-service exposure by counting recent flows to sensitive ports.

    Scans the last `hours` for flows to high-risk management/data ports (RDP,
    SMB, telnet, MSSQL, MySQL, PostgreSQL, Redis, MongoDB) and returns the ports
    with the most observed flows. A fast way to spot lateral-movement surface.

    Args:
        hours: Look-back window in hours (1–720, default 24).
        limit: Max flow samples to inspect per port (1–1000).
    """
    if not csw_client.is_configured():
        return csw_client.config_error()
    hours = _clamp_hours(hours)
    per_port_cap = _clamp_limit(limit)
    t0, t1 = _time_window(hours)

    rankings: List[Dict[str, Any]] = []
    for port, label in RISKY_PORTS.items():
        body = {
            "t0": t0,
            "t1": t1,
            "filter": {"type": "eq", "field": "dst_port", "value": port},
            "limit": per_port_cap,
        }
        resp = csw_client.search("/openapi/v1/flowsearch", body)
        if resp.get("status") != 200:
            continue
        hits = len(csw_client.extract_results(resp))
        if hits:
            rankings.append({
                "port": port,
                "service": label,
                "flow_count": hits,
                "capped": hits >= per_port_cap,
            })

    rankings.sort(key=lambda r: r["flow_count"], reverse=True)
    return {
        "window_hours": hours,
        "ports_with_activity": len(rankings),
        "note": "flow_count is a sampled count capped per port; capped=true means more exist.",
        "results": rankings,
    }


# ---------------------------------------------------------------------------
# Tools — vulnerabilities & packages
# ---------------------------------------------------------------------------

@mcp.tool()
def get_workload_cves(uuid: str) -> Dict[str, Any]:
    """List CVEs / vulnerabilities detected on a single workload.

    Args:
        uuid: The workload/sensor UUID (from `list_sensors`).

    Returns records from `GET /openapi/v1/workload/{uuid}/vulnerabilities` plus a
    severity tally (critical/high/medium/low).
    """
    if not uuid:
        return {"error": "`uuid` is required (get it from list_sensors)."}
    result = csw_client.results_or_error(
        csw_client.get(f"/openapi/v1/workload/{uuid}/vulnerabilities")
    )
    if "results" in result:
        result["severity_counts"] = _count_by_severity(result["results"])
    return result


@mcp.tool()
def get_workload_packages(uuid: str) -> Dict[str, Any]:
    """List installed software packages on a single workload.

    Args:
        uuid: The workload/sensor UUID (from `list_sensors`).

    Returns records from `GET /openapi/v1/workload/{uuid}/packages`.
    """
    if not uuid:
        return {"error": "`uuid` is required (get it from list_sensors)."}
    return csw_client.results_or_error(
        csw_client.get(f"/openapi/v1/workload/{uuid}/packages")
    )


@mcp.tool()
def top_vulnerable_hosts(limit: int = 20) -> Dict[str, Any]:
    """Rank the most vulnerable hosts in the cluster by CVE severity.

    Iterates sensors, pulls each host's vulnerabilities, and scores them as
    (critical * 10 + high). Returns the top `limit` hosts with their CVE counts.
    Scanning is capped for safety on large clusters.

    Args:
        limit: Number of top hosts to return (1–1000).
    """
    if not csw_client.is_configured():
        return csw_client.config_error()
    limit = _clamp_limit(limit)

    sensors = csw_client.fetch_all_sensors()
    scanned = 0
    truncated = len(sensors) > _MAX_HOSTS_SCANNED
    ranked: List[Dict[str, Any]] = []

    for sensor in sensors[:_MAX_HOSTS_SCANNED]:
        if not isinstance(sensor, dict):
            continue
        uuid = sensor.get("uuid")
        if not uuid:
            continue
        scanned += 1
        resp = csw_client.get(f"/openapi/v1/workload/{uuid}/vulnerabilities")
        if resp.get("status") != 200:
            continue
        counts = _count_by_severity(csw_client.extract_results(resp))
        score = counts["critical"] * 10 + counts["high"]
        if score <= 0:
            continue
        ranked.append({
            "uuid": uuid,
            "hostname": sensor.get("host_name") or sensor.get("hostname"),
            "risk_score": score,
            "critical": counts["critical"],
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
        })

    ranked.sort(key=lambda r: r["risk_score"], reverse=True)
    return {
        "hosts_scanned": scanned,
        "scan_truncated": truncated,
        "scan_cap": _MAX_HOSTS_SCANNED,
        "results": ranked[:limit],
    }


# ---------------------------------------------------------------------------
# Tools — forensics
# ---------------------------------------------------------------------------

@mcp.tool()
def list_forensic_profiles() -> Dict[str, Any]:
    """List configured forensic profiles (behavioral rule sets for agents).

    Returns records from `GET /openapi/v1/inventory_config/forensic_profiles`.
    """
    return csw_client.results_or_error(
        csw_client.get("/openapi/v1/inventory_config/forensic_profiles")
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("csw://cluster/info")
def cluster_info() -> Dict[str, Any]:
    """Basic identity + reachability info for the configured cluster.

    Reports the configured cluster URL, whether credentials are present, and —
    if reachable — quick counts of scopes and agents. Safe to read first to
    confirm the server is wired up correctly.
    """
    info: Dict[str, Any] = {
        "cluster_url": config.cluster_url() or None,
        "configured": csw_client.is_configured(),
        "transport": "stdio",
        "read_only": True,
    }
    if not csw_client.is_configured():
        info["missing_credentials"] = config.missing_vars()
        return info

    scopes_resp = csw_client.get("/openapi/v1/app_scopes")
    if scopes_resp.get("status") == 200:
        info["reachable"] = True
        info["scope_count"] = len(csw_client.extract_results(scopes_resp))
        info["agent_count"] = len(csw_client.fetch_all_sensors())
    else:
        info["reachable"] = False
        info["error"] = scopes_resp.get("error") or f"HTTP {scopes_resp.get('status')}"
    return info


@mcp.resource("csw://scopes")
def scopes_resource() -> Dict[str, Any]:
    """The cluster scope hierarchy (cached for ~60s).

    Same data as the `list_scopes` tool, exposed as a resource for clients that
    prefer to attach it as context. Cached briefly to avoid re-querying on every
    read.
    """
    return _cached("scopes", lambda: csw_client.results_or_error(
        csw_client.get("/openapi/v1/app_scopes")
    ))


@mcp.resource("csw://snapshots/latest")
def latest_snapshot() -> Dict[str, Any]:
    """The most recent cluster snapshot JSON, if one is available locally.

    Reads the newest `snapshots/snapshot-*.json` under $CSW_POV_TEMPLATE (set the
    env var to point at your generic template checkout). Returns a not-found
    message if no snapshot or template directory is configured.
    """
    snap = _latest_file(_template_dir() and (_template_dir() / "snapshots"), "snapshot-*.json")
    if snap is None:
        return {"error": "no snapshot found", "hint": "Set $CSW_POV_TEMPLATE to a template dir containing snapshots/snapshot-*.json"}
    try:
        return {"source": snap.name, "data": json.loads(snap.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError) as exc:
        return {"error": f"could not read snapshot: {exc}", "source": snap.name}


@mcp.resource("csw://reports/executive-latest")
def latest_executive_report() -> str:
    """The most recent executive-summary markdown report, if available locally.

    Reads the newest `reports/executive-summary-*.md` under $CSW_POV_TEMPLATE.
    Returns a short not-found message when nothing is available.
    """
    report = _latest_file(_template_dir() and (_template_dir() / "reports"), "executive-summary-*.md")
    if report is None:
        return "No executive summary found. Set $CSW_POV_TEMPLATE to a template dir containing reports/executive-summary-*.md"
    try:
        return report.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Could not read report {report.name}: {exc}"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt(name="csw/triage-blast-radius")
def triage_blast_radius() -> str:
    """Guided workflow to assess and shrink a cluster's blast radius."""
    return (
        "You have access to csw-mcp. Walk this workflow: (1) call list_sensors to "
        "understand the agent fleet, (2) call summarize_cluster_posture for the "
        "headline KPIs, (3) identify the top enforcement gap, (4) draft 3 "
        "prioritized recommendations to shrink blast radius. Use plain English "
        "for a security-leadership audience."
    )


@mcp.prompt(name="csw/weekly-posture-review")
def weekly_posture_review() -> str:
    """Monday-standup posture review, diffing against last week's snapshot."""
    return (
        "You have access to csw-mcp. Produce a Monday-standup posture review: "
        "posture summary (2 lines), what changed vs last week (if snapshot "
        "resource available, diff it), top-3 actions for the week. Keep it under "
        "200 words."
    )


@mcp.prompt(name="csw/pov-closeout")
def pov_closeout() -> str:
    """Draft a full proof-of-value closeout narrative + next-30-days plan."""
    return (
        "You have access to csw-mcp. Draft a POV closeout: executive narrative "
        "(3-paragraph arc of what was built, what was measured, what's next), KPI "
        "table, prioritized next-30-days list for the customer admin team."
    )


def get_server() -> FastMCP:
    """Return the configured FastMCP instance (used by the entry point)."""
    return mcp
