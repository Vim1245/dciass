# DCI AI Business Assistant

Enterprise Multi-Agent Business Assistant powered by **FastAPI**, **LangGraph**, **Ollama (`llama3.2`)**, **Model Context Protocol (MCP)**, **ChromaDB RAG**, and **CrewAI**.

Completely local and private: No cloud API keys, no paid subscriptions, no data sent to external AI servers.

---

## Architecture Overview

```
                      Client / API Request
                               ↓
                            FastAPI
                               ↓
                           LangGraph
                               ↓
                     Request Understanding
                               ↓
              ┌────────────────┼────────────────┐
              │                │                │
              ↓                ↓                ↓
             MCP              RAG             Ollama
              │                │                │
        Customer Data      Policies       Reasoning
        Complaints                         Decision
        Tickets                                │
              │                └───────────────┘
              │
              ↓
         Business Action
              │
        create_ticket
              │
              ↓
        Final Response
```

---

## Core Components

1. **FastAPI Gateway**: Main API entry point with CORS, request validation, structured responses, and Swagger UI at `/docs`.
2. **LangGraph Agentic Orchestrator**: State-driven workflow coordinating request understanding, tool planning, data retrieval, and business decision execution.
3. **Ollama Reasoning (`llama3.2`)**: Local LLM providing business reasoning, decision recommendation, and grounded natural language explanations.
4. **Model Context Protocol (MCP)**: Local stdio-based MCP client and server (`mcp_server/server.py`) exposing `search_customer`, `search_complaint`, and `create_ticket`.
5. **ChromaDB RAG**: Local persistent vector database with sentence-transformer embeddings querying company refund and support policies.
6. **CrewAI Support**: Multi-agent collaborative reasoning preserving full backwards compatibility.

---

## Configuration

Configuration is managed via `.env`:

```env
# AI Provider Selection (Ollama is the local LLM provider)
AI_PROVIDER=ollama

# Ollama Model Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_HOST=http://127.0.0.1:11434

# Application Settings
APP_NAME=DCI AI Business Assistant
APP_VERSION=1.0.0
PYTHONPATH=.
CREWAI_TELEMETRY_OPT_OUT=true
```

---

## Starting the Application

### 1. Ensure Ollama is running
```bash
ollama list
```
Ensure `llama3.2` is present. If needed, pull it:
```bash
ollama pull llama3.2
```

### 2. Start the FastAPI Backend
Using PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Or run the helper script:
```powershell
.\run_backend.ps1
```

---

## API Endpoints

### 1. Health Check
`GET /health`
```json
{
  "status": "healthy",
  "ollama": "available"
}
```

### 2. Business Assistant Gateway
`POST /api/assistant`

**Request:**
```json
{
  "message": "Ravi Kumar has a damaged product. Create a support ticket if required."
}
```

**Response:**
```json
{
  "message": "Ravi Kumar has a damaged product. Create a support ticket if required.",
  "response": "Ravi Kumar's complaint was reviewed against the available policy. A support ticket has been created.\n\nTicket ID: T001\nIssue: Damaged product\nStatus: Created",
  "decision": "CREATE_TICKET",
  "ticket": "{\n  \"ticket_id\": \"T001\",\n  \"status\": \"Open\"\n}"
}
```

### 3. Interactive Documentation
Swagger UI is accessible at:
```
http://127.0.0.1:8000/docs
```

---

## Running Test Suites

### 1. FastAPI + Ollama Agentic Workflow Tests
```powershell
.\.venv\Scripts\python.exe tests/test_fastapi_agent.py
```
Covers:
- `GET /health` operational verification
- Customer search via MCP (`search_customer`)
- Policy retrieval via RAG
- Combined customer + complaint + policy analysis
- Support ticket creation via MCP (`create_ticket`)
- Missing customer guard (`MORE_INFORMATION_REQUIRED`)
- General AI reasoning query
- Unknown customer handling
- Request validation (empty, missing, oversized, invalid JSON)

### 2. Regression Test Suites
```powershell
.\.venv\Scripts\python.exe tests/test_tools.py
.\.venv\Scripts\python.exe tests/test_rag.py
.\.venv\Scripts\python.exe tests/test_langchain.py
.\.venv\Scripts\python.exe tests/test_agent.py
.\.venv\Scripts\python.exe tests/test_mcp_client.py
.\.venv\Scripts\python.exe tests/test_agentic_workflow.py
```
