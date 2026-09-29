import asyncio
import os
import sys

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.rag_chain import answer_with_rag


async def main():

    question = (
        "How many days do customers have "
        "to request a refund?"
    )

    response = await answer_with_rag(
        question
    )

    print("\nRAG Answer:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())