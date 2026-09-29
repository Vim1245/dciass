"""
DCI AI Business Assistant - Google Gemini Service
Provides Gemini API integration using the official google-genai SDK.
"""

import logging
import os
from typing import Optional

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("dci.gemini")


def is_gemini_available() -> bool:
    """Check if a valid Gemini API key is configured."""
    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    return bool(api_key and api_key != "your_google_ai_studio_api_key_here")


async def generate_gemini_response(
    message: str,
    context: Optional[str] = None,
    system_instruction: Optional[str] = None,
) -> str:
    """
    Generate response using Google Gemini.
    Gracefully handles missing keys and execution errors.
    """
    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if not api_key or api_key == "your_google_ai_studio_api_key_here":
        return "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment."

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL") or GEMINI_MODEL

        prompt_text = message.strip() if message else ""
        if context and context.strip():
            prompt_text = f"Context:\n{context.strip()}\n\nQuestion/Request:\n{prompt_text}"

        response = client.models.generate_content(
            model=model_name,
            contents=prompt_text,
        )
        return (response.text or "").strip()
    except Exception as e:
        logger.error("Gemini generation error: %s", e)
        return "The Gemini AI reasoning service is currently unavailable."
