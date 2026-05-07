from __future__ import annotations

import re
from datetime import datetime

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
_MONTH_NAMES = {v: k.capitalize() for k, v in _MONTHS.items()}


def extract_period(text: str) -> str:
    """
    Extract the reporting period from document text.
    Returns strings like "January 2026", "Q4 2025".
    Falls back to the current month/year if nothing is found.
    """
    # "quarter ended December 31, 2025" / "quarter ended December 2025"
    m = re.search(
        r"quarter\s+ended\s+(" + "|".join(_MONTHS) + r")\w*\s+(?:\d{1,2},?\s+)?(\d{4})",
        text, re.IGNORECASE,
    )
    if m:
        month_num = _MONTHS[m.group(1).lower()]
        quarter = (month_num - 1) // 3 + 1
        return f"Q{quarter} {m.group(2)}"

    # "year ended December 31, 2025"
    m = re.search(
        r"year\s+ended\s+(" + "|".join(_MONTHS) + r")\w*\s+(?:\d{1,2},?\s+)?(\d{4})",
        text, re.IGNORECASE,
    )
    if m:
        return f"{m.group(1).capitalize()} {m.group(2)}"

    # "Q4 2025" / "Q4 '25"
    m = re.search(r"\bQ([1-4])\s*['\"]?(\d{2,4})\b", text, re.IGNORECASE)
    if m:
        year = m.group(2)
        if len(year) == 2:
            year = f"20{year}"
        return f"Q{m.group(1)} {year}"

    # "December 31, 2025" / "December 2025"
    m = re.search(
        r"\b(" + "|".join(_MONTHS) + r")\w*\s+(?:\d{1,2},?\s+)?(\d{4})\b",
        text, re.IGNORECASE,
    )
    if m:
        return f"{m.group(1).capitalize()} {m.group(2)}"

    # "12/31/2025" or "12/2025"
    m = re.search(r"\b(\d{1,2})/(?:\d{1,2}/)?(\d{4})\b", text)
    if m:
        month_num = int(m.group(1))
        if 1 <= month_num <= 12:
            return f"{_MONTH_NAMES[month_num]} {m.group(2)}"

    now = datetime.now()
    return f"{_MONTH_NAMES[now.month]} {now.year}"
