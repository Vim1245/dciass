"""
Test Suite for 100 Records & Required Scenarios:
1. Existing customer search ("Find Ravi Kumar")
2. Customer complaint search ("Show Ravi Kumar's complaint")
3. Status search across 100 records ("Which customers are inactive?")
4. Multiple records question ("Find David Miller")
5. Question for data that does not exist ("Find the customer details for Harry Potter")
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from graph.business_graph import business_graph


async def main():
    print("=" * 70, flush=True)
    print("TESTING DCI AI BUSINESS ASSISTANT - 100 RECORDS & WORKFLOW", flush=True)
    print("=" * 70, flush=True)

    # Test 1: Existing customer search
    print("\n[TEST 1] Existing Customer Search: 'Find Ravi Kumar'", flush=True)
    r1 = await business_graph.ainvoke({"question": "Find Ravi Kumar"})
    print("Decision:", r1.get("decision"), flush=True)
    print("Response:\n", r1.get("response"), flush=True)
    assert "Ravi Kumar" in r1.get("response", ""), "Expected 'Ravi Kumar' in response"
    assert "C001" in r1.get("response", "") or "Active" in r1.get("response", ""), "Expected customer details"
    print(">>> TEST 1 PASSED!", flush=True)

    # Test 2: Customer complaint search
    print("\n" + "=" * 70, flush=True)
    print("[TEST 2] Customer Complaint Search: \"Show Ravi Kumar's complaint\"", flush=True)
    r2 = await business_graph.ainvoke({"question": "Show Ravi Kumar's complaint"})
    print("Decision:", r2.get("decision"), flush=True)
    print("Response:\n", r2.get("response"), flush=True)
    assert "Damaged product" in r2.get("response", "") or "damaged" in r2.get("response", "").lower(), "Expected complaint issue"
    print(">>> TEST 2 PASSED!", flush=True)

    # Test 3: Status search across 100 records
    print("\n" + "=" * 70, flush=True)
    print("[TEST 3] Status Search: 'Which customers are inactive?'", flush=True)
    r3 = await business_graph.ainvoke({"question": "Which customers are inactive?"})
    print("Decision:", r3.get("decision"), flush=True)
    print("Response:\n", r3.get("response"), flush=True)
    assert any(name in r3.get("response", "") for name in ["Charlie Brown", "Arun Patel", "Ian Wright", "Kevin Zhao", "Inactive"]), "Expected inactive customers from database"
    print(">>> TEST 3 PASSED!", flush=True)

    # Test 4: Another customer search from the 100 records
    print("\n" + "=" * 70, flush=True)
    print("[TEST 4] Database Search for another customer (David Miller): 'Find David Miller'", flush=True)
    r4 = await business_graph.ainvoke({"question": "Find David Miller"})
    print("Decision:", r4.get("decision"), flush=True)
    print("Response:\n", r4.get("response"), flush=True)
    assert "David Miller" in r4.get("response", "") or "C007" in r4.get("response", ""), "Expected David Miller from 100 records"
    print(">>> TEST 4 PASSED!", flush=True)

    # Test 5: Missing data guard (Zero Hallucination)
    print("\n" + "=" * 70, flush=True)
    print("[TEST 5] Missing Data Search: 'Find the customer details for Harry Potter'", flush=True)
    r5 = await business_graph.ainvoke({"question": "Find the customer details for Harry Potter"})
    print("Decision:", r5.get("decision"), flush=True)
    print("Response:\n", r5.get("response"), flush=True)
    assert "not found" in r5.get("response", "").lower(), "Expected 'not found' statement"
    print(">>> TEST 5 PASSED!", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("ALL 5 TESTS COMPLETED AND VERIFIED SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
