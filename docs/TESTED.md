# Tested and working

This page is the showcase list. It is updated after each live test against a Secure Workload tenant.

**Latest run:** 2 Oct 2026, SaaS tenant. Authentication succeeded. The features below returned data.

## Ready to demo

| Feature | What you can show | Try this |
|---|---|---|
| `list_scopes` | The full scope tree | "Show me the scope tree." |
| `list_sensors` | Every reporting agent: hostname, platform, addresses | "List the agents on this cluster." |
| `list_workspaces` | Application workspaces used for policy | "What workspaces are defined?" |
| `search_inventory` | Inventory search by IP or other field | "Find the workload for this IP." |
| `get_workload` | One workload record when the address exists | "Show me the workload at this IP." |
| `list_forensic_profiles` | Configured forensic profiles, including built-in ones | "Which forensic profiles are on this cluster?" |
| `summarize_cluster_posture` | Fleet size and scope count | "How many agents and scopes are reporting?" |
| `csw://cluster/info` | Confirms the server is configured and the tenant answers | "Is csw-mcp connected?" |

## How a run is counted

A feature is listed here when a live call returns HTTP 200 and the result is something you can put on screen. The date at the top is the last time that check was done. Add a row when a later run confirms another feature.
