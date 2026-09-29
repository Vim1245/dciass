import httpx

base_url = "http://127.0.0.1:8000"
queries = [
    "Find Ravi Kumar",
    "Show Ravi Kumar's complaint",
    "Which customers are inactive?",
    "Find David Miller",
    "Find the customer details for Harry Potter"
]

print("=" * 65, flush=True)
print("TESTING LIVE FASTAPI ENDPOINT (POST /api/assistant)", flush=True)
print("=" * 65, flush=True)

with httpx.Client(base_url=base_url, timeout=60.0) as client:
    for q in queries:
        print("\n" + "-" * 50, flush=True)
        print("QUERY:", q, flush=True)
        res = client.post("/api/assistant", json={"message": q})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        print("DECISION:", data.get("decision"), flush=True)
        print("RESPONSE:\n", data.get("response"), flush=True)

print("\n" + "=" * 65, flush=True)
print("LIVE API ENDPOINT TEST COMPLETED SUCCESSFULLY!", flush=True)
print("=" * 65, flush=True)
