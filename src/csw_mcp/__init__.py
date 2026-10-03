"""csw-mcp — a read-only Model Context Protocol server for Cisco Secure Workload.

Lets MCP clients (Cursor, Claude Desktop, Grok, Codex, Gemini) query a Cisco Secure Workload
(CSW / Tetration) cluster in natural language. Read-only by design: this server
exposes no tools that create, update, or delete anything on the cluster.
"""

__version__ = "0.1.0"
