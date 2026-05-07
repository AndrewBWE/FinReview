from __future__ import annotations

import os
import time
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def run_ocr(file_bytes: bytes, filename: str) -> dict[str, Any]:
    endpoint = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT", "")
    key = os.getenv("AZURE_DOC_INTELLIGENCE_KEY", "")

    start = time.time()
    client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        body=file_bytes,
        content_type="application/octet-stream",
    )
    result = poller.result()
    duration_ms = int((time.time() - start) * 1000)

    pages: list[dict[str, Any]] = []
    for page in result.pages or []:
        lines = [line.content for line in (page.lines or [])]
        pages.append({
            "page_number": page.page_number,
            "text": "\n".join(lines),
            "width": page.width,
            "height": page.height,
            "tables": [],
        })

    for table in result.tables or []:
        page_num = (
            table.bounding_regions[0].page_number
            if table.bounding_regions
            else 1
        )
        cells = [
            {
                "row": cell.row_index,
                "col": cell.column_index,
                "content": cell.content,
                "row_span": cell.row_span or 1,
                "col_span": cell.column_span or 1,
            }
            for cell in (table.cells or [])
        ]
        table_data = {
            "row_count": table.row_count,
            "column_count": table.column_count,
            "cells": cells,
        }
        for p in pages:
            if p["page_number"] == page_num:
                p["tables"].append(table_data)
                break

    full_text = "\n\n--- Page Break ---\n\n".join(p["text"] for p in pages)

    return {
        "pages": pages,
        "page_count": len(pages),
        "full_text": full_text,
        "duration_ms": duration_ms,
    }
