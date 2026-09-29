"""
Integration tests for LangGraph + MCP Client in DCI AI Business Assistant.

Verifies:
1. TEST 1: 'Find the customer details for Ravi Kumar.'
   - Category: customer
   - MCP search_customer invoked
   - Ravi Kumar details returned
2. TEST 2: 'Check Ravi Kumar's complaint.'
   - Category: customer
   - MCP search_complaint invoked
   - Damaged product complaint returned
3. TEST 3: 'Ravi Kumar has a damaged product. Check his customer details and complaint and tell me what action should be taken.'
   - End-to-end workflow: Classification -> MCP search_customer -> MCP search_complaint -> Ollama Business Analysis -> Final Response
4. GENERAL TEST: 'What is Artificial Intelligence?'
   - Category: general
   - MCP customer tools NOT invoked
   - General answer returned
"""

import asyncio
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Ensure running inside project virtual environment if available
project_root = Path(__file__).resolve().parent.parent
venv_python = project_root / ".venv" / "Scripts" / "python.exe"

if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    result = subprocess.run([str(venv_python)] + sys.argv, cwd=str(project_root))
    sys.exit(result.returncode)

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from graph.business_graph import business_graph
from graph.state import BusinessState


async def run_test(title: str, query: str) -> dict:
    print("\n" + "=" * 60)
    print(f"RUNNING: {title}")
    print(f"QUERY:   \"{query}\"")
    print("=" * 60)

    initial_state: BusinessState = {
        "question": query,
        "category": "",
        "customer_data": "",
        "complaint_data": "",
        "context": "",
        "decision": "",
        "response": "",
    }

    result = await business_graph.ainvoke(initial_state)

    print("\n[CATEGORY]:")
    print(result.get("category", "N/A"))

    if result.get("customer_data"):
        print("\n[MCP CUSTOMER DATA]:")
        print(result["customer_data"])

    if result.get("complaint_data"):
        print("\n[MCP COMPLAINT DATA]:")
        print(result["complaint_data"])

    if result.get("decision"):
        print("\n[DECISION]:")
        print(result["decision"])

    print("\n[FINAL RESPONSE]:")
    print(result.get("response", "N/A"))

    return result


async def main():
    print("*" * 60)
    print("DCI AI BUSINESS ASSISTANT - LANGGRAPH + MCP INTEGRATION TESTS")
    print("*" * 60)

    # TEST 1: Customer Details
    res1 = await run_test(
        "TEST 1 — Customer Details Lookup",
        "Find the customer details for Ravi Kumar.",
    )
    assert res1["category"] == "customer", f"Expected category 'customer', got {res1['category']}"
    assert "Ravi Kumar" in res1.get("customer_data", ""), "Expected 'Ravi Kumar' in customer_data"
    assert "C001" in res1.get("customer_data", ""), "Expected 'C001' in customer_data"
    print("\n>>> TEST 1 PASSED: Successfully retrieved customer details via MCP.")

    # TEST 2: Complaint Lookup
    res2 = await run_test(
        "TEST 2 — Complaint Lookup",
        "Check Ravi Kumar's complaint.",
    )
    assert res2["category"] == "customer", f"Expected category 'customer', got {res2['category']}"
    assert "Damaged product" in res2.get("complaint_data", ""), "Expected 'Damaged product' in complaint_data"
    print("\n>>> TEST 2 PASSED: Successfully retrieved complaint details via MCP.")

    # TEST 3: End-to-End Workflow with Business Analysis
    res3 = await run_test(
        "TEST 3 — End-to-End Analysis & Recommendation",
        "Ravi Kumar has a damaged product. Check his customer details and complaint and tell me what action should be taken.",
    )
    assert res3["category"] in ("customer", "business_support"), f"Expected category 'customer' or 'business_support', got {res3['category']}"
    assert "Ravi Kumar" in res3.get("customer_data", ""), "Expected 'Ravi Kumar' in customer_data"
    assert "Damaged product" in res3.get("complaint_data", ""), "Expected 'Damaged product' in complaint_data"
    assert len(res3.get("response", "")) > 20, "Expected generated business analysis response"
    print("\n>>> TEST 3 PASSED: Full MCP + Ollama business analysis workflow completed.")

    # GENERAL TEST: Verify unrelated general question does not call MCP
    res4 = await run_test(
        "GENERAL TEST — General Route Isolation",
        "What is Artificial Intelligence?",
    )
    assert res4["category"] == "general", f"Expected category 'general', got {res4['category']}"
    assert not res4.get("customer_data"), "Customer data should not be populated for general questions"
    assert not res4.get("complaint_data"), "Complaint data should not be populated for general questions"
    assert len(res4.get("response", "")) > 10, "Expected non-empty response for general question"
    print("\n>>> GENERAL TEST PASSED: Successfully routed to general node without MCP calls.")

    print("\n" + "*" * 60)
    print("ALL LANGGRAPH + MCP INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("*" * 60)


if __name__ == "__main__":
    asyncio.run(main())
