from __future__ import annotations

import uuid
from typing import Any

from ocr import run_ocr
from excel_reader import run_excel
from extractor import extract_fields
from splitter import split_pages
from schemas import SCHEMAS

EXCEL_EXTENSIONS = {"xlsx", "xls"}

pipeline_results: dict[str, dict[str, Any]] = {}


def create_pipeline(filename: str) -> str:
    pipeline_id = str(uuid.uuid4())
    pipeline_results[pipeline_id] = {
        "id": pipeline_id,
        "filename": filename,
        "status": "processing",
        "document_type": None,
        "classification_confidence": None,
        "page_count": 0,
        "ocr_pages": [],
        "schema": None,
        "extracted_fields": [],
        "documents": [],
        "prompts": None,
        "trace": [],
        "error": None,
        "_file_bytes": None,  # stored for sorter, not returned in API responses
    }
    return pipeline_id


def get_result(pipeline_id: str) -> dict | None:
    return pipeline_results.get(pipeline_id)


def run_pipeline(pipeline_id: str, file_bytes: bytes) -> None:
    record = pipeline_results[pipeline_id]
    filename = record["filename"]

    try:
        record["_file_bytes"] = file_bytes

        # Step 1: OCR / file read
        ext = filename.rsplit(".", 1)[-1].lower()
        is_excel = ext in EXCEL_EXTENSIONS
        ocr_label = "Excel Sheet Reader" if is_excel else "Document Intelligence OCR"
        ocr_input = {"filename": filename} if is_excel else {"model": "prebuilt-layout", "filename": filename}

        _trace(pipeline_id, "ocr", ocr_label, "running", {}, {})
        ocr = run_excel(file_bytes, filename) if is_excel else run_ocr(file_bytes, filename)
        _trace(
            pipeline_id, "ocr", ocr_label, "success",
            ocr_input,
            {"page_count": ocr["page_count"], "tables_found": sum(len(p["tables"]) for p in ocr["pages"])},
            ocr["duration_ms"],
        )
        record["ocr_pages"] = ocr["pages"]
        record["page_count"] = ocr["page_count"]

        # Step 2: Split + classify (page-level for PDFs, single doc for Excel)
        _trace(pipeline_id, "split", "Page-Level Split & Classify", "running", {}, {})
        if is_excel:
            # Excel files are always a single document
            from classifier import classify_document
            cls = classify_document(ocr["full_text"])
            segments = [{
                "page_indices": list(range(ocr["page_count"])),
                "page_numbers": list(range(1, ocr["page_count"] + 1)),
                "document_type": cls["document_type"],
                "classification_confidence": cls["confidence"],
                "text": ocr["full_text"],
                "pages": ocr["pages"],
            }]
        else:
            segments = split_pages(ocr["pages"])

        _trace(
            pipeline_id, "split", "Page-Level Split & Classify", "success",
            {"page_count": ocr["page_count"]},
            {"segments_found": len(segments), "types": [s["document_type"] for s in segments]},
        )

        # Step 3: Extract fields for each segment
        _trace(pipeline_id, "extract", "Field Extraction", "running", {}, {})
        documents = []
        for i, segment in enumerate(segments):
            doc_type = segment["document_type"]
            schema = SCHEMAS.get(doc_type)
            doc_entry: dict[str, Any] = {
                "segment_index": i,
                "page_indices": segment["page_indices"],
                "page_numbers": segment["page_numbers"],
                "document_type": doc_type,
                "classification_confidence": segment["classification_confidence"],
                "schema": schema.to_dict() if schema else None,
                "extracted_fields": [],
            }

            if schema:
                ext_result = extract_fields(segment["text"], schema)
                doc_entry["extracted_fields"] = ext_result["fields"]

            documents.append(doc_entry)

        _trace(
            pipeline_id, "extract", "Field Extraction", "success",
            {},
            {"documents_extracted": sum(1 for d in documents if d["extracted_fields"])},
        )

        record["documents"] = documents

        # Top-level document_type: single type if all segments agree, else "mixed"
        types = list({d["document_type"] for d in documents})
        if len(types) == 1:
            record["document_type"] = types[0]
            record["classification_confidence"] = documents[0]["classification_confidence"]
            record["schema"] = documents[0]["schema"]
            record["extracted_fields"] = documents[0]["extracted_fields"]
        else:
            record["document_type"] = "mixed"
            record["classification_confidence"] = None
            record["schema"] = None
            record["extracted_fields"] = []

        record["status"] = "complete"

    except Exception as exc:
        record["status"] = "error"
        record["error"] = str(exc)
        for entry in record["trace"]:
            if entry["status"] == "running":
                entry["status"] = "error"
                entry["output"] = {"error": str(exc)}


def _trace(
    pipeline_id: str,
    step: str,
    label: str,
    status: str,
    input_data: dict,
    output_data: dict,
    duration_ms: int = 0,
) -> None:
    trace = pipeline_results[pipeline_id]["trace"]
    for entry in trace:
        if entry["step"] == step:
            entry["status"] = status
            entry["output"] = output_data
            entry["duration_ms"] = duration_ms
            return
    trace.append({
        "step": step,
        "label": label,
        "status": status,
        "input": input_data,
        "output": output_data,
        "duration_ms": duration_ms,
    })
