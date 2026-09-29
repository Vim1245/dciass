import asyncio
import os
import sys

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph.business_graph import business_graph
from graph.state import BusinessState


async def test_query(question: str):

    initial_state: BusinessState = {
        "question": question,
        "category": "",
        "context": "",
        "response": ""
    }

    result = await business_graph.ainvoke(
        initial_state
    )

    print("\nQuestion:")
    print(question)

    print("\nCategory:")
    print(result["category"])

    print("\nResponse:")
    print(result["response"])


async def main():

    await test_query(
        "Find the customer details for Ravi Kumar."
    )

    await test_query(
        "How many days do I have to request a refund?"
    )

    await test_query(
        "What is Artificial Intelligence?"
    )


if __name__ == "__main__":
    asyncio.run(main())