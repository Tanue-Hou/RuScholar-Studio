"""
Reference ingestion for a session: BibTeX entries and full-text documents
(PDF/DOCX/TXT) chunked into a BM25 index per citation key.

Shared by the Web upload endpoint and the MCP register/clear/list tools,
which previously each had their own copy of this logic.
"""
import os
import re

from naturalization_layer.document_parser import parse_document_bytes
from naturalization_layer.rag_retriever import BM25Retriever, chunk_text, parse_bibtex
from services.shared_state import session_references


def new_reference_session() -> dict:
    return {
        "bibtex": {},
        "corpus": {},
        "retrievers": {},
        "online_cache": {},
        "bib_mapping": {}
    }


def ensure_reference_session(session_id: str) -> dict:
    """Return the session's reference store, creating it (or missing keys) if needed."""
    session = session_references.get(session_id)
    if session is None:
        session = new_reference_session()
        session_references[session_id] = session
    else:
        for key, value in new_reference_session().items():
            session.setdefault(key, value)
    return session


def reset_reference_session(session_id: str) -> bool:
    """Clear a session's references. Returns False if the session did not exist."""
    existed = session_id in session_references
    if existed:
        session_references[session_id] = new_reference_session()
    return existed


def reference_key_from_filename(filename: str) -> str:
    """'[Smith2020].pdf' -> 'smith2020': the citation key a document is indexed under."""
    name_part, _ = os.path.splitext(os.path.basename(filename))
    return re.sub(r'[\[\]]', '', name_part).strip().lower()


def ingest_bibtex(session_id: str, bibtex_text: str) -> list[str]:
    """Parse BibTeX into the session. Raises on parse errors. Returns the keys added."""
    if not bibtex_text or not bibtex_text.strip():
        return []
    entries = parse_bibtex(bibtex_text)
    ensure_reference_session(session_id)["bibtex"].update(entries)
    return list(entries.keys())


def ingest_reference_text(session_id: str, filename: str, text: str):
    """Chunk + index already-extracted text. Returns the citation key, or None if empty."""
    if not text.strip():
        return None
    key = reference_key_from_filename(filename)
    corpus_entries = [
        {"text": chunk, "metadata": {"filename": filename, "key": key, "chunk_index": idx}}
        for idx, chunk in enumerate(chunk_text(text))
    ]
    session = ensure_reference_session(session_id)
    session["corpus"][key] = corpus_entries
    session["retrievers"][key] = BM25Retriever(corpus_entries)
    return key


def ingest_reference_document(session_id: str, filename: str, data: bytes):
    """Extract, chunk and index one document. Raises on parse/decode errors."""
    return ingest_reference_text(session_id, filename, parse_document_bytes(filename, data))


def list_reference_keys(session_id: str) -> dict:
    session = session_references.get(session_id, {})
    return {
        "bibtex_keys": list(session.get("bibtex", {}).keys()),
        "pdf_keys": list(session.get("retrievers", {}).keys())
    }
