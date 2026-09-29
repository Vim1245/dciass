"""
DCI AI Business Assistant - Agent Tools

Defines tools for LangChain agents to perform domain-specific lookup operations using Supabase.
"""

from langchain_core.tools import tool
from backend.supabase_client import (
    search_customer as supabase_search_customer,
    format_customer_records,
    search_orders as supabase_search_orders,
    format_order_records,
)


@tool
def search_customer(customer_name: str = "", query: str = "") -> str:
    """
    Search for a customer in the Supabase database by name, customer ID, email, phone, or city.

    Args:
        customer_name: The name or query to look up.
        query: Optional alternative query parameter.

    Returns:
        Formatted customer details with all available fields if found,
        or 'Customer not found.' if no match is found.
    """
    search_val = (customer_name or query or "").strip()
    if not search_val:
        return "Customer not found."

    results = supabase_search_customer(name=search_val, user_query=search_val)
    if not results:
        return "Customer not found."

    return format_customer_records(results)


@tool
def search_orders(
    query: str = "",
    customer_id: str = "",
    customer_name: str = "",
    order_id: str = "",
    product: str = "",
    status: str = ""
) -> str:
    """
    Search for orders in the Supabase database by customer ID, customer name, order ID, product, or status.

    Args:
        query: Search term or full query.
        customer_id: Customer ID like C001.
        customer_name: Customer name like Ravi Kumar.
        order_id: Order ID like ORD001 or O0001.
        product: Product name like Study Table.
        status: Delivery or payment status like Pending.

    Returns:
        Formatted order details with all actual columns, or 'No matching order found.'
    """
    results = supabase_search_orders(
        query=query,
        customer_id=customer_id,
        customer_name=customer_name,
        order_id=order_id,
        product=product,
        status=status,
        user_query=query or customer_id or customer_name or order_id or product or status,
    )
    if not results:
        return "No matching order found."

    return format_order_records(results)

