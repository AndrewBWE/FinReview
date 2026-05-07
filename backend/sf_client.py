from __future__ import annotations

import json
import os
import re

import requests
from simple_salesforce import Salesforce


def _get_sf() -> Salesforce:
    login_url = os.environ.get("SF_LOGIN_URL", "https://test.salesforce.com")
    resp = requests.post(
        f"{login_url}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["SF_CONSUMER_KEY"],
            "client_secret": os.environ["SF_CONSUMER_SECRET"],
        },
    )
    resp.raise_for_status()
    auth = resp.json()
    return Salesforce(instance_url=auth["instance_url"], session_id=auth["access_token"])


def _to_folder(name: str) -> str:
    """Normalize a deal name to a safe blob folder segment."""
    return re.sub(r"\s+", "_", name.strip())


def lookup_deals_by_email(email: str) -> list[dict]:
    """Return active Servicing_Loan__c records assigned to the asset manager with this email."""
    sf = _get_sf()

    safe_email = email.replace("'", "\\'")
    user_result = sf.query(f"SELECT Id, Name FROM User WHERE Email = '{safe_email}' LIMIT 1")
    users = user_result.get("records", [])
    if not users:
        return []

    # Asset_Manager__c is a plain text field storing the manager's name, not a User ID
    user_name = users[0]["Name"].replace("'", "\\'")
    loans = sf.query_all(
        f"SELECT Id, Name, BWE_Loan_Number__c FROM Servicing_Loan__c "
        f"WHERE Asset_Manager__c = '{user_name}' AND Current_Unpaid_Balance__c > 0"
    )

    return [
        {
            "id": r["Id"],
            "name": r["Name"],
            "bwe_loan_number": r.get("BWE_Loan_Number__c"),
            "folder": _to_folder(r.get("BWE_Loan_Number__c") or r["Name"]),
        }
        for r in loans.get("records", [])
    ]


def get_loan_by_number(loan_number: str) -> dict | None:
    """Get full loan details from Salesforce by BWE loan number."""
    sf = _get_sf()
    safe = loan_number.replace("'", "\\'")
    result = sf.query(
        f"SELECT Id, Name, BWE_Loan_Number__c, Investor__c, Investor_Name__c, Account_Name__c "
        f"FROM Servicing_Loan__c WHERE BWE_Loan_Number__c = '{safe}' LIMIT 1"
    )
    records = result.get("records", [])
    if not records:
        return None
    r = records[0]
    return {
        "id": r["Id"],
        "name": r["Name"],
        "bwe_loan_number": r["BWE_Loan_Number__c"],
        "investor_id": r.get("Investor__c"),
        "investor_name": r.get("Investor_Name__c") or "",
        "account_name": r.get("Account_Name__c") or "",
    }


def match_loan_from_text(text: str, am_email: str) -> dict | None:
    """
    Use an LLM to identify which of the AM's loans a document belongs to.
    Returns the matching loan dict or None.
    """
    from openai import AzureOpenAI

    deals = lookup_deals_by_email(am_email)
    if not deals:
        return None

    deal_list = "\n".join(
        f"- {d['bwe_loan_number']}: {d['name']}" for d in deals
    )

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You match financial documents to loan records by identifying property names, "
                    "loan numbers, or borrower entities in the text. "
                    'Respond with JSON only: {"loan_number": "...", "confidence": 0.0-1.0, "reasoning": "..."}. '
                    "Use null for loan_number if no match is found."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Which loan does this document belong to?\n\n"
                    f"DOCUMENT TEXT (first 2000 chars):\n{text[:2000]}\n\n"
                    f"LOAN LIST:\n{deal_list}"
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    parsed = json.loads(response.choices[0].message.content or "{}")
    loan_number = parsed.get("loan_number")
    if not loan_number:
        return None

    for deal in deals:
        if deal["bwe_loan_number"] == loan_number:
            return deal
    return None
