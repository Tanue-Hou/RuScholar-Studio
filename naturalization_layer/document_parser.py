import io
import os

import docx
from pypdf import PdfReader


def _pdf_text(reader: PdfReader) -> str:
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text


def parse_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])


def parse_pdf(file_path: str) -> str:
    return _pdf_text(PdfReader(file_path))


def parse_docx_bytes(data: bytes) -> str:
    return parse_docx(io.BytesIO(data))


def parse_pdf_bytes(data: bytes) -> str:
    return _pdf_text(PdfReader(io.BytesIO(data)))


def parse_document_bytes(filename: str, data: bytes) -> str:
    """Extract text from an uploaded .pdf/.docx; anything else is decoded as UTF-8."""
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".pdf":
        return parse_pdf_bytes(data)
    if ext == ".docx":
        return parse_docx_bytes(data)
    return data.decode("utf-8")


def parse_document(file_path: str) -> str:
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".docx":
        return parse_docx(file_path)
    elif ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in [".txt", ".md"]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")
