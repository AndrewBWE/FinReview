from .base import DocumentSchema, SchemaField

TAX_DOCUMENT_SCHEMA = DocumentSchema(
    type="tax_document",
    label="Tax Document",
    fields=[
        SchemaField("taxpayer_name", "Taxpayer Name / Entity", "text", True),
        SchemaField("ein_ssn", "EIN / SSN", "text", False),
        SchemaField("tax_year", "Tax Year", "text", True),
        SchemaField("form_type", "Form Type", "text", True, "e.g. Schedule E, 8825, 1065, 1040"),
        SchemaField("property_address", "Property Address", "text", False),
        SchemaField("total_rents_received", "Total Rents Received", "currency", True),
        SchemaField("total_expenses", "Total Expenses", "currency", True),
        SchemaField("depreciation", "Depreciation", "currency", False),
        SchemaField("net_income_loss", "Net Income / (Loss)", "currency", True),
        SchemaField("advertising", "Advertising", "currency", False),
        SchemaField("insurance", "Insurance", "currency", False),
        SchemaField("management_fees", "Management Fees", "currency", False),
        SchemaField("mortgage_interest", "Mortgage Interest", "currency", False),
        SchemaField("taxes", "Taxes", "currency", False),
        SchemaField("repairs", "Repairs", "currency", False),
        SchemaField("utilities", "Utilities", "currency", False),
    ],
)
