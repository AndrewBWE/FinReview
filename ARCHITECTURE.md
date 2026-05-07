# FinReview — Architecture

**Purpose**: Automated financial document processing for BWE asset managers. Receives forwarded client emails containing financial PDFs/spreadsheets, classifies and extracts data from each document, and routes files into the correct Azure Blob Storage deal folder.

---

## System Overview

```
Email (forwarded by AM)
        │
        ▼
  FastAPI Backend  ←── React Frontend (drag-and-drop for dev/testing)
        │
  ┌─────┴──────────────────────────────────────────────────┐
  │                    Pipeline                            │
  │  1. OCR / Excel Read  →  Azure Document Intelligence   │
  │  2. Page Split & Classify  →  heuristic + LLM fallback │
  │  3. Field Extraction  →  Azure OpenAI GPT              │
  └─────────────────────────────────────────────────────────┘
        │
  ┌─────┴──────────────────────────────────────────────────┐
  │                    Sorter                              │
  │  1. Resolve Loan  →  cover letter / regex / LLM match  │
  │  2. Find Lender Folder  →  fuzzy match on Investor     │
  │  3. Find Deal Folder  →  loan number / fuzzy name      │
  │  4. Write files  →  Azure Blob Storage                 │
  └─────────────────────────────────────────────────────────┘
```

---

## Backend (`/backend`)

### `main.py` — FastAPI application

| Endpoint | Method | Purpose |
|---|---|---|
| `/pipeline/run` | POST | Upload file (PDF, XLSX, XLS, ZIP); starts async pipeline |
| `/pipeline/{id}` | GET | Poll pipeline status and results |
| `/pipeline/{id}/sort` | POST | Trigger blob sort for a completed pipeline |
| `/pipeline/{id}/write` | POST | Legacy: write extraction JSON to a specified deal folder |
| `/deals` | GET | Lookup active deals for an AM email via Salesforce |
| `/folders` | GET | List known document type subfolder names |
| `/schemas` | GET | Return all extraction schemas |
| `/health` | GET | Health check |

ZIP uploads are expanded server-side: each eligible file becomes its own pipeline, and the endpoint returns `{"ids": [...]}`.

### `pipeline.py` — Pipeline orchestration

Runs synchronously in a `ThreadPoolExecutor` (non-blocking for FastAPI). Stages:

1. **OCR** — `run_ocr()` for PDFs (Azure Document Intelligence), `run_excel()` for spreadsheets
2. **Split & Classify** — `split_pages()` produces segments; each segment is consecutive pages of the same document type
3. **Extract** — `extract_fields()` called per segment using the schema for that document type

Results stored in `pipeline_results` dict keyed by UUID. `_file_bytes` stored for the sorter but excluded from API responses.

Top-level `document_type` is set to the single type if all segments agree; otherwise `"mixed"`.

### `splitter.py` — Page-level document splitting

For PDFs only (Excel is always treated as a single document).

- Each page's text is classified independently
- Pages with < 80 characters inherit the previous page's classification (no wasted LLM call)
- Consecutive same-type pages are grouped into segments
- Returns: `[{page_indices, page_numbers, document_type, confidence, text, pages}]`

### `heuristic_classifier.py` — Keyword scoring (cost control)

Scores each page against regex keyword rules for each document type. Returns a classification if confidence ≥ 0.75; otherwise returns `"unknown"` to trigger LLM fallback.

- Fixed denominator `_TARGET_SCORE = 8.0` — adding new patterns never dilutes existing scores
- Uses `re.IGNORECASE` (not `.lower()`) to preserve pattern accuracy
- Covered types: `cover_letter`, `rent_roll`, `operating_statement`, `balance_sheet`, `tax_document`
- Result: ~10/11 heuristic on a typical merged PDF, greatly reducing LLM classification costs

### `sorter.py` — Blob routing

Called by `/pipeline/{id}/sort` with optional `loan_number` and `am_email`.

Loan resolution order:
1. Explicit `loan_number` from request body
2. Regex scan of OCR text for 8-digit loan numbers (pattern: `LOAN # XXXXXXXX` or bare 8-digit)
3. LLM match: get AM's active loans from Salesforce, ask GPT to match doc text to loan list

Once loan is resolved → `investor_name` from Salesforce → fuzzy match to lender folder → find deal subfolder.

For each document segment (skipping cover letters):
- Extract reporting period from text (`period_extractor.py`)
- Build filename: `{Schema Label} - {Period}.{ext}` e.g. `Rent Roll - Q4 2025.pdf`
- Extract only the relevant PDF pages (for multi-segment PDFs) using `pypdf`
- Write to `{lender_folder}/{deal_folder}/{doc_type}/{filename}`

Returns `{"status": "no_folder"}` if no deal folder exists (deal folders are not auto-created).

### `storage.py` — Azure Blob Storage client

Uses `DefaultAzureCredential` (no keys; requires `az login` locally, managed identity in prod).

**Key functions:**

| Function | Purpose |
|---|---|
| `list_lender_folders()` | Walk top-level blob prefixes; return those starting with a digit |
| `find_lender_folder(investor_name)` | Fuzzy match: substring → 0.95, token → 0.80, SequenceMatcher fallback |
| `find_deal_folder(lender_folder, loan_number, loan_name)` | Loan number prefix match first; fuzzy name fallback (≥ 0.6) |
| `write_to_deal_folder(deal_path, filename, data)` | Write bytes to blob, overwrite=True |
| `write_extraction(pipeline_result, deal_folder)` | Legacy: write extracted JSON blobs by doc type |

### `sf_client.py` — Salesforce integration

Uses OAuth 2.0 **Client Credentials** flow (server-to-server, no user interaction). External Client App: `FinReview` in the BWE Full sandbox.

**Key functions:**

| Function | Purpose |
|---|---|
| `lookup_deals_by_email(email)` | Find User by email → query `Servicing_Loan__c` where `Asset_Manager__c = user.Name` and `Current_Unpaid_Balance__c > 0` |
| `get_loan_by_number(loan_number)` | Fetch loan record; returns `investor_name` from `Investor_Name__c` (string field, not the lookup ID) |
| `match_loan_from_text(text, am_email)` | LLM-assisted match: get AM's loans, ask GPT to identify which loan the document belongs to |

**Sandbox note**: User emails in the sandbox have `.invalid` appended (e.g. `coty.dowell@bwe.com.invalid`). Production will use real addresses.

### `schemas/` — Field extraction schemas

Each schema defines the fields to extract from a document type. Registered in `SCHEMAS` dict.

| Schema | Key Fields |
|---|---|
| `cover_letter` | loan_number, site_id, site_name, period, borrower_name, sender_name, document_list |
| `rent_roll` | property_name, as_of_date, total_units, occupancy_rate, gross_potential_rent, effective_gross_income |
| `operating_statement` | property_name, period_start, period_end, effective_gross_income, total_expenses, net_operating_income |
| `balance_sheet` | entity_name, as_of_date, total_assets, total_liabilities, total_equity |
| `tax_document` | entity_name, tax_year, total_income, total_deductions, taxable_income |
| `personal_financial_statement` | borrower_name, as_of_date, total_assets, total_liabilities, net_worth |
| `loan_agreement` | loan_number, borrower_name, lender_name, loan_amount, interest_rate, maturity_date |
| `appraisal` | property_address, appraisal_date, appraised_value, appraiser_name |

### `period_extractor.py`

Extracts the reporting period from document text. Output examples:
- `"quarter ended December 31, 2025"` → `"Q4 2025"`
- `"Year Ended December 31, 2025"` → `"December 2025"`  
- `"1/1/2026"` → `"January 2026"`
- No date found → current month/year (e.g. `"May 2026"`)

---

## Blob Storage Structure

```
financial-review/           ← container
├── 001 - Thrivent/
│   └── {loan_number} - {loan_name}/
│       ├── rent_roll/
│       │   └── 20250106_120000_WellingtonGreen_Rent Roll - Q4 2025.pdf
│       └── operating_statement/
│           └── 20250106_120000_WellingtonGreen_Operating Statement - Q4 2025.pdf
├── 014 - Voya/
│   └── 01497009 - Wellington Green Commons/
│       └── ...
└── ...
```

Lender folders are pre-populated via `setup_blob_folders.py`. Deal folders are created manually (or will be created on demand in a future iteration). If no deal folder is found, the sorter exits with `status: "no_folder"`.

**Current lenders (31):** Thrivent, American Fidelity, Nationwide, Genworth, State Farm, Sun Life, Lincoln, Empower, Corebridge Financial, Situs, Voya, PPM, American Equity, Farm Bureau, Farm Bureau MI, Protective, One America, Guardian, Columbian Mutual, KCL, UNUM, PIMCO, CorAmerica, CNA, JPM, Everlake, ANICO, Arrowmark, Woodmen, Assurity, TurnCap.

---

## Frontend (`/frontend`)

React + TypeScript + Vite + Tailwind CSS.

### Key components

| Component | Purpose |
|---|---|
| `SidebarNav` | Document list, upload button |
| `UploadZone` | Full-area drop target when no doc selected |
| `ExtractionResults` | Renders extracted fields table, Write to Storage button |
| `SourceViewer` | Embedded PDF viewer via `<object>` |
| `OcrViewer` | Raw OCR text per page |
| `SchemaViewer` | JSON schema definition for the classified doc type |
| `PromptViewer` | LLM prompts used during extraction |
| `PipelineTrace` | Live step-by-step pipeline progress |

### Sort testing UI

A "Simulated Email" bar at the top of the main panel lets developers enter a sender email and optional loan number to simulate the metadata that will eventually come from a forwarded email. Once a pipeline completes, a **Sort to Blob** button appears in the document header; clicking it calls `POST /pipeline/{id}/sort` and shows the resolved deal path inline.

---

## Data Flow (full sort)

```
1. AM forwards email with attachments
        ↓
2. Email handler (future) extracts files, sender email → POST /pipeline/run
        ↓
3. Pipeline: OCR → split → classify → extract
        ↓  (status: complete)
4. POST /pipeline/{id}/sort  {am_email, loan_number?}
        ↓
5. Sorter resolves loan via cover letter / regex / Salesforce + LLM
        ↓
6. Salesforce: Investor_Name__c → fuzzy match → lender folder in blob
        ↓
7. Blob: scan deal subfolders → match loan number / loan name
        ↓
8. Write each document segment to:
   {lender_folder}/{deal_folder}/{doc_type}/{Label} - {Period}.{ext}
```

---

## Environment Variables

| Variable | Used by | Description |
|---|---|---|
| `AZURE_STORAGE_ACCOUNT_NAME` | `storage.py` | Blob account (default: `bwefoundrydevbusiness`) |
| `AZURE_STORAGE_CONTAINER_NAME` | `storage.py` | Container (default: `financial-review`) |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | `ocr.py` | Document Intelligence endpoint |
| `AZURE_OPENAI_ENDPOINT` | `extractor.py`, `classifier.py` | Azure OpenAI endpoint |
| `AZURE_OPENAI_DEPLOYMENT` | extractor | GPT deployment name |
| `SF_CONSUMER_KEY` | `sf_client.py` | FinReview External Client App key |
| `SF_CONSUMER_SECRET` | `sf_client.py` | FinReview External Client App secret |
| `SF_LOGIN_URL` | `sf_client.py` | Salesforce org URL (sandbox: `https://bwecap--full.sandbox.my.salesforce.com`) |

All Azure credentials resolved via `DefaultAzureCredential` (no explicit keys needed if `az login` is active).

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
az login
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # → http://localhost:5173
```

The Vite dev server proxies `/pipeline/*`, `/deals`, `/folders`, `/schemas` to `localhost:8000`.
