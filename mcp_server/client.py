"""
DCI AI Business Assistant - MCP Client

Provides client connection management to the local FastMCP server using stdio transport.
Exposes reusable functions and context managers to list tools and call tools safely.
"""

import json
import sys
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

warnings.filterwarnings("ignore")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = str(Path(__file__).parent / "server.py")


def get_server_parameters() -> StdioServerParameters:
    """
    Create StdioServerParameters pointing to the local MCP server.
    Prefers virtual environment python if available.
    """
    project_root = Path(__file__).resolve().parent.parent
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    executable = str(venv_python) if venv_python.exists() else sys.executable

    return StdioServerParameters(
        command=executable,
        args=[SERVER_PATH],
    )


class MCPClient:
    """
    Clean client wrapper for interacting with the MCP server over stdio.

    Features:
    - Asynchronous connection and lifecycle management
    - Tool discovery (list_tools)
    - Dynamic tool invocation (call_tool)
    - Error handling and safe degradation
    """

    def __init__(self, server_params: StdioServerParameters | None = None):
        self.server_params = server_params or get_server_parameters()
        self._client_cm = None
        self._session_cm = None
        self.session: ClientSession | None = None

    async def connect(self) -> ClientSession:
        """Connect to the MCP server and initialize the session if not already connected."""
        if self.session is None:
            self._client_cm = stdio_client(self.server_params)
            read_stream, write_stream = await self._client_cm.__aenter__()
            self._session_cm = ClientSession(read_stream, write_stream)
            self.session = await self._session_cm.__aenter__()
            await self.session.initialize()
        return self.session

    async def close(self) -> None:
        """Cleanly close the session and transport client."""
        if self._session_cm:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_cm = None
            self.session = None

        if self._client_cm:
            try:
                await self._client_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._client_cm = None

    async def __aenter__(self) -> "MCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def list_tools(self) -> list[str]:
        """
        Discover and list available tools on the MCP server.

        Returns:
            A list of tool name strings.
        """
        try:
            session = await self.connect()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]
        except Exception as e:
            return [f"Error listing tools: {e}"]

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        parse_json: bool = False,
    ) -> Any:
        """
        Call an MCP tool by name with arguments.

        Args:
            tool_name: The name of the tool to execute (e.g. 'search_customer').
            arguments: Dictionary of arguments for the tool.
            parse_json: If True and the output is valid JSON, returns the parsed dict/list.

        Returns:
            The tool result string (or parsed structured object if parse_json=True),
            or a descriptive error message on failure.
        """
        if arguments is None:
            arguments = {}

        try:
            session = await self.connect()
            result = await session.call_tool(tool_name, arguments)

            # Check if the tool reported an execution error
            if getattr(result, "isError", False):
                error_texts = [
                    getattr(block, "text", "") for block in result.content if getattr(block, "text", None)
                ]
                error_msg = "\n".join(error_texts) if error_texts else "MCP tool execution failed."
                return f"Error: {error_msg}"

            # Extract text content from all content blocks
            texts = [
                getattr(block, "text", "") for block in result.content if getattr(block, "text", None)
            ]
            output = "\n".join(texts).strip()

            if parse_json:
                try:
                    return json.loads(output)
                except Exception:
                    pass

            return output

        except Exception as e:
            return f"Error calling tool '{tool_name}': {str(e)}"


@asynccontextmanager
async def get_mcp_client() -> AsyncIterator[ClientSession]:
    """
    Async context manager to connect to the MCP server and yield an initialized ClientSession.
    Provided for backwards compatibility with low-level session callers.
    """
    client = MCPClient()
    try:
        session = await client.connect()
        yield session
    finally:
        await client.close()