from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FieldType = Literal["text", "number", "date", "currency", "percentage"]


@dataclass
class SchemaField:
    id: str
    label: str
    field_type: FieldType
    required: bool
    description: str = ""


@dataclass
class DocumentSchema:
    type: str
    label: str
    fields: list[SchemaField]

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "label": self.label,
            "fields": [
                {
                    "id": f.id,
                    "label": f.label,
                    "field_type": f.field_type,
                    "required": f.required,
                    "description": f.description,
                }
                for f in self.fields
            ],
        }

    def to_prompt_description(self) -> str:
        lines = [f"Document Type: {self.label}", "", "Fields to extract:"]
        for f in self.fields:
            req = "required" if f.required else "optional"
            desc = f" — {f.description}" if f.description else ""
            lines.append(f"  - {f.id} ({f.field_type}, {req}): {f.label}{desc}")
        return "\n".join(lines)
