import asyncio
import os
import sys

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.langchain_agent import run_customer_agent


async def main():

    response = await run_customer_agent(
        "Find the customer details for Ravi Kumar."
    )

    print("\nAgent Response:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())