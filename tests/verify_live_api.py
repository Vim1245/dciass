import sys
from pathlib import Path
import httpx

API_URL = "http://127.0.0.1:8000/api/assistant"

QUERIES = [
    "find Manoj Kumar",
    "find Manoj",
    "find customer C012",
    "what is Manoj Kumar's email?"
]

print("=" * 80)
print("VERIFYING ALL 4 QUERIES AGAINST LIVE FASTAPI BACKEND (/api/assistant)")
print("=" * 80)

for q in QUERIES:
    print(f"\n[SENDING QUERY]: '{q}'")
    try:
        resp = httpx.post(API_URL, json={"message": q}, timeout=180.0)
        data = resp.json()
        print(f"HTTP Status: {resp.status_code}")
        print(f"Decision: {data.get('decision')}")
        print("Response:\n" + data.get("response", ""))
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 80)
