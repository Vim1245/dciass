"""
DCI AI Business Assistant - LangChain Prompts

Contains LangChain ChatPromptTemplate definitions for structured messaging.
"""

from langchain_core.prompts import ChatPromptTemplate

# Reusable ChatPromptTemplate for the DCI Business Assistant
BUSINESS_CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a professional DCI Business Assistant. "
                "Please follow these guidelines:\n"
                "- Be accurate and professional.\n"
                "- Do not invent business information.\n"
                "- If information is unavailable, clearly say so.\n"
                "- Keep answers concise."
            ),
        ),
        (
            "user",
            "{message}",
        ),
    ]
)
