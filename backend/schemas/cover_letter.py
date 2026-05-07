from .base import DocumentSchema, SchemaField

COVER_LETTER_SCHEMA = DocumentSchema(
    type="cover_letter",
    label="Cover Letter / Transmittal",
    fields=[
        SchemaField("loan_number", "Loan Number", "text", required=False),
        SchemaField("site_id", "Site ID", "text", required=False),
        SchemaField("site_name", "Site / Property Name", "text", required=False),
        SchemaField("period", "Reporting Period", "text", required=False),
        SchemaField("borrower_name", "Borrower Entity", "text", required=False),
        SchemaField("sender_name", "Sender Name", "text", required=False),
        SchemaField("sender_company", "Sender Company", "text", required=False),
        SchemaField("recipient_name", "BWE Recipient", "text", required=False),
        SchemaField("document_list", "Attached Documents Listed", "text", required=False),
    ],
)
