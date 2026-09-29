"""Test plan_node routing for all 5 queries."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

async def test():
    from graph.nodes import plan_node
    from graph.state import BusinessState

    tests = [
        "Show all customers",
        "Show all orders",
        "Find Manoj Kumar",
        "Show Manoj Kumar's orders",
        "Find pending complaints",
    ]
    for q in tests:
        state = BusinessState(
            question=q, category="", customer_name="",
            required_actions=[], customer_data="", order_data="",
            complaint_data="", policy_context="", context="",
            decision="", ticket_result="", response=""
        )
        result = await plan_node(state)
        actions = result.get("required_actions", [])
        cname = result.get("customer_name", "")
        cat = result.get("category", "")
        print(f"Q: {q}")
        print(f"  actions: {actions}")
        print(f"  customer_name: '{cname}'")
        print(f"  category: {cat}")
        print()

asyncio.run(test())
