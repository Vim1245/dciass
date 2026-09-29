"""
Test MCP Client Integration for DCI AI Business Assistant.

Verifies:
1. MCP connection works.
2. Available MCP tools are displayed (search_customer, search_complaint, create_ticket).
3. search_customer works for 'Ravi Kumar'.
4. search_complaint works for 'Ravi Kumar'.
5. create_ticket can be called successfully and returns a ticket ID (e.g. T001).
"""

import asyncio
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Ensure running inside the project's virtual environment if available
project_root = Path(__file__).resolve().parent.parent
venv_python = project_root / ".venv" / "Scripts" / "python.exe"

if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    result = subprocess.run([str(venv_python)] + sys.argv, cwd=str(project_root))
    sys.exit(result.returncode)

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_server.mcp_service import (
    call_mcp_tool,
    create_ticket_mcp,
    list_mcp_tools,
    search_complaint_mcp,
    search_customer_mcp,
)


async def main():
    print("=" * 60)
    print("DCI AI BUSINESS ASSISTANT - MCP CLIENT INTEGRATION TEST")
    print("=" * 60)

    # 1 & 2: MCP Connection and Tool Discovery
    print("\n[1] AVAILABLE MCP TOOLS:")
    tools = await list_mcp_tools()
    for tool in tools:
        print(f"  - {tool}")

    assert "search_customer" in tools, "Tool 'search_customer' not found!"
    assert "search_complaint" in tools, "Tool 'search_complaint' not found!"
    assert "create_ticket" in tools, "Tool 'create_ticket' not found!"
    print("  [SUCCESS] All expected tools discovered.")

    # 3: search_customer for Ravi Kumar
    print("\n[2] CUSTOMER SEARCH (Ravi Kumar):")
    customer_result = await search_customer_mcp("Ravi Kumar")
    print(customer_result)

    assert "Ravi Kumar" in customer_result, "Expected customer name 'Ravi Kumar' in result!"
    assert "C001" in customer_result, "Expected customer ID 'C001' in result!"
    assert "Active" in customer_result, "Expected status 'Active' in result!"
    print("  [SUCCESS] Customer found with ID C001 and Active status.")

    # 4: search_complaint for Ravi Kumar
    print("\n[3] COMPLAINT SEARCH (Ravi Kumar):")
    complaint_result = await search_complaint_mcp("Ravi Kumar")
    print(complaint_result)

    assert "Damaged product" in complaint_result, "Expected issue 'Damaged product' in result!"
    assert "Open" in complaint_result, "Expected status 'Open' in result!"
    print("  [SUCCESS] Complaint found with issue 'Damaged product' and Open status.")

    # 5: create_ticket
    print("\n[4] CREATE TICKET (Ravi Kumar - Damaged product):")
    ticket_result = await create_ticket_mcp(
        customer_name="Ravi Kumar",
        issue="Damaged product",
    )
    print(ticket_result)

    assert "T001" in ticket_result or "T00" in ticket_result, "Expected new ticket ID (e.g. T001) in result!"
    assert "Open" in ticket_result, "Expected status 'Open' in result!"
    print("  [SUCCESS] Ticket created successfully.")

    print("\n" + "=" * 60)
    print("ALL 5 MCP CLIENT INTEGRATION TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())