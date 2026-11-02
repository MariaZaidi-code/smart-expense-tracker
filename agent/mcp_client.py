"""MCP client used by the agent for real tool invocations.

The client launches ``mcp_server/server.py`` over the stdio transport, performs
the MCP initialize handshake, and calls tools.  This is a genuine MCP
client/server round trip (not a plain HTTP call), which is what Assignment 2
requires.  If the ``mcp`` package is missing or the server cannot start, the
tool runner falls back to the same Python functions locally.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = ROOT / "mcp_server" / "server.py"


def mcp_import_available() -> bool:
    try:
        import mcp  # noqa: F401

        return True
    except Exception:
        return False


class MCPToolClient:
    def __init__(
        self,
        server_script: str | Path | None = None,
        enabled: bool | None = None,
        timeout: int = 60,
    ):
        self.server_script = Path(server_script or SERVER_SCRIPT)
        if enabled is None:
            enabled = os.environ.get("MCP_ENABLED", "1").lower() not in {"0", "false", "no"}
        self.enabled = bool(enabled) and mcp_import_available() and self.server_script.exists()
        self.timeout = timeout
        self._tools: list[str] | None = None
        self.last_error: str | None = None

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "available": mcp_import_available(),
            "server": str(self.server_script.relative_to(ROOT))
            if self.server_script.is_relative_to(ROOT)
            else str(self.server_script),
            "last_error": self.last_error,
        }

    def _server_params(self):
        from mcp import StdioServerParameters

        env = {
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "HF_HUB_DISABLE_PROGRESS_BARS": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "TRANSFORMERS_VERBOSITY": "error",
        }
        model_cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2"
        if model_cache.exists():
            env["HF_HUB_OFFLINE"] = "1"
            env["TRANSFORMERS_OFFLINE"] = "1"
        return StdioServerParameters(
            command=sys.executable,
            args=[str(self.server_script)],
            cwd=str(ROOT),
            env=env,
        )

    async def _list_tools_async(self) -> list[str]:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client

        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]

    def list_tools(self, refresh: bool = False) -> list[str]:
        if not self.enabled:
            return []
        if self._tools is not None and not refresh:
            return self._tools
        try:
            self._tools = asyncio.run(
                asyncio.wait_for(self._list_tools_async(), timeout=self.timeout)
            )
            self.last_error = None
            return self._tools
        except Exception as exc:
            self.last_error = f"MCP list_tools failed: {exc}"
            self._tools = []
            return []

    async def _call_tool_async(self, name: str, arguments: dict) -> dict:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client

        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                texts = []
                for content in result.content:
                    text = getattr(content, "text", None)
                    if text is not None:
                        texts.append(text)
                raw = "\n".join(texts)
                try:
                    parsed: Any = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    parsed = raw
                return {
                    "ok": not bool(getattr(result, "isError", False)),
                    "tool": name,
                    "arguments": arguments,
                    "result": parsed,
                    "raw": raw,
                    "transport": "mcp",
                }

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        if not self.enabled:
            return {
                "ok": False,
                "tool": name,
                "arguments": arguments or {},
                "error": "MCP client is disabled",
                "transport": "mcp",
            }
        try:
            return asyncio.run(
                asyncio.wait_for(
                    self._call_tool_async(name, arguments or {}),
                    timeout=self.timeout,
                )
            )
        except Exception as exc:
            self.last_error = f"MCP call_tool({name}) failed: {exc}"
            return {
                "ok": False,
                "tool": name,
                "arguments": arguments or {},
                "error": self.last_error,
                "transport": "mcp",
            }
