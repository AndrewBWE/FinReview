from .base import DocumentSchema
from .rent_roll import RENT_ROLL_SCHEMA
from .operating_statement import OPERATING_STATEMENT_SCHEMA
from .tax_document import TAX_DOCUMENT_SCHEMA
from .cover_letter import COVER_LETTER_SCHEMA
from .balance_sheet import BALANCE_SHEET_SCHEMA

SCHEMAS: dict[str, DocumentSchema] = {
    "rent_roll": RENT_ROLL_SCHEMA,
    "operating_statement": OPERATING_STATEMENT_SCHEMA,
    "tax_document": TAX_DOCUMENT_SCHEMA,
    "cover_letter": COVER_LETTER_SCHEMA,
    "balance_sheet": BALANCE_SHEET_SCHEMA,
}

__all__ = ["SCHEMAS", "DocumentSchema"]
