import json
import os
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Canonical subfolder names. Doc types not in this set fall back to "unknown".
KNOWN_FOLDERS = {
    "cover_letter",
    "rent_roll",
    "operating_statement",
    "balance_sheet",
    "tax_document",
    "personal_financial_statement",
    "loan_agreement",
    "appraisal",
    "environmental",
    "title",
    "insurance",
    "unknown",
}


def _blob_client() -> BlobServiceClient:
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "bwefoundrydevbusiness")
    return BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=DefaultAzureCredential(),
    )


def _container_client(container_name: Optional[str] = None):
    name = container_name or os.getenv("AZURE_STORAGE_CONTAINER_NAME", "financial-review")
    return _blob_client().get_container_client(name)


# ---------------------------------------------------------------------------
# Blob folder navigation
# ---------------------------------------------------------------------------

def list_lender_folders(container_name: Optional[str] = None) -> list[str]:
    """Return top-level virtual folder names that begin with a digit."""
    cc = _container_client(container_name)
    folders = []
    for item in cc.walk_blobs(name_starts_with="", delimiter="/"):
        name = item.name.rstrip("/")
        if name and name[0].isdigit():
            folders.append(name)
    return folders


def _lender_name_from_folder(folder: str) -> str:
    """Extract lender name from '014 - Voya' → 'Voya'."""
    m = re.match(r"^\d+\s*-\s*(.+)$", folder)
    return m.group(1).strip() if m else folder


def _match_score(investor_name: str, folder: str) -> float:
    lender = _lender_name_from_folder(folder).lower()
    investor = investor_name.lower()
    # Substring match is the strongest signal (e.g. "voya" in "voya investment management")
    if lender in investor or investor in lender:
        return 0.95
    # Token-level: any word in the folder name appearing in the investor name
    folder_words = [w for w in lender.split() if len(w) > 3]
    if folder_words and any(w in investor for w in folder_words):
        return 0.80
    return SequenceMatcher(None, lender, investor).ratio()


def find_lender_folder(investor_name: str, container_name: Optional[str] = None) -> Optional[str]:
    """Fuzzy match investor_name against numeric lender folders."""
    folders = list_lender_folders(container_name)
    if not folders:
        return None
    best = max(folders, key=lambda f: _match_score(investor_name, f))
    return best if _match_score(investor_name, best) >= 0.4 else None


def find_deal_folder(
    lender_folder: str,
    loan_number: str,
    loan_name: str,
    container_name: Optional[str] = None,
) -> Optional[str]:
    """
    Look for a subfolder matching loan_number or loan_name under lender_folder.
    Returns the full blob prefix (without trailing slash) or None.
    """
    cc = _container_client(container_name)
    prefix = f"{lender_folder}/"
    for item in cc.walk_blobs(name_starts_with=prefix, delimiter="/"):
        folder_segment = item.name.rstrip("/")[len(prefix):]
        if not folder_segment:
            continue
        # Loan number match is definitive
        if loan_number and folder_segment.startswith(loan_number):
            return item.name.rstrip("/")
        # Fuzzy name match as fallback
        if loan_name:
            score = SequenceMatcher(None, loan_name.lower(), folder_segment.lower()).ratio()
            if score >= 0.6:
                return item.name.rstrip("/")
    return None


def write_to_deal_folder(
    deal_path: str,
    filename: str,
    data: bytes,
    container_name: Optional[str] = None,
) -> dict:
    """Write a file into the deal folder path. Overwrites if it already exists."""
    cc = _container_client(container_name)
    blob_name = f"{deal_path}/{filename}"
    bc = cc.get_blob_client(blob_name)
    bc.upload_blob(data, overwrite=True)
    return {"blob_name": blob_name, "url": bc.url}


# ---------------------------------------------------------------------------
# Legacy extraction writer (kept for backward compatibility)
# ---------------------------------------------------------------------------

def write_extraction(pipeline_result: dict, deal_folder: str) -> dict:
    """Write one blob per document segment under deal_folder/{doc_type}/."""
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "financial-review")
    service = _blob_client()
    base_name = os.path.splitext(pipeline_result.get("filename", "document"))[0]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    written = []

    documents = pipeline_result.get("documents") or []
    if not documents:
        documents = [{
            "segment_index": 0,
            "page_numbers": list(range(1, pipeline_result.get("page_count", 1) + 1)),
            "document_type": pipeline_result.get("document_type", "unknown"),
            "classification_confidence": pipeline_result.get("classification_confidence"),
            "extracted_fields": pipeline_result.get("extracted_fields", []),
        }]

    for doc in documents:
        doc_type = doc.get("document_type", "unknown")
        subfolder = doc_type if doc_type in KNOWN_FOLDERS else "unknown"
        suffix = f"_seg{doc['segment_index']}" if len(documents) > 1 else ""
        blob_name = f"{deal_folder}/{subfolder}/{timestamp}_{base_name}{suffix}_extracted.json"

        payload = {
            "extraction_metadata": {
                "pipeline_id": pipeline_result["id"],
                "filename": pipeline_result["filename"],
                "document_type": doc_type,
                "classification_confidence": doc.get("classification_confidence"),
                "page_numbers": doc.get("page_numbers", []),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
                "deal_folder": deal_folder,
            },
            "extracted_fields": doc.get("extracted_fields", []),
        }

        blob_client = service.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(json.dumps(payload, indent=2), overwrite=True)
        written.append({"blob_name": blob_name, "document_type": doc_type, "url": blob_client.url})

    return {"status": "written", "container": container_name, "blobs": written}
