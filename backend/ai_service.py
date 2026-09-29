"""
DCI AI Business Assistant - AI Provider Abstraction Layer

Provides a unified interface for LLM operations supporting:
1. Google Gemini (Google AI Studio) via official `google-genai` SDK
2. Ollama (local open-source models e.g. llama3.2) as fallback or local provider

Selected via environment variable `AI_PROVIDER` ('gemini' or 'ollama').
"""

import asyncio
import logging
import os
from typing import Optional

import ollama

from backend.config import AI_PROVIDER, OLLAMA_MODEL
from prompts.prompt_builder import build_prompt
from prompts.system_prompts import BUSINESS_ASSISTANT_PROMPT

logger = logging.getLogger("dci.ai_service")


async def check_ollama_status() -> str:
    """Check if the local Ollama instance is reachable and healthy."""
    try:
        await asyncio.wait_for(asyncio.to_thread(ollama.list), timeout=2.0)
        return "available"
    except Exception:
        return "unavailable"


def get_active_provider() -> str:
    """Return the currently configured AI provider ('ollama')."""
    return (os.getenv("AI_PROVIDER") or AI_PROVIDER).strip().lower()


async def generate_ollama_response(
    message: str,
    context: Optional[str] = None,
    system_instruction: Optional[str] = None,
) -> str:
    """
    Clean reusable Ollama service layer (STEP 10.2):
    - Accepts a user message.
    - Accepts optional context.
    - Sends the request to Ollama using configured OLLAMA_MODEL.
    - Returns the generated response.
    - Handles Ollama errors gracefully.
    - Never exposes internal prompts.
    - Never exposes stack traces to the user.
    """
    model_name = os.getenv("OLLAMA_MODEL") or OLLAMA_MODEL
    logger.info("Generating response using Ollama model: %s", model_name)

    messages = []
    if system_instruction and system_instruction.strip():
        messages.append({"role": "system", "content": system_instruction.strip()})

    user_content = message.strip() if message else ""
    if context and context.strip():
        user_content = f"Context:\n{context.strip()}\n\nQuestion/Request:\n{user_content}"

    messages.append({"role": "user", "content": user_content})

    try:
        # Wrap synchronous ollama.chat in thread pool for non-blocking async execution
        result = await asyncio.to_thread(
            ollama.chat,
            model=model_name,
            messages=messages,
        )
        return (result.get("message", {}).get("content") or "").strip()
    except Exception as e:
        logger.error("Ollama execution failed: %s", type(e).__name__)
        return "The AI reasoning service is currently unavailable. Please verify that Ollama is running and try again."


async def generate_llm_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    allow_fallback: bool = True,
) -> str:
    """
    Unified entry point for Ollama LLM inference.
    Delegates to the reusable Ollama service layer.
    """
    return await generate_ollama_response(
        message=prompt,
        system_instruction=system_instruction,
    )


async def generate_response(
    message: str,
    context: str = "",
) -> str:
    """
    Standard generation helper for user chat queries.
    Accepts a user message and optional context, builds structured prompt,
    and returns Ollama's response safely.
    """
    prompt = build_prompt(
        user_message=message,
        context=context,
    )
    return await generate_ollama_response(
        message=prompt,
        system_instruction=BUSINESS_ASSISTANT_PROMPT,
    )