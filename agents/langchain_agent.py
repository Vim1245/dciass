"""
DCI AI Business Assistant - Customer & Orders Agent

An agent that uses ChatOllama and Supabase tools (search_customer, search_orders)
to answer user queries grounded in verified database records.
"""

import re
from typing import Any
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from backend.config import OLLAMA_MODEL
from agents.customer_tools import search_customer, search_orders
from backend.supabase_client import (
    search_customer as supabase_search_customer,
    search_customers_multi as supabase_search_multi,
    extract_all_customer_names as extract_all_names,
    format_customer_records,
    search_orders as supabase_search_orders,
    format_order_records,
)

SYSTEM_INSTRUCTION = (
    "You are the DCI AI Business Assistant specializing in customer and orders operations. "
    "You have access to two tools connected to our database:\n"
    "1. `search_customer`: Search customer profile, name, customer ID, email, phone, city, status.\n"
    "2. `search_orders`: Search orders by Customer ID (e.g. 'C001'), Customer Name (e.g. 'Ravi Kumar', 'Manoj Kumar'), "
    "Order ID (e.g. 'ORD001', 'O0001'), Product (e.g. 'Study Table', 'Laptop'), or Order Status (e.g. 'Pending', 'Delivered', 'In Transit').\n\n"
    "CRITICAL RULES:\n"
    "1. You MUST ALWAYS call `search_orders` when the user asks about orders (e.g. 'Show orders for C001', "
    "'What orders does Ravi Kumar have?', 'Find order ORD001', 'Show pending orders', 'What did Manoj Kumar order?').\n"
    "2. You MUST ALWAYS call `search_customer` when the user asks about a customer's personal or account details.\n"
    "3. When the user asks about MULTIPLE customers (e.g. 'Give me the details of Ravi Kumar and Priya'), "
    "call `search_customer` SEPARATELY for each customer name.\n"
    "4. NEVER guess, invent, or hallucinate order or customer information.\n"
    "5. If `search_orders` returns matching records, summarize the order records accurately in a clear, professional, natural-language response.\n"
    "6. If no matching order is found, return exactly: 'No matching order found.'\n"
    "7. If no customer is found, state that the customer was not found."
)

# Initialize the Ollama model and register both tools
llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.1)
model_with_tools = llm.bind_tools([search_customer, search_orders])


def _has_order_query_intent(message: str) -> bool:
    """Detect if user query is inquiring about orders, purchases, order IDs, or order status."""
    q_lower = message.lower()
    if re.search(r"\b(?:ORD|O)\d{1,5}\b", message, re.IGNORECASE):
        return True
    if any(term in q_lower for term in ["order", "orders", "ordered", "purchase", "purchases", "buy", "bought"]):
        return True
    if "pending" in q_lower or "in transit" in q_lower or "delivered" in q_lower:
        return True
    return False


def _has_customer_query_intent(message: str) -> bool:
    """Detect if user query is inquiring about a customer, ID, email, phone, or city."""
    q_lower = message.lower()
    if re.search(r"\b(C\d{1,4})\b", message, re.IGNORECASE) and not _has_order_query_intent(message):
        return True
    indicators = [
        "customer", "who is", "email", "phone", "city", "account status",
        "registration", "profile"
    ]
    return any(ind in q_lower for ind in indicators)


async def run_customer_agent(message: str) -> str:
    """
    Run the agent on a user message, ensuring search_orders or search_customer is executed
    and results are passed to Ollama for the final natural-language response.
    Supports MULTIPLE customer names in one query (e.g. 'Give me details of Ravi Kumar and Priya').
    """
    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_INSTRUCTION),
        HumanMessage(content=message),
    ]

    tool_executed = False
    is_order_tool = False
    tool_output = ""
    response = None

    # --- Pre-check: detect multi-customer queries and handle directly ---
    all_names = extract_all_names(message)
    is_multi_customer = len(all_names) > 1 and _has_customer_query_intent(message)

    if is_multi_customer:
        # Multi-customer path: search each customer independently
        results = supabase_search_multi(all_names, user_query=message)
        if results:
            tool_output = format_customer_records(results)
            follow_up_prompt = (
                f"User Request: {message}\n\n"
                f"Verified Supabase Customer Records:\n{tool_output}\n\n"
                "Please provide a clear, professional, natural-language response based strictly on the above records. "
                "Include the Customer ID, Name, Email, and all remaining available fields from the database for EACH customer. "
                "Present each customer's details separately. Do NOT invent any information not present above."
            )
            final_resp = await llm.ainvoke([
                SystemMessage(content=SYSTEM_INSTRUCTION),
                HumanMessage(content=follow_up_prompt),
            ])
            return str(final_resp.content)
        else:
            return "The requested customers were not found in the available data."

    try:
        response = await model_with_tools.ainvoke(messages)
        messages.append(response)

        if response.tool_calls:
            for tool_call in response.tool_calls:
                call_name = tool_call.get("name", "")
                args = tool_call.get("args", {})

                if call_name == "search_orders":
                    tool_executed = True
                    is_order_tool = True
                    query_arg = args.get("query") or args.get("customer_id") or args.get("order_id") or message
                    tool_output = search_orders.invoke({
                        "query": str(query_arg),
                        "customer_id": str(args.get("customer_id", "")),
                        "customer_name": str(args.get("customer_name", "")),
                        "order_id": str(args.get("order_id", "")),
                        "product": str(args.get("product", "")),
                        "status": str(args.get("status", "")),
                    })
                    messages.append(
                        ToolMessage(
                            content=str(tool_output),
                            tool_call_id=tool_call["id"],
                        )
                    )

                elif call_name == "search_customer":
                    tool_executed = True
                    search_arg = args.get("query") or args.get("customer_name") or message
                    tool_output = search_customer.invoke({"query": str(search_arg)})
                    messages.append(
                        ToolMessage(
                            content=str(tool_output),
                            tool_call_id=tool_call["id"],
                        )
                    )

            if tool_executed:
                if is_order_tool and "No matching order found." in str(tool_output):
                    return "No matching order found."
                final_response = await model_with_tools.ainvoke(messages)
                return str(final_response.content)

    except Exception:
        tool_executed = False

    # Guard 1: Direct fallback execution for Orders if model didn't call tool
    if not tool_executed and _has_order_query_intent(message):
        results = supabase_search_orders(query=message, user_query=message)
        if results:
            formatted_orders = format_order_records(results)
            follow_up_prompt = (
                f"User Request: {message}\n\n"
                f"Verified Database Orders:\n{formatted_orders}\n\n"
                "Please provide a clear, professional, natural-language response based strictly on the above verified orders. "
                "Include Order ID, Customer ID, Customer Name, Product, Amount, and Delivery/Payment Status. "
                "Do NOT invent any order information not present above."
            )
            final_resp = await llm.ainvoke([
                SystemMessage(content=SYSTEM_INSTRUCTION),
                HumanMessage(content=follow_up_prompt),
            ])
            return str(final_resp.content)
        else:
            return "No matching order found."

    # Guard 2: Direct fallback execution for Customer if model didn't call tool
    if not tool_executed and _has_customer_query_intent(message):
        # Use multi-search even in fallback path
        if all_names:
            results = supabase_search_multi(all_names, user_query=message)
        else:
            results = supabase_search_customer(name=message, user_query=message)

        if results:
            tool_output = format_customer_records(results)
            follow_up_prompt = (
                f"User Request: {message}\n\n"
                f"Verified Supabase Customer Records:\n{tool_output}\n\n"
                "Please provide a clear, professional, natural-language response based strictly on the above records. "
                "Include the Customer ID, Name, Email, and all remaining available fields from the database."
            )
            final_resp = await llm.ainvoke([
                SystemMessage(content=SYSTEM_INSTRUCTION),
                HumanMessage(content=follow_up_prompt),
            ])
            return str(final_resp.content)
        else:
            return "Customer not found. No records matching your query were found in the customer database."

    # Return direct response if no database search was required
    if response is not None and getattr(response, "content", None):
        return str(response.content)
    return "Request processed."

