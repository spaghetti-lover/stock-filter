"""Long-lived in-process FastMCP client sessions plus a LangChain tool cache.

Built once at FastAPI startup. Trading-agent analysts pull pre-built BaseTool
instances out of here; nothing else needs to know about MCP plumbing.
"""

from contextlib import AsyncExitStack

from fastmcp import Client
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools

from infrastructure.tools.catalog import SERVER_INSTANCES
from infrastructure.tools.toolset import ToolSet


class McpToolRegistry:
    def __init__(self) -> None:
        self._stack: AsyncExitStack | None = None
        self._tools_by_name: dict[str, BaseTool] = {}

    async def start(self) -> None:
        if self._stack is not None:
            return
        stack = AsyncExitStack()
        await stack.__aenter__()
        try:
            for server in SERVER_INSTANCES.values():
                client = await stack.enter_async_context(Client(server))
                tools = await load_mcp_tools(client.session)
                for t in tools:
                    self._tools_by_name[t.name] = t
        except BaseException:
            await stack.__aexit__(None, None, None)
            raise
        self._stack = stack

    async def stop(self) -> None:
        if self._stack is None:
            return
        await self._stack.__aexit__(None, None, None)
        self._stack = None
        self._tools_by_name.clear()

    def tools_for(self, toolset: ToolSet) -> list[BaseTool]:
        return [self._tools_by_name[n] for n in toolset.names]
