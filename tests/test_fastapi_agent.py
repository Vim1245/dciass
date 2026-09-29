"""
DCI AI Business Assistant - STEP 10 FastAPI + Full Agentic Integration Tests

Verifies the FastAPI gateway as the main entry point for the Agentic AI Business Assistant:
1. GET /health (Health & Ollama status)
2. POST /api/assistant - Customer request ("Find the customer details for Ravi Kumar.")
3. POST /api/assistant - Policy request ("How many days do customers have to request a refund?")
4. POST /api/assistant - Combined request ("Ravi Kumar has a damaged product. Check his complaint against the refund policy.")
5. POST /api/assistant - Ticket request ("Ravi Kumar has a damaged product. Create a support ticket if required.")
6. POST /api/assistant - Missing customer guard ("Create a support ticket for a damaged product.")
7. POST /api/assistant - General question ("What is Artificial Intelligence?")
8. POST /api/assistant - Unknown customer ("Find the customer details for John Smith.")
9. Request Validation Tests (Empty message, Missing message, Extremely large message, Invalid JSON)
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

import httpx
from backend.main import app


async def test_health_check(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 1: Health Check (GET /health)", flush=True)
    print("=" * 65, flush=True)

    response = await client.get("/health")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    print("Response JSON:", data, flush=True)
    assert data.get("status") == "healthy", f"Expected status healthy, got {data.get('status')}"
    assert data.get("ollama") in ("available", "unavailable"), f"Unexpected ollama status: {data.get('ollama')}"
    print(">>> TEST 1 PASSED: Health check verified successfully.", flush=True)


async def test_customer_request(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 2: Customer Request (POST /api/assistant)", flush=True)
    print("QUERY: \"Find the customer details for Ravi Kumar.\"", flush=True)
    print("=" * 65, flush=True)

    payload = {"message": "Find the customer details for Ravi Kumar."}
    response = await client.post("/api/assistant", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    print("[MESSAGE]:", data.get("message"), flush=True)
    print("[DECISION]:", data.get("decision"), flush=True)
    print("[RESPONSE]:", data.get("response"), flush=True)
    assert "Ravi Kumar" in data.get("response", ""), "Expected Ravi Kumar in response"
    assert data.get("decision") in ("NO_ACTION", "MORE_INFORMATION_REQUIRED")
    assert not data.get("ticket"), f"No ticket should be created for customer lookup, got {data.get('ticket')}"
    print(">>> TEST 2 PASSED: Customer request routed through LangGraph, MCP, and Ollama.", flush=True)


async def test_policy_request(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 3: Policy Request (POST /api/assistant)", flush=True)
    print("QUERY: \"How many days do customers have to request a refund?\"", flush=True)
    print("=" * 65, flush=True)

    payload = {"message": "How many days do customers have to request a refund?"}
    response = await client.post("/api/assistant", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    print("[MESSAGE]:", data.get("message"), flush=True)
    print("[DECISION]:", data.get("decision"), flush=True)
    print("[RESPONSE]:", data.get("response"), flush=True)
    assert "7" in data.get("response", "") or "refund" in data.get("response", "").lower(), "Expected refund policy timeframe in response"
    assert data.get("decision") == "NO_ACTION"
    assert not data.get("ticket"), "No ticket should be created for policy query"
    print(">>> TEST 3 PASSED: Policy request answered via RAG and Ollama.", flush=True)


async def test_combined_request(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 4: Combined Business Request (POST /api/assistant)", flush=True)
    print("QUERY: \"Ravi Kumar has a damaged product. Check his complaint against the refund policy.\"", flush=True)
    print("=" * 65, flush=True)

    payload = {"message": "Ravi Kumar has a damaged product. Check his complaint against the refund policy."}
    response = await client.post("/api/assistant", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    print("[MESSAGE]:", data.get("message"), flush=True)
    print("[DECISION]:", data.get("decision"), flush=True)
    print("[RESPONSE]:", data.get("response"), flush=True)
    assert len(data.get("response", "")) > 20, "Expected detailed response from Ollama"
    assert not data.get("ticket"), "Ticket should not be created unless explicitly instructed"
    print(">>> TEST 4 PASSED: Combined analysis executed across MCP, RAG, and Ollama.", flush=True)


async def test_ticket_request(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 5: Ticket Creation Request (POST /api/assistant)", flush=True)
    print("QUERY: \"Ravi Kumar has a damaged product. Create a support ticket if required.\"", flush=True)
    print("=" * 65, flush=True)

    payload = {"message": "Ravi Kumar has a damaged product. Create a support ticket if required."}
    response = await client.post("/api/assistant", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    print("[MESSAGE]:", data.get("message"), flush=True)
    print("[DECISION]:", data.get("decision"), flush=True)
    print("[TICKET]:", data.get("ticket"), flush=True)
    print("[RESPONSE]:", data.get("response"), flush=True)
    assert data.get("decision") == "CREATE_TICKET", f"Expected CREATE_TICKET, got {data.get('decision')}"
    assert data.get("ticket"), "Expected ticket details in response"
    assert "T00" in data.get("ticket", "") or "ticket_id" in data.get("ticket", ""), "Expected ticket ID"
    assert "T00" in data.get("response", "") or "ticket" in data.get("response", "").lower(), "Expected ticket mention in response"
    print(">>> TEST 5 PASSED: Full agentic workflow created ticket via MCP server.", flush=True)


async def test_missing_customer(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 6: Missing Customer Guard (POST /api/assistant)", flush=True)
    print("QUERY: \"Create a support ticket for a damaged product.\"", flush=True)
    print("=" * 65, flush=True)

    payload = {"message": "Create a support ticket for a damaged product."}
    response = await client.post("/api/assistant", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    print("[MESSAGE]:", data.get("message"), flush=True)
    print("[DECISION]:", data.get("decision"), flush=True)
    print("[RESPONSE]:", data.get("response"), flush=True)
    assert data.get("decision") == "MORE_INFORMATION_REQUIRED", f"Expected MORE_INFORMATION_REQUIRED, got {data.get('decision')}"
    assert not data.get("ticket"), f"Ticket should NOT be created without customer info, got {data.get('ticket')}"
    assert "customer" in data.get("response", "").lower() or "information" in data.get("response", "").lower()
    print(">>> TEST 6 PASSED: Missing customer guard validated safely.", flush=True)


async def test_general_question(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 7: General Question (POST /api/assistant)", flush=True)
    print("QUERY: \"What is Artificial Intelligence?\"", flush=True)
    print("=" * 65, flush=True)

    payload = {"message": "What is Artificial Intelligence?"}
    response = await client.post("/api/assistant", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    print("[MESSAGE]:", data.get("message"), flush=True)
    print("[DECISION]:", data.get("decision"), flush=True)
    print("[RESPONSE]:", data.get("response")[:120] + "...", flush=True)
    assert data.get("decision") == "NO_ACTION"
    assert not data.get("ticket"), "Ticket should not be created for general question"
    assert len(data.get("response", "")) > 30, "Expected comprehensive answer from Ollama"
    print(">>> TEST 7 PASSED: General reasoning query handled through Ollama.", flush=True)


async def test_unknown_customer(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 8: Unknown Customer Lookup (POST /api/assistant)", flush=True)
    print("QUERY: \"Find the customer details for John Smith.\"", flush=True)
    print("=" * 65, flush=True)

    payload = {"message": "Find the customer details for John Smith."}
    response = await client.post("/api/assistant", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    print("[MESSAGE]:", data.get("message"), flush=True)
    print("[DECISION]:", data.get("decision"), flush=True)
    print("[RESPONSE]:", data.get("response"), flush=True)
    assert "not found" in data.get("response", "").lower() or "no account" in data.get("response", "").lower()
    assert data.get("decision") in ("NO_ACTION", "MORE_INFORMATION_REQUIRED")
    assert not data.get("ticket"), "No ticket should be created for unknown customer"
    print(">>> TEST 8 PASSED: Unknown customer handled safely without errors.", flush=True)


async def test_request_validation(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 9: Request Validation Guards", flush=True)
    print("=" * 65, flush=True)

    # 1. Empty message
    r1 = await client.post("/api/assistant", json={"message": "   "})
    print("Empty message status:", r1.status_code, "Detail:", r1.json().get("detail"))
    assert r1.status_code == 400, f"Expected 400 Bad Request, got {r1.status_code}"
    assert "empty" in r1.json().get("detail", "").lower()

    # 2. Missing message field
    r2 = await client.post("/api/assistant", json={})
    print("Missing message status:", r2.status_code, "Detail:", r2.json().get("detail"))
    assert r2.status_code in (400, 422), f"Expected 400 or 422, got {r2.status_code}"

    # 3. Extremely large message (> 10,000 chars)
    r3 = await client.post("/api/assistant", json={"message": "A" * 12000})
    print("Extremely large message status:", r3.status_code, "Detail:", r3.json().get("detail"))
    assert r3.status_code == 400, f"Expected 400 Bad Request, got {r3.status_code}"

    # 4. Invalid JSON
    r4 = await client.post(
        "/api/assistant",
        content="invalid-json-string",
        headers={"Content-Type": "application/json"}
    )
    print("Invalid JSON status:", r4.status_code, "Detail:", r4.json().get("detail"))
    assert r4.status_code in (400, 422), f"Expected 400 or 422, got {r4.status_code}"

    print(">>> TEST 9 PASSED: All validation guards enforced cleanly without tracebacks.", flush=True)


async def test_openapi_documentation(client: httpx.AsyncClient):
    print("\n" + "=" * 65, flush=True)
    print("TEST 10: OpenAPI & Swagger Documentation (GET /docs, /openapi.json)", flush=True)
    print("=" * 65, flush=True)

    # 1. Verify /docs returns 200 OK
    r_docs = await client.get("/docs")
    assert r_docs.status_code == 200, f"Expected 200 OK from /docs, got {r_docs.status_code}"
    assert "swagger-ui" in r_docs.text.lower() or "html" in r_docs.text.lower()
    print("GET /docs Status:", r_docs.status_code, "HTML UI verified.")

    # 2. Verify OpenAPI spec
    r_spec = await client.get("/openapi.json")
    assert r_spec.status_code == 200, f"Expected 200 OK from /openapi.json, got {r_spec.status_code}"
    spec = r_spec.json()

    assert "/api/assistant" in spec.get("paths", {}), "Expected /api/assistant in OpenAPI paths"
    endpoint_spec = spec["paths"]["/api/assistant"]["post"]
    print("Endpoint summary:", endpoint_spec.get("summary"))

    schemas = spec.get("components", {}).get("schemas", {})
    assert "AssistantRequest" in schemas, "Expected AssistantRequest schema"
    assert "AssistantResponse" in schemas, "Expected AssistantResponse schema"

    req_props = list(schemas["AssistantRequest"]["properties"].keys())
    resp_props = list(schemas["AssistantResponse"]["properties"].keys())
    print("AssistantRequest properties:", req_props)
    print("AssistantResponse properties:", resp_props)

    assert "message" in req_props, "Expected 'message' in AssistantRequest"
    assert "response" in resp_props, "Expected 'response' in AssistantResponse"
    assert "decision" in resp_props, "Expected 'decision' in AssistantResponse"
    assert "ticket" in resp_props, "Expected 'ticket' in AssistantResponse"

    print(">>> TEST 10 PASSED: FastAPI Swagger documentation and schemas fully validated.", flush=True)


async def main():
    print("*" * 65, flush=True)
    print("DCI AI BUSINESS ASSISTANT - FASTAPI AGENT INTEGRATION TESTS", flush=True)
    print("*" * 65, flush=True)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=90.0) as client:
        await test_health_check(client)
        await test_customer_request(client)
        await test_policy_request(client)
        await test_combined_request(client)
        await test_ticket_request(client)
        await test_missing_customer(client)
        await test_general_question(client)
        await test_unknown_customer(client)
        await test_request_validation(client)
        await test_openapi_documentation(client)

    print("\n" + "*" * 65, flush=True)
    print("ALL 10 FASTAPI AGENT INTEGRATION TESTS COMPLETED SUCCESSFULLY!", flush=True)
    print("*" * 65, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
