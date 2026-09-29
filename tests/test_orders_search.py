import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.supabase_client import search_orders, format_order_records, search_customer, format_customer_records
from agents.langchain_agent import run_customer_agent
from graph.business_graph import business_graph


ORDER_TESTS = [
    ("Test 1", "Show orders for C001"),
    ("Test 2", "What orders does Ravi Kumar have?"),
    ("Test 3", "Find order ORD001"),
    ("Test 4", "Show pending orders"),
    ("Test 5", "What did Manoj Kumar order?"),
    ("Test 6 (Not Found)", "Find order ORD99999"),
]

CUSTOMER_REGRESSION_TESTS = [
    ("Customer Test 1", "find Manoj Kumar"),
    ("Customer Test 2", "find customer C012"),
    ("Customer Test 3", "what is Manoj Kumar's email?"),
]


async def run_all_tests():
    print("=" * 80)
    print("STEP 8 VERIFICATION SUITE — ORDERS SEARCH & CUSTOMER REGRESSION")
    print("=" * 80)

    # 1. Direct Backend Tool tests
    print("\n--- SECTION 1: DIRECT BACKEND TOOL (search_orders) ---")
    for name, query in ORDER_TESTS:
        print(f"\n[{name}] Query: '{query}'")
        records = search_orders(query=query)
        formatted = format_order_records(records)
        print(f"Match Count: {len(records)}")
        print(f"Tool Output:\n{formatted[:300]}...")
        if "ORD99999" in query:
            assert formatted == "No matching order found.", f"Expected 'No matching order found.', got {formatted}"
        else:
            assert len(records) > 0, f"Expected records for '{query}'"
            assert "Order_ID:" in formatted, "Expected formatted order records"
        print(f">>> {name} PASSED!")

    # 2. LangChain Agent tests (/agent endpoint)
    print("\n\n--- SECTION 2: LANGCHAIN AGENT (/agent endpoint) ---")
    for name, query in ORDER_TESTS[:4]:
        print(f"\n[{name}] Agent Query: '{query}'")
        res = await run_customer_agent(query)
        print(f"Agent Response:\n{res}\n")
        assert res and len(res.strip()) > 0, "Expected non-empty agent response"
        print(f">>> {name} PASSED IN AGENT!")

    # 3. LangGraph Workflow tests (/api/assistant endpoint)
    print("\n\n--- SECTION 3: LANGGRAPH WORKFLOW (/api/assistant endpoint) ---")
    for name, query in ORDER_TESTS[:4]:
        print(f"\n[{name}] Workflow Query: '{query}'")
        state = await business_graph.ainvoke({"question": query})
        resp = state.get("response", "")
        print(f"Decision: {state.get('decision')}")
        print(f"Workflow Response:\n{resp}\n")
        assert resp and len(resp.strip()) > 0, "Expected non-empty workflow response"
        print(f">>> {name} PASSED IN WORKFLOW!")

    # 4. Customer Search Regression tests
    print("\n\n--- SECTION 4: CUSTOMER SEARCH REGRESSION TESTS ---")
    for name, query in CUSTOMER_REGRESSION_TESTS:
        print(f"\n[{name}] Query: '{query}'")
        cust_records = search_customer(query=query)
        print(f"Customer Records found: {len(cust_records)}")
        assert len(cust_records) > 0, f"Expected customer records for '{query}'"
        assert any(c.get("Name") == "Manoj Kumar" or c.get("Customer_ID") == "C012" for c in cust_records), "Expected Manoj Kumar / C012"
        
        agent_res = await run_customer_agent(query)
        print(f"Customer Agent Response:\n{agent_res}\n")
        assert "Manoj" in agent_res or "C012" in agent_res, "Expected customer details in agent response"
        print(f">>> {name} PASSED!")

    print("\n" + "=" * 80)
    print("ALL TESTS IN STEP 8 VERIFICATION SUITE PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
