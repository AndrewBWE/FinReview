import json
import os
import time

from openai import AzureOpenAI

SYSTEM_PROMPT = """You are a financial document classifier specializing in real estate documents.
Classify the document into exactly one of these types:
- cover_letter: A transmittal or cover letter accompanying financial documents — lists attached reports, references a loan number or property, signed by borrower or their representative. Includes certification pages.
- rent_roll: Shows tenant-level data — unit numbers, tenant names, lease dates, rents, occupancy status
- operating_statement: Income/expense statement, P&L, NOI analysis, CAM breakdown, or landlord expense report for a property
- balance_sheet: Shows assets, liabilities, and equity for an entity at a point in time
- tax_document: A tax form with rental income — Schedule E, Form 8825, 1065, 1040, or similar
- unknown: Cannot determine type, or does not fit the above categories

Respond with JSON only:
{
  "document_type": "<type>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence explanation>"
}"""


def classify_document(text_sample: str) -> dict:
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )

    user_prompt = f"Classify this financial document:\n\n{text_sample[:3000]}"

    start = time.time()
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    duration_ms = int((time.time() - start) * 1000)

    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)

    return {
        "document_type": parsed.get("document_type", "unknown"),
        "confidence": parsed.get("confidence", 0.0),
        "reasoning": parsed.get("reasoning", ""),
        "prompts": {
            "system": SYSTEM_PROMPT,
            "user": user_prompt,
            "response": raw,
        },
        "duration_ms": duration_ms,
        "tokens_used": response.usage.total_tokens if response.usage else 0,
    }
