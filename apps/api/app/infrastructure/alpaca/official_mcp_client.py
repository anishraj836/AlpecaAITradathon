"""
VOLTRON Official Alpaca MCP (Model Context Protocol) & CLI Integration Client
Connects to official Alpaca MCP Server (npx -y @alpaca/mcp / uvx alpaca-mcp-server)
and Alpaca CLI for JSON-RPC 2.0 tool execution.
"""

import json
import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional, List
from app.config import settings
from app.domain.models import AccountInfo, PositionInfo, OrderResult

logger = logging.getLogger("AlpacaOfficialMCPClient")

class AlpacaOfficialMCPClient:
    """
    Standard MCP Client for official Alpaca MCP tools:
    - alpaca_get_account
    - alpaca_get_positions
    - alpaca_get_market_data
    - alpaca_place_order
    - alpaca_get_options_chain
    """

    def __init__(self):
        self.api_key = settings.ALPACA_API_KEY
        self.secret_key = settings.ALPACA_SECRET_KEY
        self.is_paper = settings.ALPACA_PAPER
        self.server_url = settings.ALPACA_MCP_URL or "http://localhost:8002"

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP Tool call via JSON-RPC 2.0 protocol.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": 1,
        }

        # 1. Try MCP HTTP / SSE Server if running
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.server_url}/rpc", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if "result" in data:
                        return data["result"]
        except Exception:
            pass

        # 2. Try CLI Fallback (alpaca CLI subprocess)
        try:
            cmd = ["alpaca", tool_name.replace("alpaca_", ""), "--json"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0 and stdout:
                return json.loads(stdout.decode())
        except Exception:
            pass

        # 3. Honest unavailable response (no fake success fabrication)
        return {
            "error": "Alpaca MCP server offline and CLI not available in PATH",
            "tool": tool_name,
            "is_available": False,
        }

    async def is_available(self) -> bool:
        """Probe if either Alpaca MCP server or Alpaca CLI is actively responsive."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.get(f"{self.server_url}/health")
                if resp.status_code == 200:
                    return True
        except Exception:
            pass

        try:
            proc = await asyncio.create_subprocess_exec(
                "alpaca", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if proc.returncode == 0:
                return True
        except Exception:
            pass

        return False

    async def get_account_via_mcp(self) -> Optional[Dict[str, Any]]:
        """Call official alpaca_get_account MCP tool."""
        res = await self.call_mcp_tool("alpaca_get_account", {})
        return res if (isinstance(res, dict) and "equity" in res and not res.get("error")) else None

    async def get_positions_via_mcp(self) -> Optional[List[Dict[str, Any]]]:
        """Call official alpaca_get_positions MCP tool."""
        res = await self.call_mcp_tool("alpaca_get_positions", {})
        return res if (isinstance(res, list) and not (isinstance(res, dict) and res.get("error"))) else None

    async def get_options_chain_via_mcp(
        self,
        symbol: str,
        expiration_gte: Optional[str] = None,
        expiration_lte: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """Call official alpaca_get_options_chain MCP tool."""
        args: Dict[str, Any] = {"underlying_symbol": symbol}
        if expiration_gte:
            args["expiration_date_gte"] = expiration_gte
        if expiration_lte:
            args["expiration_date_lte"] = expiration_lte
        res = await self.call_mcp_tool("alpaca_get_options_chain", args)
        if isinstance(res, list) and not (isinstance(res, dict) and res.get("error")):
            return res
        if isinstance(res, dict) and "option_contracts" in res:
            return res["option_contracts"]
        return None

    async def place_multileg_order_via_mcp(
        self,
        order_payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Execute multi-leg options trade via official alpaca_place_order / alpaca_place_multileg_order MCP tool.
        """
        # Hard fail-closed paper trading check
        if not settings.ALPACA_PAPER:
            raise ValueError("Safety Circuit Breaker: VOLTRON execution is strictly locked to Paper Trading.")

        res = await self.call_mcp_tool("alpaca_place_multileg_order", order_payload)
        if isinstance(res, dict) and ("id" in res or "client_order_id" in res) and not res.get("error"):
            return res

        # Try standard alpaca_place_order MCP tool
        res = await self.call_mcp_tool("alpaca_place_order", order_payload)
        if isinstance(res, dict) and ("id" in res or "client_order_id" in res) and not res.get("error"):
            return res

        return None

    async def get_order_via_mcp(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Call official alpaca_get_order MCP tool."""
        res = await self.call_mcp_tool("alpaca_get_order", {"order_id": order_id})
        return res if (isinstance(res, dict) and ("id" in res or "status" in res) and not res.get("error")) else None
