from .base import DocumentSchema, SchemaField

BALANCE_SHEET_SCHEMA = DocumentSchema(
    type="balance_sheet",
    label="Balance Sheet",
    fields=[
        SchemaField("entity_name", "Entity / Borrower Name", "text", required=False),
        SchemaField("as_of_date", "As-Of Date", "date", required=False),
        SchemaField("total_assets", "Total Assets", "currency", required=False),
        SchemaField("total_liabilities", "Total Liabilities", "currency", required=False),
        SchemaField("total_equity", "Total Equity / Net Worth", "currency", required=False),
        SchemaField("cash_and_equivalents", "Cash and Cash Equivalents", "currency", required=False),
        SchemaField("real_estate_net", "Real Estate, Net", "currency", required=False),
        SchemaField("total_debt", "Total Debt / Mortgage Payable", "currency", required=False),
    ],
)
