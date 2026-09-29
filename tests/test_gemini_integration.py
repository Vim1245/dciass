"""
DCI AI Business Assistant - STEP 10 Google AI Studio (Gemini) Integration Tests

Tests:
1. Basic Gemini / LLM request: "Explain Artificial Intelligence in two simple sentences."
2. Customer request: "Find the customer details for Ravi Kumar."
3. Complaint request: "Check Ravi Kumar's complaint."
4. Policy request: "How many days do customers have to request a refund?"
5. Combined business request: "Ravi Kumar has a damaged product. Check his complaint against the refund policy and tell me what action should be taken."
6. Ticket request: "Ravi Kumar has a damaged product. Create a support ticket if the available information requires one."
7. Missing information: "Create a support ticket for a damaged product." -> MORE_INFORMATION_REQUIRED, no ticket created.
8. Provider Switching: Test both AI_PROVIDER=gemini and AI_PROVIDER=ollama using the same LangGraph workflow.
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
from backend.ai_service import generate_llm_response
from backend.gemini_service import is_gemini_available, generate_gemini_response
import backend.config as config


async def run_scenario(test_num: int, title: str, query: str, provider: str = "gemini") -> dict:
    print("\n" + "=" * 65, flush=True)
    print(f"TEST {test_num}: {title} [PROVIDER: {provider.upper()}]", flush=True)
    print(f"QUERY: \"{query}\"", flush=True)
    print("=" * 65, flush=True)

    # Configure provider for this scenario
    original_provider = config.AI_PROVIDER
    config.AI_PROVIDER = provider

    initial_state: BusinessState = {
        "question": query,
        "category": "",
        "customer_name": "",
        "required_actions": [],
        "customer_data": "",
        "complaint_data": "",
        "policy_context": "",
        "decision": "",
        "ticket_result": "",
        "response": "",
    }

    try:
        result = await business_graph.ainvoke(initial_state)
    finally:
        config.AI_PROVIDER = original_provider

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
    print("DCI AI BUSINESS ASSISTANT - STEP 10 GEMINI INTEGRATION TESTS", flush=True)
    print(f"Configured AI_PROVIDER: {config.AI_PROVIDER}", flush=True)
    print(f"Configured GEMINI_MODEL: {config.GEMINI_MODEL}", flush=True)
    print(f"Gemini API Key configured: {bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != 'your_google_ai_studio_api_key_here')}", flush=True)
    print("*" * 65, flush=True)

    # -------------------------------------------------------------
    # TEST 1: Basic Request (General Knowledge)
    # -------------------------------------------------------------
    res1 = await run_scenario(
        1,
        "Basic LLM Request",
        "Explain Artificial Intelligence in two simple sentences.",
        provider="gemini",
    )
    assert res1.get("category") == "general", f"Expected 'general', got {res1.get('category')}"
    assert not res1.get("customer_data"), "Expected no MCP customer data for general query"
    assert not res1.get("policy_context"), "Expected no RAG policy for general query"
    assert len(res1.get("response", "")) > 10, "Expected non-empty response"
    print(">>> TEST 1 PASSED: Basic request answered successfully.\n")

    # -------------------------------------------------------------
    # TEST 2: Customer Request (MCP Customer Lookup + Gemini)
    # -------------------------------------------------------------
    res2 = await run_scenario(
        2,
        "Customer Lookup Request",
        "Find the customer details for Ravi Kumar.",
        provider="gemini",
    )
    assert res2.get("category") == "customer", f"Expected 'customer', got {res2.get('category')}"
    assert "CUSTOMER_LOOKUP" in res2.get("required_actions", []), "Expected CUSTOMER_LOOKUP in actions"
    assert "Ravi Kumar" in res2.get("customer_data", ""), "Expected Ravi Kumar in customer_data"
    assert not res2.get("ticket_result"), "No ticket should be created for customer lookup"
    assert len(res2.get("response", "")) > 10, "Expected non-empty response"
    print(">>> TEST 2 PASSED: Customer lookup via MCP and LLM response verified.\n")

    # -------------------------------------------------------------
    # TEST 3: Complaint Request (MCP Complaint Lookup + Gemini)
    # -------------------------------------------------------------
    res3 = await run_scenario(
        3,
        "Complaint Lookup Request",
        "Check Ravi Kumar's complaint.",
        provider="gemini",
    )
    assert "COMPLAINT_LOOKUP" in res3.get("required_actions", []), "Expected COMPLAINT_LOOKUP in actions"
    assert "damaged" in res3.get("complaint_data", "").lower() or "screen" in res3.get("complaint_data", "").lower(), "Expected complaint data"
    assert not res2.get("ticket_result"), "No ticket should be created for complaint lookup"
    assert len(res3.get("response", "")) > 10, "Expected non-empty response"
    print(">>> TEST 3 PASSED: Complaint lookup via MCP and LLM response verified.\n")

    # -------------------------------------------------------------
    # TEST 4: Policy Request (RAG Policy Search + Gemini)
    # -------------------------------------------------------------
    res4 = await run_scenario(
        4,
        "Policy Information Request",
        "How many days do customers have to request a refund?",
        provider="gemini",
    )
    assert res4.get("category") == "policy", f"Expected 'policy', got {res4.get('category')}"
    assert any(a in res4.get("required_actions", []) for a in ("POLICY_SEARCH", "POLICY_LOOKUP")), "Expected POLICY_SEARCH in actions"
    assert res4.get("policy_context"), "Expected RAG policy context to be retrieved"
    assert not res4.get("customer_data"), "Customer data should not be queried for policy request"
    assert len(res4.get("response", "")) > 10, "Expected non-empty response"
    print(">>> TEST 4 PASSED: Policy retrieval via RAG and LLM response verified.\n")

    # -------------------------------------------------------------
    # TEST 5: Combined Business Request (MCP + RAG + Analysis)
    # -------------------------------------------------------------
    res5 = await run_scenario(
        5,
        "Combined Business Request",
        "Ravi Kumar has a damaged product. Check his complaint against the refund policy and tell me what action should be taken.",
        provider="gemini",
    )
    assert "CUSTOMER_LOOKUP" in res5.get("required_actions", []), "Expected CUSTOMER_LOOKUP in actions"
    assert "COMPLAINT_LOOKUP" in res5.get("required_actions", []), "Expected COMPLAINT_LOOKUP in actions"
    assert any(a in res5.get("required_actions", []) for a in ("POLICY_SEARCH", "POLICY_LOOKUP")), "Expected POLICY_SEARCH in actions"
    assert res5.get("customer_data"), "Expected customer data"
    assert res5.get("complaint_data"), "Expected complaint data"
    assert res5.get("policy_context"), "Expected policy context"
    assert res5.get("decision") in ("CREATE_TICKET", "MORE_INFORMATION_REQUIRED", "NO_ACTION"), "Expected valid decision"
    if res5.get("decision") == "CREATE_TICKET":
        assert res5.get("ticket_result"), "Expected ticket result when decision is CREATE_TICKET"
    print(">>> TEST 5 PASSED: Combined business analysis verified.\n")

    # -------------------------------------------------------------
    # TEST 6: Ticket Request (Justified Ticket Creation)
    # -------------------------------------------------------------
    res6 = await run_scenario(
        6,
        "Ticket Creation Request",
        "Ravi Kumar has a damaged product. Create a support ticket if the available information requires one.",
        provider="gemini",
    )
    assert res6.get("decision") == "CREATE_TICKET", f"Expected CREATE_TICKET, got {res6.get('decision')}"
    assert "ticket_id" in res6.get("ticket_result", "").lower() or "t0" in res6.get("ticket_result", "").lower(), "Expected ticket ID"
    print(">>> TEST 6 PASSED: Ticket creation workflow executed successfully.\n")

    # -------------------------------------------------------------
    # TEST 7: Missing Information Guard
    # -------------------------------------------------------------
    res7 = await run_scenario(
        7,
        "Missing Information Guard",
        "Create a support ticket for a damaged product.",
        provider="gemini",
    )
    assert res7.get("decision") == "MORE_INFORMATION_REQUIRED", f"Expected MORE_INFORMATION_REQUIRED, got {res7.get('decision')}"
    assert not res7.get("ticket_result"), "Ticket must NOT be created when information is missing"
    assert len(res7.get("response", "")) > 10, "Expected prompt requesting missing customer details"
    print(">>> TEST 7 PASSED: Guard against missing information verified.\n")

    # -------------------------------------------------------------
    # TEST 8: Provider Switching (Ollama vs Gemini)
    # -------------------------------------------------------------
    print("\n" + "=" * 65, flush=True)
    print("TEST 8: Provider Switching Verification (AI_PROVIDER=ollama)", flush=True)
    print("=" * 65, flush=True)
    res8 = await run_scenario(
        8,
        "Ollama Provider Test",
        "How many days do customers have to request a refund?",
        provider="ollama",
    )
    assert res8.get("category") == "policy", f"Expected 'policy', got {res8.get('category')}"
    assert res8.get("policy_context"), "Expected RAG policy context"
    assert len(res8.get("response", "")) > 10, "Expected non-empty response from Ollama provider"
    print(">>> TEST 8 PASSED: LangGraph executed identical workflow seamlessly with AI_PROVIDER=ollama.\n")

    print("=" * 65, flush=True)
    print("ALL STEP 10 GEMINI INTEGRATION TESTS PASSED SUCCESSFULLY!", flush=True)
    print("=" * 65, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
