"""
Document Parser Tools

Handles extraction of resume text from PDF, DOCX, and plain text formats.
"""

import os

import io

def parse_pdf(file_bytes: bytes) -> dict:
    """
    Extract text content from a PDF resume.

    Args:
        file_bytes: Bytes containing the PDF data

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    try:
        import pdfplumber
    except ImportError:
        return {
            "success": False,
            "text": "",
            "error": "pdfplumber not installed. Run: pip install pdfplumber",
        }

    if not file_bytes:
        return {"success": False, "text": "", "error": "PDF bytes are empty"}

    try:
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            return {
                "success": False,
                "text": "",
                "error": "PDF appears to be empty or image-only. Try converting to DOCX first.",
            }

        return {"success": True, "text": full_text, "error": None}

    except Exception as e:
        return {"success": False, "text": "", "error": f"PDF parsing failed: {str(e)}"}


def parse_docx(file_bytes: bytes) -> dict:
    """
    Extract text content from a DOCX resume.

    Args:
        file_bytes: Bytes containing the DOCX data

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    try:
        from docx import Document
    except ImportError:
        return {
            "success": False,
            "text": "",
            "error": "python-docx not installed. Run: pip install python-docx",
        }

    if not file_bytes:
        return {"success": False, "text": "", "error": "DOCX bytes are empty"}

    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        full_text = "\n".join(paragraphs).strip()

        if not full_text:
            return {"success": False, "text": "", "error": "DOCX appears to be empty."}

        return {"success": True, "text": full_text, "error": None}

    except Exception as e:
        return {"success": False, "text": "", "error": f"DOCX parsing failed: {str(e)}"}


def parse_plain_text(text: str) -> dict:
    """
    Process plain text resume content (passthrough with cleanup).

    Args:
        text: Raw resume text pasted by the user.

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    if not text or not text.strip():
        return {"success": False, "text": "", "error": "Provided text is empty."}

    cleaned = text.strip()
    return {"success": True, "text": cleaned, "error": None}
