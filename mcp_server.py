"""Optional read-only MCP adapter for the local memory store."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from memory_manager import MemoryStore, default_db_path


def build_server() -> object:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install requirements-mcp.txt before starting the MCP adapter.") from exc

    db_path = os.environ.get("AGENTIC_MEMORY_DB")
    token = os.environ.get("AGENTIC_MEMORY_MCP_TOKEN")
    if not token:
        raise RuntimeError("AGENTIC_MEMORY_MCP_TOKEN must be set; refusing anonymous MCP access.")
    store = MemoryStore(db_path or default_db_path())
    server = FastMCP("agentic-memory", host="127.0.0.1", port=int(os.environ.get("AGENTIC_MEMORY_MCP_PORT", "8766")), stateless_http=True)

    @server.tool()
    def search_memory(query: str, limit: int = 8) -> dict:
        """Search active, unexpired memories using a short query."""
        return {"items": store.search(query, max(1, min(int(limit), 8)))}

    @server.tool()
    def get_memory_context(task: str, limit: int = 8) -> dict:
        """Retrieve the smallest relevant local context for a task."""
        return store.context(task, max(1, min(int(limit), 8)))

    @server.tool()
    def memory_health() -> dict:
        """Return minimal liveness information without exposing memory."""
        return {"ok": True}

    return server


if __name__ == "__main__":
    server = build_server()
    transport = sys.argv[1] if len(sys.argv) > 1 else "streamable-http"
    server.run(transport=transport)
