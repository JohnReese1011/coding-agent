import json
from langchain_mcp_adapters.client import MultiServerMCPClient
from coding_agent.settings import MCP_CONFIG

class MCPTools:
    def __init__(self):
        self.client = None

    async def load(self):
        if not MCP_CONFIG.exists():
            raise FileNotFoundError(f"MCP config not found: {MCP_CONFIG}")
        config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        self.client = MultiServerMCPClient(config)
        tools = await self.client.get_tools()
        if not tools:
            raise RuntimeError("No MCP tools discovered. Check MCP server config/logs.")
        return tools
