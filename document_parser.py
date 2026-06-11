"""
Text extraction from PDF, DOCX, and EML files.
Falls back to raw text if optional libraries are missing.
"""

import os
import re
from pathlib import Path


def extract_text(filepath: str) -> str:
    """Return plain text from a document file."""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return _from_pdf(filepath)
    elif ext in (".docx", ".doc"):
        return _from_docx(filepath)
    elif ext in (".eml", ".msg"):
        return _from_eml(filepath)
    elif ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    else:
        # Try reading as plain text
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


def _from_pdf(filepath: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages)
    except ImportError:
        pass

    try:
        import pypdf
        reader = pypdf.PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        pass

    return f"[PDF extraction unavailable — install pdfplumber or pypdf: {os.path.basename(filepath)}]"


def _from_docx(filepath: str) -> str:
    try:
        import docx
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        return f"[DOCX extraction unavailable — install python-docx: {os.path.basename(filepath)}]"


def _from_eml(filepath: str) -> str:
    import email
    from email import policy

    with open(filepath, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    parts = []
    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    date = msg.get("Date", "")
    parts.append(f"От: {sender}\nТема: {subject}\nДата: {date}\n")

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                try:
                    parts.append(part.get_content())
                except Exception:
                    pass
    else:
        try:
            parts.append(msg.get_content())
        except Exception:
            pass

    return "\n".join(parts)


def truncate_for_llm(text: str, max_chars: int = 12000) -> str:
    """Keep first and last chunks so the LLM sees header and footer."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n[...фрагмент опущен...]\n\n" + text[-half:]
