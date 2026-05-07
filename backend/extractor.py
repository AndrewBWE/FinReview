import json
import os
import time

from openai import AzureOpenAI

from schemas.base import DocumentSchema

SYSTEM_PROMPT_TEMPLATE = """You are a financial document data extractor for real estate documents.
Extract all available fields from the document text according to the schema below.

{schema_description}

Rules:
- Return null for any field not found in the document
- Currency values: return as a plain number (no $ or commas), e.g. 125000.00
- Percentages: return as a number 0–100, e.g. 94.5
- Dates: return as YYYY-MM-DD if determinable, otherwise the original string
- For each field, include:
    "source": where on the page you found the value (e.g. "Page 1 header", "Page 2 summary table row 3")
    "confidence": "high" (clearly stated), "medium" (inferred/calculated), or "low" (uncertain)
    "alternatives": list of other candidate values if ambiguous, else empty list

Respond with JSON only:
{{
  "fields": {{
    "<field_id>": {{
      "value": <extracted value or null>,
      "confidence": "high|medium|low",
      "source": "<location description>",
      "alternatives": []
    }}
  }}
}}"""


def extract_fields(full_text: str, schema: DocumentSchema) -> dict:
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        schema_description=schema.to_prompt_description()
    )
    user_prompt = f"Extract fields from this document:\n\n{full_text[:12000]}"

    start = time.time()
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    duration_ms = int((time.time() - start) * 1000)

    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)
    raw_fields = parsed.get("fields", {})

    extracted = []
    for sf in schema.fields:
        data = raw_fields.get(sf.id, {})
        extracted.append({
            "id": sf.id,
            "label": sf.label,
            "field_type": sf.field_type,
            "required": sf.required,
            "value": data.get("value"),
            "confidence": data.get("confidence"),
            "source": data.get("source"),
            "alternatives": data.get("alternatives", []),
        })

    return {
        "fields": extracted,
        "prompts": {
            "system": system_prompt,
            "user": user_prompt,
            "response": raw,
        },
        "duration_ms": duration_ms,
        "tokens_used": response.usage.total_tokens if response.usage else 0,
    }
