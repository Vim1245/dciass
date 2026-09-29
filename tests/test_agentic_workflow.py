"""
DCI AI Business Assistant - STEP 9.5 Complete Agentic Workflow Test Suite

Verifies 8 Agentic Scenarios:
1. TEST 1 (Customer Lookup): MCP customer search only, no unnecessary RAG, no ticket.
2. TEST 2 (Complaint Lookup): MCP complaint search, no unnecessary ticket.
3. TEST 3 (Policy Question): RAG policy search only, no MCP ticket.
4. TEST 4 (Combined Business Analysis): MCP customer + complaint + RAG policy + Ollama analysis. No ticket created.
5. TEST 5 (Ticket Workflow): MCP + RAG + Ollama + Decision (CREATE_TICKET) + MCP Ticket creation.
6. TEST 6 (Missing Information): No ticket created, requests missing customer details.
7. TEST 7 (General Question): Ollama only, no MCP or RAG calls.
8. TEST 8 (Unknown Customer): Customer not found, no ticket created.
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
        "customer_name": "",
        "required_actions": [],
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
    print(f"[REQUIRED ACTIONS]: {result.get('required_actions')}", flush=True)

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
    print("DCI AI BUSINESS ASSISTANT - COMPLETE AGENTIC WORKFLOW TESTS", flush=True)
    print("*" * 65, flush=True)

    # -------------------------------------------------------------
    # TEST 1: Customer Lookup
    # -------------------------------------------------------------
    res1 = await run_scenario(
        1,
        "Customer Lookup",
        "Find the customer details for Ravi Kumar.",
    )
    assert res1.get("category") == "customer", f"Expected category 'customer', got {res1.get('category')}"
    assert "CUSTOMER_LOOKUP" in res1.get("required_actions", []), "Expected CUSTOMER_LOOKUP in actions"
    assert "Ravi Kumar" in res1.get("customer_data", ""), "Expected Ravi Kumar in customer_data"
    assert not res1.get("policy_context"), "RAG policy should NOT be called for simple customer lookup"
    assert not res1.get("ticket_result"), "No ticket should be created for customer lookup"
    print(">>> TEST 1 PASSED: MCP customer search executed with no unnecessary RAG or ticket.", flush=True)

    # -------------------------------------------------------------
    # TEST 2: Complaint Lookup
    # -------------------------------------------------------------
    res2 = await run_scenario(
        2,
        "Complaint Lookup",
        "Check Ravi Kumar's complaint.",
    )
    assert "COMPLAINT_LOOKUP" in res2.get("required_actions", []), "Expected COMPLAINT_LOOKUP in actions"
    assert "Damaged product" in res2.get("complaint_data", ""), "Expected Damaged product in complaint_data"
    assert not res1.get("ticket_result"), "No ticket should be created for complaint lookup"
    print(">>> TEST 2 PASSED: MCP complaint search executed with no unnecessary ticket.", flush=True)

    # -------------------------------------------------------------
    # TEST 3: Policy Question
    # -------------------------------------------------------------
    res3 = await run_scenario(
        3,
        "Policy Question",
        "How many days do customers have to request a refund?",
    )
    assert res3.get("category") == "policy", f"Expected category 'policy', got {res3.get('category')}"
    assert "POLICY_SEARCH" in res3.get("required_actions", []), "Expected POLICY_SEARCH in actions"
    assert "refund" in res3.get("policy_context", "").lower(), "Expected refund policy context"
    assert not res3.get("customer_data"), "Customer data should NOT be called for policy question"
    assert not res3.get("ticket_result"), "No ticket should be created for policy question"
    print(">>> TEST 3 PASSED: RAG policy search executed with no MCP calls.", flush=True)

    # -------------------------------------------------------------
    # TEST 4: Combined Business Analysis (No Ticket)
    # -------------------------------------------------------------
    res4 = await run_scenario(
        4,
        "Combined Business Analysis",
        "Ravi Kumar has a damaged product. Check his complaint against the refund policy.",
    )
    assert "CUSTOMER_LOOKUP" in res4.get("required_actions", []), "Expected CUSTOMER_LOOKUP"
    assert "COMPLAINT_LOOKUP" in res4.get("required_actions", []), "Expected COMPLAINT_LOOKUP"
    assert "POLICY_SEARCH" in res4.get("required_actions", []), "Expected POLICY_SEARCH"
    assert "Ravi Kumar" in res4.get("customer_data", ""), "Expected Ravi Kumar in customer_data"
    assert "Damaged product" in res4.get("complaint_data", ""), "Expected Damaged product in complaint_data"
    assert "refund" in res4.get("policy_context", "").lower(), "Expected refund policy context"
    assert not res4.get("ticket_result"), "No ticket should be created when only analysis is requested"
    print(">>> TEST 4 PASSED: Combined analysis completed without ticket creation.", flush=True)

    # -------------------------------------------------------------
    # TEST 5: Ticket Workflow
    # -------------------------------------------------------------
    res5 = await run_scenario(
        5,
        "Ticket Workflow",
        "Ravi Kumar has a damaged product. Check the available information and create a support ticket if required.",
    )
    assert "TICKET_CREATION" in res5.get("required_actions", []), "Expected TICKET_CREATION in actions"
    assert res5.get("decision") == "CREATE_TICKET", f"Expected decision 'CREATE_TICKET', got {res5.get('decision')}"
    assert res5.get("ticket_result"), "Expected ticket_result from MCP"
    assert "ticket_id" in res5["ticket_result"] or "T00" in res5["ticket_result"], "Expected ticket ID in ticket_result"
    assert "T00" in res5.get("response", ""), "Expected ticket ID in final response"
    print(">>> TEST 5 PASSED: Full MCP + RAG + Ticket Creation workflow completed.", flush=True)

    # -------------------------------------------------------------
    # TEST 6: Missing Customer Information
    # -------------------------------------------------------------
    res6 = await run_scenario(
        6,
        "Missing Customer Information Guard",
        "Create a support ticket for a damaged product.",
    )
    assert res6.get("decision") == "MORE_INFORMATION_REQUIRED", f"Expected 'MORE_INFORMATION_REQUIRED', got {res6.get('decision')}"
    assert not res6.get("ticket_result"), "No ticket should be created when customer name is missing"
    assert "customer name" in res6.get("response", "").lower(), "Expected response to request customer name"
    print(">>> TEST 6 PASSED: Missing customer intercepted, no ticket created.", flush=True)

    # -------------------------------------------------------------
    # TEST 7: General Question
    # -------------------------------------------------------------
    res7 = await run_scenario(
        7,
        "General Question",
        "What is Artificial Intelligence?",
    )
    assert res7.get("category") == "general", f"Expected category 'general', got {res7.get('category')}"
    assert not res7.get("customer_data"), "Customer data should NOT be called for general query"
    assert not res7.get("complaint_data"), "Complaint data should NOT be called for general query"
    assert not res7.get("policy_context"), "Policy context should NOT be called for general query"
    assert not res7.get("ticket_result"), "No ticket should be created for general query"
    print(">>> TEST 7 PASSED: General route isolated from MCP and RAG.", flush=True)

    # -------------------------------------------------------------
    # TEST 8: Unknown Customer
    # -------------------------------------------------------------
    res8 = await run_scenario(
        8,
        "Unknown Customer Lookup",
        "Find the customer details for John Smith.",
    )
    assert "CUSTOMER_LOOKUP" in res8.get("required_actions", []), "Expected CUSTOMER_LOOKUP in actions"
    assert "customer not found" in res8.get("customer_data", "").lower(), "Expected customer not found in customer_data"
    assert not res8.get("ticket_result"), "No ticket should be created for unknown customer"
    assert "not found" in res8.get("response", "").lower(), "Expected 'not found' in response"
    print(">>> TEST 8 PASSED: Unknown customer handled safely, no ticket created.", flush=True)

    print("\n" + "*" * 65, flush=True)
    print("ALL 8 AGENTIC WORKFLOW TESTS PASSED SUCCESSFULLY!", flush=True)
    print("*" * 65, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
