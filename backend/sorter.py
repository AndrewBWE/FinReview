from __future__ import annotations

import io
import re
from datetime import datetime

from pypdf import PdfReader, PdfWriter

from period_extractor import extract_period
from schemas import SCHEMAS
from sf_client import get_loan_by_number, match_loan_from_text
from storage import find_lender_folder, find_deal_folder, write_to_deal_folder


def sort_pipeline(
    pipeline_result: dict,
    file_bytes: bytes,
    loan_number: str | None = None,
    am_email: str | None = None,
) -> dict:
    """
    Route a processed pipeline's documents to the correct blob deal folder.

    Loan identification priority:
      1. loan_number passed directly (from email subject)
      2. Extracted from document content via LLM using am_email

    Returns a status dict. If no deal folder is found, status is "no_folder"
    and the caller should notify the AM.
    """
    # Step 1 — identify the loan
    loan = _resolve_loan(pipeline_result, loan_number, am_email)
    if not loan:
        return {"status": "error", "reason": "Could not identify loan from document content or subject"}

    resolved_loan_number = loan["bwe_loan_number"]
    loan_name = loan["name"]
    investor_name = loan.get("investor_name", "")

    # Step 2 — find the lender folder
    lender_folder = find_lender_folder(investor_name)
    if not lender_folder:
        return {
            "status": "error",
            "reason": f"No lender folder found for investor: {investor_name}",
            "loan_number": resolved_loan_number,
        }

    # Step 3 — find the deal folder
    deal_path = find_deal_folder(lender_folder, resolved_loan_number, loan_name)
    if not deal_path:
        return {
            "status": "no_folder",
            "reason": f"No deal folder found for {resolved_loan_number} - {loan_name} under {lender_folder}",
            "loan_number": resolved_loan_number,
            "lender_folder": lender_folder,
        }

    # Step 4 — write each document segment
    filename = pipeline_result.get("filename", "document")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    is_excel = ext in ("xlsx", "xls")
    documents = pipeline_result.get("documents") or []
    written = []

    for doc in documents:
        doc_type = doc.get("document_type", "unknown")

        # Extract period from this segment's page text (look up from ocr_pages by page_number)
        page_nums = set(doc.get("page_numbers", []))
        page_text = " ".join(
            p.get("text", "")
            for p in pipeline_result.get("ocr_pages", [])
            if p.get("page_number") in page_nums
        )
        period = extract_period(page_text) if page_text.strip() else _current_period()

        # Build the output filename
        out_filename = _build_filename(doc_type, period, ext)

        # Get the bytes for this segment
        if is_excel or len(documents) == 1:
            segment_bytes = file_bytes
        else:
            page_indices = doc.get("page_indices") or [pn - 1 for pn in doc.get("page_numbers", [])]
            segment_bytes = _extract_pdf_pages(file_bytes, page_indices)

        result = write_to_deal_folder(deal_path, out_filename, segment_bytes)
        written.append({
            "document_type": doc_type,
            "filename": out_filename,
            "period": period,
            "blob_name": result["blob_name"],
            "url": result["url"],
        })

    return {
        "status": "sorted",
        "loan_number": resolved_loan_number,
        "loan_name": loan_name,
        "investor": investor_name,
        "lender_folder": lender_folder,
        "deal_path": deal_path,
        "documents_written": written,
    }


def _resolve_loan(
    pipeline_result: dict,
    loan_number: str | None,
    am_email: str | None,
) -> dict | None:
    # Direct lookup by loan number
    if loan_number:
        return get_loan_by_number(loan_number)

    # Try to find a loan number in the document text itself
    full_text = " ".join(
        p.get("text", "")
        for page in pipeline_result.get("ocr_pages", [])
        for p in [page]
    )
    extracted_number = _extract_loan_number(full_text)
    if extracted_number:
        loan = get_loan_by_number(extracted_number)
        if loan:
            return loan

    # LLM fallback — match against AM's portfolio
    if am_email and full_text.strip():
        return match_loan_from_text(full_text, am_email)

    return None


def _extract_loan_number(text: str) -> str | None:
    """Look for a BWE-style loan number pattern in document text."""
    m = re.search(r"\b(LOAN\s*#?\s*|BWE\s*#?\s*)(\d{8})\b", text, re.IGNORECASE)
    if m:
        return m.group(2)
    # Plain 8-digit number that could be a loan number
    m = re.search(r"\b(\d{8})\b", text)
    return m.group(1) if m else None


def _build_filename(doc_type: str, period: str, ext: str) -> str:
    schema = SCHEMAS.get(doc_type)
    label = schema.label if schema else doc_type.replace("_", " ").title()
    return f"{label} - {period}.{ext}"


def _extract_pdf_pages(pdf_bytes: bytes, page_indices: list[int]) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for idx in page_indices:
        if 0 <= idx < len(reader.pages):
            writer.add_page(reader.pages[idx])
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _current_period() -> str:
    now = datetime.now()
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    return f"{months[now.month - 1]} {now.year}"
