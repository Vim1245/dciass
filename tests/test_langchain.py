import asyncio
import os
import sys 

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.langchain_service import generate_langchain_response


async def main():
    print("Starting LangChain + Ollama test...")

    response = await generate_langchain_response(
        "What is the role of an AI Business Assistant?"
    )
    print("\nAI Response:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())