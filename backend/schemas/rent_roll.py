from .base import DocumentSchema, SchemaField

RENT_ROLL_SCHEMA = DocumentSchema(
    type="rent_roll",
    label="Rent Roll",
    fields=[
        SchemaField("property_name", "Property Name", "text", True),
        SchemaField("property_address", "Property Address", "text", True),
        SchemaField("report_date", "Report Date / As-Of Date", "date", True),
        SchemaField("total_units", "Total Units", "number", True),
        SchemaField("occupied_units", "Occupied Units", "number", True),
        SchemaField("vacant_units", "Vacant Units", "number", False),
        SchemaField("occupancy_rate", "Occupancy Rate (%)", "percentage", True),
        SchemaField("gross_potential_rent", "Gross Potential Rent", "currency", True),
        SchemaField("total_actual_rent", "Total Actual Rent Collected", "currency", True),
        SchemaField("vacancy_loss", "Vacancy Loss", "currency", False),
        SchemaField("total_concessions", "Total Concessions", "currency", False),
        SchemaField("average_rent_per_unit", "Average Rent Per Unit", "currency", False),
        SchemaField("unit_mix_summary", "Unit Mix Summary", "text", False, "e.g. '50 1BR, 30 2BR, 20 3BR'"),
    ],
)
