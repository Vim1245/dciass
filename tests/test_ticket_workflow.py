"""
DCI AI Business Assistant - STEP 9.4 Ticket Workflow Integration Tests

Verifies:
1. TEST 1 (Ticket Creation): 'Ravi Kumar has a damaged product. Check his complaint and create a support ticket if required.'
   - Customer found through MCP
   - Complaint found through MCP
   - Policy searched through RAG
   - Decision generated (CREATE_TICKET)
   - create_ticket MCP tool called
   - Ticket ID (e.g. T001) returned by MCP
   - Final response contains ticket result
2. TEST 2 (Customer Only): 'Find the customer details for Ravi Kumar.'
   - Customer info returned
   - No unnecessary ticket created
3. TEST 3 (Policy Only): 'How many days do customers have to request a refund?'
   - RAG is used
   - No MCP ticket created
4. TEST 4 (Missing Customer): 'Create a ticket for a customer with a damaged product.'
   - System does NOT create a ticket
   - Asks for customer name or required info
5. TEST 5 (General Question): 'What is Artificial Intelligence?'
   - General route works
   - No unnecessary MCP ticket created
"""

import asyncio
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")

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


async def run_scenario(test_num: int, title: str, query: str) -> dict:
    print("\n" + "=" * 65, flush=True)
    print(f"TEST {test_num}: {title}", flush=True)
    print(f"QUERY: \"{query}\"", flush=True)
    print("=" * 65, flush=True)

    initial_state: BusinessState = {
        "question": query,
        "category": "",
        "customer_data": "",
        "complaint_data": "",
        "policy_context": "",
        "context": "",
        "decision": "",
        "ticket_result": "",
        "response": "",
    }

    result = await business_graph.ainvoke(initial_state)

    print(f"\n[CATEGORY]: {result.get('category')}", flush=True)

    if result.get("customer_data"):
        print(f"\n[MCP CUSTOMER DATA]:\n{result['customer_data']}", flush=True)

    if result.get("complaint_data"):
        print(f"\n[MCP COMPLAINT DATA]:\n{result['complaint_data']}", flush=True)

    if result.get("policy_context"):
        print(f"\n[RAG POLICY CONTEXT]:\n{result['policy_context']}", flush=True)

    print(f"\n[DECISION]: {result.get('decision')}", flush=True)

    if result.get("ticket_result"):
        print(f"\n[MCP TICKET RESULT]:\n{result['ticket_result']}", flush=True)

    print(f"\n[FINAL RESPONSE]:\n{result.get('response')}\n", flush=True)

    return result


async def main():
    print("*" * 65, flush=True)
    print("DCI AI BUSINESS ASSISTANT - STEP 9.4 TICKET WORKFLOW TESTS", flush=True)
    print("*" * 65, flush=True)

    # -------------------------------------------------------------
    # TEST 1: Ticket Creation Workflow
    # -------------------------------------------------------------
    res1 = await run_scenario(
        1,
        "Ticket Creation (Customer + Complaint + Policy + MCP Ticket)",
        "Ravi Kumar has a damaged product. Check his complaint and create a support ticket if required.",
    )
    assert res1["category"] == "business_support", f"Expected category 'business_support', got {res1['category']}"
    assert "Ravi Kumar" in res1.get("customer_data", ""), "Expected Ravi Kumar in customer_data"
    assert "Damaged product" in res1.get("complaint_data", ""), "Expected Damaged product in complaint_data"
    assert "support" in res1.get("policy_context", "").lower() or "refund" in res1.get("policy_context", "").lower(), "Expected policy context"
    assert res1.get("decision") == "CREATE_TICKET", f"Expected decision 'CREATE_TICKET', got {res1.get('decision')}"
    assert res1.get("ticket_result"), "Expected ticket_result to be populated from MCP server"
    assert "ticket_id" in res1["ticket_result"] or "T00" in res1["ticket_result"], "Expected ticket ID in ticket_result"
    assert "Ticket:" in res1.get("response", "") or "T00" in res1.get("response", ""), "Expected ticket ID in final response"
    print(">>> TEST 1 PASSED: Ticket created successfully through MCP Server.", flush=True)

    # -------------------------------------------------------------
    # TEST 2: Customer Only (No Ticket Created)
    # -------------------------------------------------------------
    res2 = await run_scenario(
        2,
        "Customer Details Only (No Ticket)",
        "Find the customer details for Ravi Kumar.",
    )
    assert res2["category"] == "customer", f"Expected category 'customer', got {res2['category']}"
    assert "Ravi Kumar" in res2.get("customer_data", ""), "Expected Ravi Kumar in customer_data"
    assert not res2.get("ticket_result"), f"No ticket should be created for lookup, got {res2.get('ticket_result')}"
    print(">>> TEST 2 PASSED: Customer details retrieved, no ticket created.", flush=True)

    # -------------------------------------------------------------
    # TEST 3: Policy Only (No Ticket Created)
    # -------------------------------------------------------------
    res3 = await run_scenario(
        3,
        "Policy Only (No Ticket)",
        "How many days do customers have to request a refund?",
    )
    assert res3["category"] == "policy", f"Expected category 'policy', got {res3['category']}"
    assert "refund" in res3.get("policy_context", "").lower(), "Expected refund policy context"
    assert not res3.get("ticket_result"), f"No ticket should be created for policy query, got {res3.get('ticket_result')}"
    print(">>> TEST 3 PASSED: Policy returned via RAG, no ticket created.", flush=True)

    # -------------------------------------------------------------
    # TEST 4: Missing Customer (Ticket Not Created)
    # -------------------------------------------------------------
    res4 = await run_scenario(
        4,
        "Missing Customer Ticket Request (Validation Guard)",
        "Create a ticket for a customer with a damaged product.",
    )
    assert res4.get("decision") == "MORE_INFORMATION_REQUIRED", f"Expected 'MORE_INFORMATION_REQUIRED', got {res4.get('decision')}"
    assert not res4.get("ticket_result"), f"No ticket should be created when customer is missing, got {res4.get('ticket_result')}"
    assert "customer name" in res4.get("response", "").lower() or "additional information" in res4.get("response", "").lower(), "Expected request for customer name"
    print(">>> TEST 4 PASSED: Missing customer intercepted, no ticket created.", flush=True)

    # -------------------------------------------------------------
    # TEST 5: General Question (No Ticket Created)
    # -------------------------------------------------------------
    res5 = await run_scenario(
        5,
        "General Question (No Ticket)",
        "What is Artificial Intelligence?",
    )
    assert res5["category"] == "general", f"Expected category 'general', got {res5['category']}"
    assert not res5.get("ticket_result"), "No ticket should be created for general query"
    assert not res5.get("customer_data"), "Customer data should not be called for general query"
    print(">>> TEST 5 PASSED: General route isolated, no ticket created.", flush=True)

    print("\n" + "*" * 65, flush=True)
    print("ALL 5 TICKET WORKFLOW INTEGRATION TESTS PASSED SUCCESSFULLY!", flush=True)
    print("*" * 65, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
