import asyncio
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph.business_graph import business_graph
from graph.state import BusinessState
from agents.langchain_agent import run_customer_agent

TEST_QUERIES = [
    "find Manoj Kumar",
    "find Manoj",
    "find customer C012",
    "what is Manoj Kumar's email?",
]

async def test_langgraph():
    print("=" * 70)
    print("TESTING LANGGRAPH (FastAPI /api/assistant workflow)")
    print("=" * 70)
    for q in TEST_QUERIES:
        print(f"\n[QUERY]: '{q}'")
        state_input: BusinessState = {
            "question": q,
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
        res = await business_graph.ainvoke(state_input)
        print(f"[DECISION]: {res.get('decision')}")
        print(f"[CATEGORY]: {res.get('category')}")
        print(f"[RESPONSE]:\n{res.get('response')}\n")
        print("-" * 70)

async def test_langchain():
    print("\n" + "=" * 70)
    print("TESTING LANGCHAIN AGENT (/agent endpoint)")
    print("=" * 70)
    for q in TEST_QUERIES:
        print(f"\n[QUERY]: '{q}'")
        res = await run_customer_agent(q)
        print(f"[RESPONSE]:\n{res}\n")
        print("-" * 70)

async def main():
    await test_langgraph()
    await test_langchain()

if __name__ == "__main__":
    asyncio.run(main())
