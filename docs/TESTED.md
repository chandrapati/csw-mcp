# Current capabilities

[![Live test](https://img.shields.io/badge/live%20test-4%20Oct%202026-059669)](.)
[![SaaS tenant](https://img.shields.io/badge/tenant-Secure%20Workload%20SaaS-00bceb)](.)

Latest run: **4 Oct 2026** on a Secure Workload SaaS tenant. Sign-in succeeded. Every feature in the table returned data.

| | Feature | What you get | Try this |
|---|---|---|---|
| ✅ | `list_scopes` | The full scope tree | “Show me the scope tree.” |
| ✅ | `list_sensors` | Every reporting agent: hostname, platform, addresses | “List the agents on this cluster.” |
| ✅ | `list_workspaces` | Application workspaces used for policy | “What workspaces are defined?” |
| ✅ | `search_inventory` | Inventory matches by IP or another field | “Find the workload for this IP.” |
| ✅ | `get_workload` | One workload record for an address that exists | “Show me the workload at this IP.” |
| ✅ | `list_forensic_profiles` | Configured forensic profiles, including built-in profiles | “Which forensic profiles are on this cluster?” |
| ✅ | `summarize_cluster_posture` | Agent count, scope count, and how many agents are enforcing | “How many agents are enforcing?” |
| ✅ | `get_workspace_policies` | Absolute and default policies for one workspace | “Show the policies in this workspace.” |
| ✅ | `search_flows` | Recent flow records for a scope | “Show recent flows in the root scope.” |
| ✅ | `get_conversations` | ADM conversations for one workspace | “Show the conversations for this workspace.” |
| ✅ | `top_risky_flows` | Risky ports that have recent flow activity | “Which risky ports have recent traffic?” |
| ✅ | `list_forensic_rules` | Forensic detection rules, including MITRE ids in the name | “Which forensic rules are configured?” |
| ✅ | `list_forensic_intents` | Which profile is bound to which agent group | “Which forensic profile applies where?” |
| ✅ | `summarize_flows` | Policy verdicts, busiest ports, and process names in a sample | “Summarize recent flows.” |
| ✅ | `long_lived_processes` | Processes that keep appearing across daily samples | “Which processes stay up across days?” |
| ✅ | `audit_risky_policy_ports` | ALLOW policies that open a risky port | “Which policies allow RDP or SMB?” |
| ✅ | `csw://cluster/info` | Confirmation the server is configured and the tenant answers | “Is csw-mcp connected?” |

A feature is added here after a live call returns HTTP 200 and a result you can put on screen. Update the date when the next run confirms the list.
