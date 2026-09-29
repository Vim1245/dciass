"""
DCI AI Business Assistant - MCP Service Layer

Provides high-level service functions for interacting with the MCP server:
- list_mcp_tools: Discover available tools dynamically
- call_mcp_tool: Call any tool by name with arguments and safe error handling
- Domain helpers for customer lookup, complaint lookup, and ticket creation
"""

from typing import Any
from mcp_server.client import MCPClient, get_mcp_client


async def list_mcp_tools() -> list[str]:
    """
    Discover and return the list of available MCP tools.
    """
    async with MCPClient() as client:
        return await client.list_tools()


async def call_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    parse_json: bool = False,
) -> Any:
    """
    Call an MCP tool by name with arguments.

    Args:
        tool_name: Name of the tool on the MCP server.
        arguments: Dictionary of arguments.
        parse_json: If True, attempts to parse and return structured JSON.

    Returns:
        Clean output string or structured object, or descriptive error string.
    """
    async with MCPClient() as client:
        return await client.call_tool(tool_name, arguments or {}, parse_json=parse_json)


async def search_customer_mcp(customer_name: str) -> Any:
    """Helper to query customer information via MCP."""
    return await call_mcp_tool("search_customer", {"customer_name": customer_name})


async def search_complaint_mcp(customer_name: str) -> Any:
    """Helper to query complaint information via MCP."""
    return await call_mcp_tool("search_complaint", {"customer_name": customer_name})


async def search_customers_by_status_mcp(status: str) -> Any:
    """Helper to query customers by status via MCP."""
    return await call_mcp_tool("search_customers_by_status", {"status": status})


async def create_ticket_mcp(customer_name: str, issue: str) -> Any:
    """Helper to create a support ticket via MCP."""
    return await call_mcp_tool(
        "create_ticket",
        {"customer_name": customer_name, "issue": issue},
    )