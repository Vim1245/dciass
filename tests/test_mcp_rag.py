"""
DCI AI Business Assistant - MCP + RAG Integration Test Suite (STEP 9.3)

Tests:
1. TEST 1: Policy inquiry using RAG ('How many days do customers have to request a refund?')
2. TEST 2: Customer lookup using MCP ('Find the customer details for Ravi Kumar.')
3. TEST 3: Complaint lookup using MCP ('Check Ravi Kumar's complaint.')
4. TEST 4: Business support inquiry using MCP + RAG ('Ravi Kumar has a damaged product. Check his complaint and tell me whether he is eligible for a refund.')
5. TEST 5: General question without MCP/RAG ('What is Artificial Intelligence?')
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
        "response": "",
    }

    result = await business_graph.ainvoke(initial_state)

    print(f"\n[ROUTE / CATEGORY]: {result.get('category')}", flush=True)

    if result.get("customer_data"):
        print(f"\n[MCP CUSTOMER DATA]:\n{result['customer_data']}", flush=True)

    if result.get("complaint_data"):
        print(f"\n[MCP COMPLAINT DATA]:\n{result['complaint_data']}", flush=True)

    if result.get("policy_context"):
        print(f"\n[RAG POLICY CONTEXT]:\n{result['policy_context']}", flush=True)

    if result.get("decision"):
        print(f"\n[DECISION]: {result['decision']}", flush=True)

    print(f"\n[FINAL RESPONSE]:\n{result.get('response')}\n", flush=True)

    return result


async def main():
    print("*" * 65, flush=True)
    print("DCI AI BUSINESS ASSISTANT - STEP 9.3 MCP + RAG INTEGRATION TESTS", flush=True)
    print("*" * 65, flush=True)

    # -------------------------------------------------------------
    # TEST 1: Policy inquiry (RAG only)
    # -------------------------------------------------------------
    res1 = await run_scenario(
        1,
        "Policy Route (RAG Document Search)",
        "How many days do customers have to request a refund?",
    )
    assert res1["category"] == "policy", f"Expected category 'policy', got {res1['category']}"
    assert "refund" in res1.get("policy_context", "").lower() or "7 days" in res1.get("policy_context", "").lower(), "Expected refund policy context"
    assert len(res1.get("response", "")) > 10, "Expected non-empty policy response"
    print(">>> TEST 1 PASSED: Pure policy routed through RAG successfully.", flush=True)

    # -------------------------------------------------------------
    # TEST 2: Customer lookup (MCP only)
    # -------------------------------------------------------------
    res2 = await run_scenario(
        2,
        "Customer Route (MCP search_customer)",
        "Find the customer details for Ravi Kumar.",
    )
    assert res2["category"] == "customer", f"Expected category 'customer', got {res2['category']}"
    assert "Ravi Kumar" in res2.get("customer_data", ""), "Expected 'Ravi Kumar' in customer_data"
    assert "C001" in res2.get("customer_data", ""), "Expected 'C001' in customer_data"
    print(">>> TEST 2 PASSED: Pure customer inquiry routed through MCP successfully.", flush=True)

    # -------------------------------------------------------------
    # TEST 3: Complaint lookup (MCP only)
    # -------------------------------------------------------------
    res3 = await run_scenario(
        3,
        "Complaint Route (MCP search_complaint)",
        "Check Ravi Kumar's complaint.",
    )
    assert res3["category"] == "customer", f"Expected category 'customer', got {res3['category']}"
    assert "Damaged product" in res3.get("complaint_data", ""), "Expected 'Damaged product' in complaint_data"
    print(">>> TEST 3 PASSED: Complaint lookup routed through MCP successfully.", flush=True)

    # -------------------------------------------------------------
    # TEST 4: Combined Business Support (MCP + RAG + Ollama Analysis)
    # -------------------------------------------------------------
    res4 = await run_scenario(
        4,
        "Combined Business Support (MCP Customer & Complaint + RAG Refund Policy + Ollama)",
        "Ravi Kumar has a damaged product. Check his complaint and tell me whether he is eligible for a refund.",
    )
    assert res4["category"] == "business_support", f"Expected category 'business_support', got {res4['category']}"
    assert "Ravi Kumar" in res4.get("customer_data", ""), "Expected 'Ravi Kumar' in customer_data"
    assert "Damaged product" in res4.get("complaint_data", ""), "Expected 'Damaged product' in complaint_data"
    assert "refund" in res4.get("policy_context", "").lower() or "48 hours" in res4.get("policy_context", "").lower(), "Expected refund policy context"
    assert len(res4.get("response", "")) > 30, "Expected comprehensive business analysis response"
    print(">>> TEST 4 PASSED: Combined MCP + RAG business support workflow completed successfully.", flush=True)

    # -------------------------------------------------------------
    # TEST 5: General Route (No MCP, No RAG)
    # -------------------------------------------------------------
    res5 = await run_scenario(
        5,
        "General Route (Ollama only, No MCP, No RAG)",
        "What is Artificial Intelligence?",
    )
    assert res5["category"] == "general", f"Expected category 'general', got {res5['category']}"
    assert not res5.get("customer_data"), "Customer data must not be called for general queries"
    assert not res5.get("complaint_data"), "Complaint data must not be called for general queries"
    assert not res5.get("policy_context"), "Policy context must not be called for general queries"
    assert len(res5.get("response", "")) > 10, "Expected general knowledge answer"
    print(">>> TEST 5 PASSED: General route isolated from MCP and RAG successfully.", flush=True)

    print("\n" + "*" * 65, flush=True)
    print("ALL 5 MCP + RAG INTEGRATION TESTS PASSED SUCCESSFULLY!", flush=True)
    print("*" * 65, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
