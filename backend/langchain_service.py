"""
DCI AI Business Assistant - LangChain Service

Handles communication with the local Ollama model using LangChain LCEL chains with output parsing.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from backend.config import OLLAMA_MODEL
from prompts.langchain_prompts import BUSINESS_CHAT_PROMPT

# Create the ChatOllama model instance
model = ChatOllama(model=OLLAMA_MODEL)

# Create a string output parser to extract clean text responses
parser = StrOutputParser()

# Build the LCEL chain by piping prompt -> model -> parser
chain = BUSINESS_CHAT_PROMPT | model | parser


async def generate_langchain_response(message: str) -> str:
    """
    Send a user message to the local Ollama model via LangChain LCEL chain.

    Args:
        message: The input user query string.

    Returns:
        The parsed response string from the model.
    """
    response = await chain.ainvoke({"message": message})

    # Return the parsed plain text response
    return str(response)
