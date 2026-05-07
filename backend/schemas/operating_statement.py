from .base import DocumentSchema, SchemaField

OPERATING_STATEMENT_SCHEMA = DocumentSchema(
    type="operating_statement",
    label="Operating Statement",
    fields=[
        SchemaField("property_name", "Property Name", "text", True),
        SchemaField("property_address", "Property Address", "text", True),
        SchemaField("period_start", "Period Start Date", "date", True),
        SchemaField("period_end", "Period End Date", "date", True),
        SchemaField("period_type", "Period Type", "text", False, "e.g. Annual, YTD, Monthly"),
        SchemaField("gross_potential_rent", "Gross Potential Rent", "currency", True),
        SchemaField("vacancy_credit_loss", "Vacancy & Credit Loss", "currency", False),
        SchemaField("other_income", "Other Income", "currency", False),
        SchemaField("effective_gross_income", "Effective Gross Income (EGI)", "currency", True),
        SchemaField("total_operating_expenses", "Total Operating Expenses", "currency", True),
        SchemaField("net_operating_income", "Net Operating Income (NOI)", "currency", True),
        SchemaField("management_fees", "Management Fees", "currency", False),
        SchemaField("insurance", "Insurance", "currency", False),
        SchemaField("real_estate_taxes", "Real Estate Taxes", "currency", False),
        SchemaField("maintenance_repairs", "Maintenance & Repairs", "currency", False),
        SchemaField("utilities", "Utilities", "currency", False),
        SchemaField("debt_service", "Debt Service", "currency", False),
        SchemaField("net_cash_flow", "Net Cash Flow (after debt service)", "currency", False),
    ],
)
