from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

DOCUMENTS_PATH = Path("documents")
VECTOR_DB_PATH = "rag/chroma_db"

_vector_db: Optional[Chroma] = None
_embeddings: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Singleton getter for HuggingFace embeddings model."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings


def load_documents():
    documents = []
    for file_path in DOCUMENTS_PATH.glob("*.txt"):
        loader = TextLoader(str(file_path), encoding="utf-8")
        documents.extend(loader.load())
    return documents


def create_vector_database():
    global _vector_db
    documents = load_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)
    embeddings = get_embeddings()

    _vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH,
    )
    return _vector_db


def get_vector_database() -> Chroma:
    """
    Get or load the persistent Chroma vector database.
    Reuses existing stored database on disk, avoiding expensive re-indexing on every query.
    """
    global _vector_db
    if _vector_db is not None:
        return _vector_db

    db_path = Path(VECTOR_DB_PATH)
    embeddings = get_embeddings()

    # If Chroma store already exists on disk, load it directly
    if db_path.exists() and any(db_path.iterdir()):
        try:
            _vector_db = Chroma(
                persist_directory=str(db_path),
                embedding_function=embeddings,
            )
            return _vector_db
        except Exception:
            pass

    return create_vector_database()


def search_documents(query: str, k: int = 3):
    """Search for relevant policy documents in the persistent vector store."""
    vector_db = get_vector_database()
    results = vector_db.similarity_search(query, k=k)
    return results