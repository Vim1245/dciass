import os
import sys
import warnings
from typing import Any
from pathlib import Path

warnings.filterwarnings("ignore")

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from backend.database import (
    get_customer_by_name,
    get_complaint_by_customer_name,
    get_customers_by_status,
    create_support_ticket,
    get_total_customer_count,
)
from backend.supabase_client import (
    search_customer as supabase_search_customer,
    search_orders as supabase_search_orders,
)

# Initialize FastMCP Server
mcp = FastMCP("DCI Business MCP Server")


@mcp.tool()
def search_orders(query: str = "", customer_id: str = "", order_id: str = "") -> list[dict[str, Any]] | str:
    """Search orders database by customer ID, order ID, product, or status.

    Args:
        query: Search term or natural language query.
        customer_id: Optional Customer ID (e.g. C001).
        order_id: Optional Order ID (e.g. ORD001, O0001).

    Returns:
        List of matching order records, or 'No matching order found.'
    """
    records = supabase_search_orders(query=query, customer_id=customer_id, order_id=order_id, user_query=query)
    if records:
        return records
    return "No matching order found."



@mcp.tool()
def search_customer(customer_name: str) -> dict[str, Any] | str:
    """Search customer database by customer name, customer ID, email, or details.

    Args:
        customer_name: The name, customer ID (e.g. C012), or partial name of the customer.

    Returns:
        A dictionary containing customer details if found,
        or 'Customer not found.' if no matching record exists.
    """
    records = supabase_search_customer(name=customer_name, user_query=customer_name)
    if records:
        return records[0]

    # Fallback to local database if needed
    res = get_customer_by_name(customer_name)
    if isinstance(res, dict):
        return {
            "customer_id": res.get("customer_id"),
            "name": res.get("name"),
            "email": res.get("email"),
            "status": res.get("status"),
        }
    return "Customer not found."


@mcp.tool()
def search_complaint(customer_name: str) -> dict[str, str] | str:
    """Search complaint database by customer name.

    Args:
        customer_name: The name or partial name of the customer.

    Returns:
        Complaint details if found, or 'Complaint not found.' otherwise.
    """
    res = get_complaint_by_customer_name(customer_name)
    if isinstance(res, dict):
        return {
            "complaint_id": res["complaint_id"],
            "customer_name": res["customer_name"],
            "issue": res["issue"],
            "status": res["status"],
        }
    return "Complaint not found."


@mcp.tool()
def search_customers_by_status(status: str) -> list[dict[str, str]]:
    """Filter customers by their account status (e.g. 'Inactive', 'Active', 'Suspended').

    Args:
        status: The customer status to filter by.

    Returns:
        A list of matching customer records.
    """
    return get_customers_by_status(status)


@mcp.tool()
def create_ticket(customer_name: str, issue: str) -> dict[str, str]:
    """Create a support ticket for a customer issue.

    Args:
        customer_name: The name of the customer submitting the ticket.
        issue: A description of the issue or support request.

    Returns:
        A dictionary containing the generated ticket ID (e.g., T001) and status.
    """
    return create_support_ticket(customer_name, issue)


if __name__ == "__main__":
    mcp.run()
