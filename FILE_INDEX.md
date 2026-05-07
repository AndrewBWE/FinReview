# FinReview — File Index

## Backend (`/backend`)

### Core API & Orchestration

| File | Purpose |
|------|---------|
| [main.py](backend/main.py) | FastAPI application entry point. Defines all HTTP endpoints: `POST /pipeline/run` (upload + start pipeline), `GET /pipeline/{id}` (poll for results), `POST /pipeline/{id}/write` (write to blob), `GET /schemas` (list available schemas). Also mounts the built React frontend as static files in production. |
| [pipeline.py](backend/pipeline.py) | Pipeline orchestrator. Holds the in-memory result store (`pipeline_results` dict). `create_pipeline()` initializes a record and returns an ID immediately. `run_pipeline()` executes the three steps in sequence — OCR → classify → extract — updating the record after each step so the frontend can poll live progress. |

### Pipeline Steps

| File | Purpose |
|------|---------|
| [ocr.py](backend/ocr.py) | Azure Document Intelligence client. Sends the uploaded PDF bytes to the `prebuilt-layout` model, then parses the response into a clean structure: list of pages (with raw text) and tables (with cell-level content). Returns `full_text` (all pages joined) used by the LLM steps downstream. |
| [classifier.py](backend/classifier.py) | LLM document classification. Sends the first 3,000 characters of OCR text to Azure OpenAI and asks it to classify the document as `rent_roll`, `operating_statement`, `tax_document`, or `unknown`. Returns the type, a confidence score (0–1), a one-sentence reasoning string, and the full prompt/response for the Prompts tab. |
| [extractor.py](backend/extractor.py) | LLM field extraction. Given the full OCR text and a `DocumentSchema`, builds a structured system prompt describing every field to extract, then calls Azure OpenAI with `response_format: json_object`. Maps the LLM response back onto the schema field list, adding `value`, `confidence`, `source`, and `alternatives` to each field. |
| [storage.py](backend/storage.py) | Azure Blob Storage writer (Phase 2). Uses `DefaultAzureCredential()` from `azure-identity` — authenticates via your existing `az login` session, no connection string or key required. Uploads extracted JSON to `bwefoundrydevbusiness / financial-review` at path `{doc_type}/{timestamp}_{filename}_extracted.json`. |

### Document Schemas (`/backend/schemas`)

| File | Purpose |
|------|---------|
| [schemas/base.py](backend/schemas/base.py) | Base dataclasses: `SchemaField` (id, label, type, required, description) and `DocumentSchema` (type, label, list of fields). Provides `to_dict()` for JSON serialization to the frontend and `to_prompt_description()` which formats the schema as a plain-text field list injected into the extraction prompt. |
| [schemas/\_\_init\_\_.py](backend/schemas/__init__.py) | Exports the `SCHEMAS` dict — maps string keys (`rent_roll`, `operating_statement`, `tax_document`) to their `DocumentSchema` instances. Used by `pipeline.py` to look up the schema after classification. |
| [schemas/rent_roll.py](backend/schemas/rent_roll.py) | Schema definition for rent rolls. 13 fields covering: property name/address, as-of date, total/occupied/vacant units, occupancy rate, gross potential rent, actual rent collected, vacancy loss, concessions, average rent per unit, and unit mix summary. |
| [schemas/operating_statement.py](backend/schemas/operating_statement.py) | Schema definition for operating statements / P&L / NOI analyses. 18 fields covering: property info, period dates, GPR, vacancy loss, other income, EGI, total operating expenses, NOI, and line-item expense categories (management, insurance, taxes, maintenance, utilities, debt service, net cash flow). |
| [schemas/tax_document.py](backend/schemas/tax_document.py) | Schema definition for tax documents (Schedule E, Form 8825, 1065, 1040, etc.). 16 fields covering: taxpayer name, EIN/SSN, tax year, form type, property address, total rents received, total expenses, depreciation, net income/loss, and expense line items. |

### Configuration

| File | Purpose |
|------|---------|
| [requirements.txt](backend/requirements.txt) | Python dependencies: `fastapi`, `uvicorn`, `python-dotenv`, `openai`, `azure-ai-documentintelligence`, `azure-identity`, `azure-storage-blob`, `pypdf`, `python-multipart`. Install into `backend/.venv` via `pip install -r requirements.txt`. |

---

## Frontend (`/frontend`)

### Configuration & Build

| File | Purpose |
|------|---------|
| [package.json](frontend/package.json) | npm manifest. Runtime deps: `react`, `react-dom`, `lucide-react` (icons), `tailwind-merge`, `clsx`. Dev deps: Vite, TypeScript, Tailwind CSS, Autoprefixer, ESLint. |
| [vite.config.ts](frontend/vite.config.ts) | Vite build config. Dev-server proxy rules forward `/pipeline`, `/schemas`, and `/health` to the FastAPI backend at `localhost:8000`, so the frontend can call the API without CORS issues during development. |
| [tailwind.config.js](frontend/tailwind.config.js) | Tailwind CSS config. Scans `index.html` and all `src/**` files for class names. No custom theme overrides — uses Tailwind defaults. |
| [postcss.config.js](frontend/postcss.config.js) | PostCSS config enabling Tailwind CSS and Autoprefixer as plugins (required by Vite's CSS pipeline). |
| [tsconfig.json](frontend/tsconfig.json) | Root TypeScript project file. References `tsconfig.app.json` (source) and `tsconfig.node.json` (Vite config). |
| [tsconfig.app.json](frontend/tsconfig.app.json) | TypeScript config for the React source. Targets ES2020, enables strict mode, JSX `react-jsx`, bundler module resolution. |
| [tsconfig.node.json](frontend/tsconfig.node.json) | TypeScript config for the Vite config file itself. Targets ES2022 with Node-appropriate settings. |
| [index.html](frontend/index.html) | HTML entry point. Single `<div id="root">` and the `src/main.tsx` module script. |

### Source Root (`/frontend/src`)

| File | Purpose |
|------|---------|
| [src/main.tsx](frontend/src/main.tsx) | React entry point. Mounts `<App />` into `#root` inside `StrictMode`. |
| [src/index.css](frontend/src/index.css) | Global stylesheet. Three Tailwind directives: `@tailwind base`, `@tailwind components`, `@tailwind utilities`. |
| [src/types.ts](frontend/src/types.ts) | All shared TypeScript types: `OcrPage`, `OcrTable`, `ExtractedField`, `SchemaField`, `Schema`, `TraceEntry`, `PromptPair`, `PipelineResult`, `DocumentRecord`, `TabId`. Single source of truth — imported by App and all components. |
| [src/lib/utils.ts](frontend/src/lib/utils.ts) | Shared utility functions: `cn()` (Tailwind class merging via clsx + tailwind-merge), `formatCurrency()`, `formatValue()` (routes to currency/percentage formatting by field type), `docTypeLabel()` (maps internal type keys to display names). |

### Components (`/frontend/src/components`)

| File | Purpose |
|------|---------|
| [components/SidebarNav.tsx](frontend/src/components/SidebarNav.tsx) | Left sidebar. Shows the FinReview logo, an "Upload PDF" button (triggers hidden file input), and the document queue — a scrollable list of all uploaded documents with status icons (spinner / checkmark / X), filename, and detected document type. Highlights the selected document. Footer shows extracted vs. processing counts. |
| [components/UploadZone.tsx](frontend/src/components/UploadZone.tsx) | Empty-state upload area shown in the main pane when no document is selected. Supports drag-and-drop and click-to-browse. Accepts PDF files only. Passes the `File` object up to `App.tsx` via `onUpload`. |
| [components/SourceViewer.tsx](frontend/src/components/SourceViewer.tsx) | **Source PDF tab.** Renders the original uploaded PDF in a full-height `<iframe>` using the browser-native viewer. The blob URL is created in `App.tsx` from the `File` object at upload time and passed down. Shows a placeholder if no URL is available. |
| [components/OcrViewer.tsx](frontend/src/components/OcrViewer.tsx) | **OCR Text tab.** Page-by-page viewer for Azure Document Intelligence output. Page navigation buttons at top. For each page: raw extracted text in a monospace block, then any detected tables rendered as HTML `<table>` elements (first row styled as header). Shows table count in the nav bar. |
| [components/ExtractionResults.tsx](frontend/src/components/ExtractionResults.tsx) | **Extracted Data tab** — the primary output view. Stats bar shows extracted/high/medium/low/missing-required counts and classification confidence. Field table shows: field label (with required `*`), field ID, extracted value (formatted by type), confidence badge (color-coded High/Medium/Low), source location, and alternative values. "Write to Blob Storage" button triggers Phase 2 write with live status feedback. |
| [components/SchemaViewer.tsx](frontend/src/components/SchemaViewer.tsx) | **Schema tab.** Shows the schema that was matched to the document: schema type key, display label, required vs. optional field counts, and a table of all field definitions (ID, label, data type, required flag, description/notes). Useful for understanding what the extractor was asked to find. |
| [components/PromptViewer.tsx](frontend/src/components/PromptViewer.tsx) | **Prompts tab.** Side-by-side section selector (Classification / Extraction) with sub-tabs for System Prompt, User Prompt, and LLM Response. Renders each in a monospace block. Core debugging surface for tuning extraction quality — shows exactly what was sent to and received from Azure OpenAI. |
| [components/PipelineTrace.tsx](frontend/src/components/PipelineTrace.tsx) | **Pipeline Trace tab.** Shows each pipeline step (OCR, Classify, Extract) as an expandable card. Status icons: animated spinner (running), green checkmark (success), red X (error), dash (skipped). Expanded cards show input and output as formatted JSON in dark-mode code blocks. Duration in ms shown per step. Errors auto-expand. |

### Application Shell

| File | Purpose |
|------|---------|
| [src/App.tsx](frontend/src/App.tsx) | Main application shell. Owns all state: document list, selected document ID, active tab, per-document blob storage status. Handles upload (POST to `/pipeline/run`, creates blob URL, adds to list), async polling (`GET /pipeline/{id}` every 1.5s until complete or error), and blob write calls. Renders `SidebarNav` + the doc header bar + tab bar + active tab content. Shows a processing overlay with the current pipeline step while a document is being processed. |

---

## Project Root

| File | Purpose |
|------|---------|
| [.env](.env) | Environment variables for all Azure services: OpenAI endpoint/key/deployment/version, Document Intelligence endpoint/key, Blob Storage account name and container name. No connection string needed — blob auth uses `DefaultAzureCredential` (`az login`). Never committed (listed in `.gitignore`). |
| [.gitignore](.gitignore) | Excludes `.env`, `__pycache__`, `.venv`, `node_modules`, `dist`, and `.DS_Store` from version control. |
| [README.md](README.md) | Project readme (currently minimal). |
