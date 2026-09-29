"""
DCI AI Business Assistant - Customer Tools

Defines LangChain tools for searching customer information from Supabase.
"""

from typing import Optional
from langchain_core.tools import tool
from backend.supabase_client import (
    search_customer as supabase_search_customer,
    format_customer_records,
    search_orders as supabase_search_orders,
    format_order_records,
)


@tool
def search_customer(query: str = "", customer_name: str = "") -> str:
    """
    Search for customer records in the Supabase database.
    Use this tool whenever the user asks about:
    - customer name or partial name (e.g. 'Manoj Kumar', 'Manoj')
    - customer ID (e.g. 'C012', 'find customer C012')
    - customer email
    - customer phone
    - customer city
    - customer details or account status

    Args:
        query: Customer name, partial name, customer ID, or search phrase.
        customer_name: Optional customer name if separate.

    Returns:
        Formatted customer details with all available fields if found,
        or 'Customer not found.' if no matching records exist.
    """
    search_val = (query or customer_name or "").strip()
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
    Search for orders in the Supabase database.
    Use this tool whenever the user asks about:
    - orders for a customer ID (e.g. 'Show orders for C001')
    - orders for a customer name (e.g. 'What orders does Ravi Kumar have?', 'What did Manoj Kumar order?')
    - order ID lookup (e.g. 'Find order ORD001', 'O0001')
    - pending orders or order status (e.g. 'Show pending orders', 'delivered orders')
    - products ordered (e.g. 'Who ordered a Laptop?', 'orders for Study Table')

    Args:
        query: General search query, phrase, customer name, ID, or status.
        customer_id: Optional specific Customer ID (e.g. 'C001').
        customer_name: Optional specific customer name (e.g. 'Ravi Kumar').
        order_id: Optional specific Order ID (e.g. 'ORD001' or 'O0001').
        product: Optional product name.
        status: Optional order status (e.g. 'Pending', 'Delivered', 'In Transit').

    Returns:
        Formatted order details with all actual columns if found,
        or 'No matching order found.' if no match is found.
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

