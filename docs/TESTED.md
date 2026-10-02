# Tested and working

[![Live test](https://img.shields.io/badge/live%20test-2%20Oct%202026-059669)](.)
[![SaaS tenant](https://img.shields.io/badge/tenant-Secure%20Workload%20SaaS-00bceb)](.)

Latest run: **2 Oct 2026** on a Secure Workload SaaS tenant. Sign-in succeeded. Every feature in the table returned data.

| | Feature | What you get | Try this |
|---|---|---|---|
| ✅ | `list_scopes` | The full scope tree | “Show me the scope tree.” |
| ✅ | `list_sensors` | Every reporting agent: hostname, platform, addresses | “List the agents on this cluster.” |
| ✅ | `list_workspaces` | Application workspaces used for policy | “What workspaces are defined?” |
| ✅ | `search_inventory` | Inventory matches by IP or another field | “Find the workload for this IP.” |
| ✅ | `get_workload` | One workload record for an address that exists | “Show me the workload at this IP.” |
| ✅ | `list_forensic_profiles` | Configured forensic profiles, including built-in profiles | “Which forensic profiles are on this cluster?” |
| ✅ | `summarize_cluster_posture` | How many agents and scopes are on the cluster | “How many agents and scopes are reporting?” |
| ✅ | `csw://cluster/info` | Confirmation the server is configured and the tenant answers | “Is csw-mcp connected?” |

A feature is added here after a live call returns HTTP 200 and a result you can put on screen. Update the date when the next run confirms the list.
