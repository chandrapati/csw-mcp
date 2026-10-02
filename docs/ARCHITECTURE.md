# Architecture

`csw-mcp` is a thin, read-only translation layer between an MCP client and the
Cisco Secure Workload OpenAPI. It is deliberately small.

## Component diagram

```mermaid
flowchart TB
    subgraph Client["MCP Client (Cursor / Claude Desktop)"]
        LLM[LLM + tool-calling]
    end

    subgraph Server["csw-mcp (this project)"]
        M["__main__.py<br/>stdio entry point"]
        SV["server.py<br/>FastMCP: 15 tools, 4 resources, 3 prompts"]
        CL["csw_client.py<br/>read-only wrapper + error normalization"]
        CF["config.py<br/>.env loader (no override, no logging)"]
        subgraph Vendor["vendor/ (synced, not hand-edited)"]
            API["csw_api.py<br/>HMAC-SHA256 signing + HTTP"]
            H["csw_helpers.py<br/>pagination, sensor map, result shapes"]
        end
    end

    CSW[(Cisco Secure Workload<br/>OpenAPI v1)]

    LLM -- "stdio (JSON-RPC)" --> M --> SV
    SV --> CL
    CL --> CF
    CL --> API
    API --> H
    API -- "HTTPS GET / search POST" --> CSW

    classDef cisco fill:#00bceb,stroke:#005073,color:#fff;
    class CSW cisco;
```

## Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `__main__.py` | Starts the server on **stdio** transport. |
| `server.py` | Defines every tool, resource, and prompt. Validates/clamps inputs; projects outputs down to useful fields. Holds no credentials. |
| `csw_client.py` | The only module that talks to the cluster. Loads `.env` once, exposes read-only `get()` / `search()` helpers, and normalizes responses into `{count, results}` or a structured error. |
| `config.py` | Finds and loads a project `.env` into the environment (never overrides existing vars, never logs secrets). Reports missing required vars. |
| `vendor/csw_api.py` | Vendored HMAC-SHA256 request signer + HTTP client. **Do not hand-edit** — re-sync from `CSW_POV_Template`. |
| `vendor/csw_helpers.py` | Vendored pagination, sensor enumeration, and result-shape normalization. |

## Request lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant C as Cursor
    participant S as server.py
    participant K as csw_client
    participant A as vendor/csw_api
    participant X as CSW API

    U->>C: "How many agents are enforcing?"
    C->>S: call tool summarize_cluster_posture()
    S->>K: fetch_all_sensors()
    K->>A: make_request("GET", "/openapi/v1/sensors")
    A->>A: sign HMAC-SHA256(secret, canonical request)
    A->>X: HTTPS GET + Id / Authorization / Timestamp headers
    X-->>A: JSON (sensors)
    A-->>K: {status, data}
    K-->>S: normalized results
    S->>S: tally agent_type, compute coverage %
    S-->>C: {total_agents, enforcing_agents, coverage_pct, …}
    C-->>U: plain-English KPI summary
```

## HMAC-SHA256 authentication (how the vendored client signs)

CSW's OpenAPI uses an HMAC digest scheme. For each request the vendored
`csw_api.py`:

1. Builds a **canonical message**:
   ```
   METHOD\n
   PATH (including query string)\n
   CHECKSUM (sha256 hex of body for POST/PUT with a body, else empty)\n
   application/json\n
   TIMESTAMP (ISO-8601 UTC, +0000)\n
   ```
2. Computes `HMAC-SHA256(api_secret, canonical_message)` and base64-encodes the
   raw digest.
3. Sends it with the request:
   - `Id`: the API key
   - `Authorization`: the base64 HMAC digest (no scheme prefix)
   - `Timestamp`: the exact timestamp used in the signature
   - `X-Tetration-Cksum`: the body checksum (only when a body is present)

Because the timestamp is part of the signed message, client/cluster clock skew
can cause 401s — see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

> `csw-mcp` only ever issues GET requests and read-only *search* POSTs
> (`/inventory/search`, `/flowsearch`). There is no code path that mutates the
> cluster.

## Why these choices

- **stdio only** eliminates the DNS-rebinding and CSRF risks of an HTTP listener
  and needs zero infrastructure.
- **Vendoring** the API client keeps the generic `CSW_POV_Template` as the single
  source of truth while letting this repo ship self-contained.
- **One cluster per process** (credentials from `.env`) keeps the MVP simple;
  multiple clusters = multiple installs.
