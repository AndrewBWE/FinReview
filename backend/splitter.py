from __future__ import annotations

from classifier import classify_document
from heuristic_classifier import classify_heuristic, HEURISTIC_CONFIDENCE_THRESHOLD

# Pages with fewer characters than this are likely blank/signature pages —
# inherit the previous segment's type rather than classifying independently.
_MIN_PAGE_CHARS = 80


def split_pages(ocr_pages: list[dict]) -> list[dict]:
    """
    Classify each page and group consecutive same-type pages into segments.

    Returns a list of segments, each:
    {
        "page_indices": [0, 1, ...],   # 0-based indices into ocr_pages
        "page_numbers": [1, 2, ...],   # 1-based for display
        "document_type": str,
        "classification_confidence": float,
        "text": str,                   # concatenated text for extraction
        "pages": [...]                 # the raw ocr page dicts
    }
    """
    if not ocr_pages:
        return []

    page_classifications = _classify_pages(ocr_pages)
    return _group_segments(ocr_pages, page_classifications)


def _classify_pages(ocr_pages: list[dict]) -> list[dict]:
    last_valid_type = "unknown"
    results = []

    for page in ocr_pages:
        text = page.get("text", "")
        if len(text.strip()) < _MIN_PAGE_CHARS:
            # Too little content — inherit previous type, no classification needed
            results.append({
                "document_type": last_valid_type,
                "confidence": 0.0,
                "inherited": True,
                "method": "inherited",
            })
            continue

        # Try heuristics first — free and fast
        heuristic = classify_heuristic(text)
        if heuristic["document_type"] != "unknown":
            last_valid_type = heuristic["document_type"]
            results.append({
                "document_type": heuristic["document_type"],
                "confidence": heuristic["confidence"],
                "inherited": False,
                "method": "heuristic",
            })
        else:
            # Heuristic not confident — fall back to LLM
            cls = classify_document(text)
            last_valid_type = cls["document_type"]
            results.append({
                "document_type": cls["document_type"],
                "confidence": cls["confidence"],
                "inherited": False,
                "method": "llm",
            })

    return results


def _group_segments(ocr_pages: list[dict], classifications: list[dict]) -> list[dict]:
    segments: list[dict] = []
    current_type = classifications[0]["document_type"]
    current_conf = classifications[0]["confidence"]
    current_indices = [0]

    for i, cls in enumerate(classifications[1:], start=1):
        if cls["document_type"] == current_type:
            current_indices.append(i)
            if not cls["inherited"]:
                current_conf = cls["confidence"]
        else:
            segments.append(_make_segment(ocr_pages, current_indices, current_type, current_conf))
            current_type = cls["document_type"]
            current_conf = cls["confidence"]
            current_indices = [i]

    segments.append(_make_segment(ocr_pages, current_indices, current_type, current_conf))
    return segments


def _make_segment(
    ocr_pages: list[dict],
    indices: list[int],
    doc_type: str,
    confidence: float,
) -> dict:
    pages = [ocr_pages[i] for i in indices]
    return {
        "page_indices": indices,
        "page_numbers": [i + 1 for i in indices],
        "document_type": doc_type,
        "classification_confidence": confidence,
        "text": "\n\n".join(p.get("text", "") for p in pages),
        "pages": pages,
    }
