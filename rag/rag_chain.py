import ollama

from backend.config import OLLAMA_MODEL
from rag.rag_service import search_documents


async def answer_with_rag(question: str) -> str:

    documents = search_documents(question)

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    prompt = f"""
You are DCI AI Business Assistant.

Answer the user's question using ONLY the provided context.

If the answer is not available in the context,
say that the information is not available.

Context:
{context}

User Question:
{question}

Answer:
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]