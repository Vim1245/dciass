# DCI AI Business Assistant - Configuration
import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "DCI AI Business Assistant")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# AI Provider Configuration (Ollama is the primary local provider)
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")