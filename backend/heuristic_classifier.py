from __future__ import annotations

import re

# Minimum confidence to accept a heuristic result without falling back to LLM.
HEURISTIC_CONFIDENCE_THRESHOLD = 0.75

# ---------------------------------------------------------------------------
# Keyword sets — each entry is (pattern, weight). Weights sum to a raw score
# which is normalised to [0, 1] by dividing by the max possible.
# ---------------------------------------------------------------------------

_RULES: dict[str, list[tuple[str, float]]] = {
    "cover_letter": [
        (r"\bRE\s*:\s*LOAN\b", 3.0),
        (r"\bLOAN\s*#\s*\d+", 2.5),
        (r"\bpursuant to the requirements\b", 2.0),
        (r"\bcertified (operating statement|rent roll|balance sheet)\b", 2.0),
        (r"\bquarterly reports?\b", 1.5),
        (r"\bannual reports?\b", 1.0),
        (r"\bdear (sir|madam|lender)\b", 1.5),
        (r"\bsincerely\b", 1.0),
        (r"\bplease find attached\b", 1.5),
        (r"\bguarantor\b", 0.5),
        # Certification pages always accompany cover letters
        (r"\bcertification of attached\b", 3.0),
        (r"\bborrower hereby certifies\b", 3.0),
        (r"\battached reports are true\b", 2.0),
    ],
    "rent_roll": [
        (r"\brent\s*roll\b", 3.0),
        (r"\bsummary rent roll\b", 3.0),
        (r"\bsuite\s*(id|no|#)?\b", 2.0),
        (r"\boccupant\s*name\b", 2.0),
        (r"\blease\s+(commencement|expiration|start|end)\b", 2.0),
        (r"\bbase\s+rent\b", 2.0),
        (r"\b(occupied|vacant|vacancy)\b", 1.5),
        (r"\bcam\b", 1.5),
        (r"\bpsf\b", 1.5),
        (r"\bsq\s*ft\b", 1.0),
        (r"\bmonth.to.month\b", 1.0),
        (r"\bnet\s+(net|lease)\b", 0.5),
    ],
    "operating_statement": [
        (r"\b(operating statement|operating statements)\b", 3.0),
        (r"\bnet operating income\b", 3.0),
        (r"\bnoi\b", 2.0),
        (r"\btotal revenues?\b", 2.5),
        (r"\btotal expenses?\b", 2.5),
        (r"\bminimum rent\b", 2.0),
        (r"\bcommon area maintenance\b", 2.0),
        (r"\bmanagement fees?\b", 1.5),
        (r"\b(qtd|ytd)\b", 2.0),
        (r"\bvariance\b", 1.5),
        (r"\breal estate tax(es)?\b", 1.0),
        (r"\bdepreciation\b", 1.0),
        (r"\bnet income\b", 1.0),
        # Sub-reports that are part of an operating statement package
        (r"\bcam breakdown\b", 3.0),
        (r"\blandlord\s+expenses?\b", 2.5),
        (r"\bnon\s*recoverable\b", 1.5),
        (r"\bsop\s+reported\b", 2.5),
        (r"\brevenues from rental properties\b", 2.5),
        (r"\bconsolidated statements? of income\b", 2.5),
        (r"\boperating expenses?\b", 1.0),
    ],
    "balance_sheet": [
        (r"\bbalance sheet\b", 3.0),
        (r"\bconsolidated balance sheets?\b", 3.0),
        (r"\btotal assets\b", 3.0),
        (r"\btotal liabilities\b", 2.5),
        (r"\b(members?|stockholders?|partners?)\s+equity\b", 2.5),
        (r"\baccumulated depreciation\b", 2.0),
        (r"\bbuilding and improvements\b", 2.0),
        (r"\bcash and cash equivalents\b", 2.0),
        (r"\baccounts (receivable|payable)\b", 1.5),
        (r"\breal estate,?\s+net\b", 1.5),
        (r"\bintangible assets\b", 1.0),
        (r"\bretained earnings\b", 1.0),
    ],
    "tax_document": [
        (r"\bschedule\s+e\b", 3.0),
        (r"\bform\s+8825\b", 3.0),
        (r"\bform\s+1065\b", 3.0),
        (r"\bform\s+1040\b", 2.5),
        (r"\binternal revenue service\b", 2.5),
        (r"\b(irs|omb)\b", 1.5),
        (r"\btax\s+year\b", 2.0),
        (r"\bgross\s+rents\b", 1.5),
        (r"\bdepreciation\s+expense\b", 1.5),
        (r"\bpartnership\s+return\b", 1.5),
        (r"\bpassive\s+(income|loss|activity)\b", 1.0),
        (r"\btaxable\s+income\b", 1.0),
    ],
}

# Raw score needed to reach 1.0 confidence. Using a fixed target means adding
# more supporting patterns doesn't dilute scores for documents that already
# match the core signals. A document hitting 8.0+ raw is unambiguously identified.
_TARGET_SCORE = 8.0


def _score(text: str, doc_type: str) -> float:
    """Return normalised score [0, 1] for doc_type against text."""
    raw = sum(
        weight for pattern, weight in _RULES[doc_type]
        if re.search(pattern, text, re.IGNORECASE)
    )
    return min(raw / _TARGET_SCORE, 1.0)


def classify_heuristic(text: str) -> dict:
    """
    Score text against all known document types.
    Returns the best match if it clears the confidence threshold, else unknown.

    Return shape matches classifier.classify_document() so callers are uniform.
    """
    scores = {doc_type: _score(text, doc_type) for doc_type in _RULES}
    best_type = max(scores, key=lambda t: scores[t])
    best_score = scores[best_type]

    if best_score >= HEURISTIC_CONFIDENCE_THRESHOLD:
        return {
            "document_type": best_type,
            "confidence": round(best_score, 3),
            "method": "heuristic",
            "all_scores": {t: round(s, 3) for t, s in scores.items()},
        }

    return {
        "document_type": "unknown",
        "confidence": best_score,
        "method": "heuristic",
        "all_scores": {t: round(s, 3) for t, s in scores.items()},
    }
