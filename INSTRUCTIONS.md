# FinReview — How to Run

## Prerequisites

These are already set up on this machine — no action needed:
- **Azure CLI** logged in as `asmith9@bwe.com` (`az login` already done)
- **Node.js** v24 / npm 11 (frontend)
- **Python 3.9** (backend)
- **Backend `.venv`** already created with all packages installed

---

## Every Time You Start the App

You need two terminal windows running simultaneously — one for the backend, one for the frontend.

### Terminal 1 — Backend

```bash
cd /Users/andrew.smith/FinReview/backend
.venv/bin/python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — Frontend

```bash
cd /Users/andrew.smith/FinReview/frontend
npm run dev
```

You should see:
```
  VITE ready in Xms
  ➜  Local:   http://localhost:5173/
```

### Open the App

Go to **http://localhost:5173** in your browser.

---

## First Time Only (Already Done)

If you ever need to rebuild the environment from scratch:

```bash
# Backend — create venv and install packages
cd /Users/andrew.smith/FinReview/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Frontend — install npm packages
cd /Users/andrew.smith/FinReview/frontend
npm install
```

---

## How to Use the App

1. **Upload a PDF** — click "Upload PDF" in the sidebar or drag a file onto the main area
2. **Watch the pipeline run** — switch to the **Pipeline Trace** tab to see OCR → Classify → Extract steps live
3. **Review results** — the **Extracted Data** tab is the main output: all fields, confidence badges, and source locations
4. **Inspect the details** using the other tabs:
   - **Source PDF** — original document
   - **OCR Text** — raw text and tables extracted by Azure Document Intelligence, page by page
   - **Schema** — the field definitions that were used for extraction
   - **Prompts** — exact prompts sent to and responses received from Azure OpenAI (key for debugging bad extractions)
5. **Write to Blob Storage** — once extraction is complete, click "Write to Blob Storage" in the Extracted Data tab to push the result to `bwefoundrydevbusiness / financial-review`

---

## Blob Storage Auth

No key or connection string is needed. The backend authenticates to Azure Blob Storage using your active `az login` session (`asmith9@bwe.com`). As long as you're logged in, writes will work.

To verify you're still logged in:
```bash
az account show
```

If it fails, re-authenticate:
```bash
az login
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Backend crashes on start | Make sure you're running `.venv/bin/python main.py`, not `python main.py` |
| `ModuleNotFoundError` | Re-run `.venv/bin/pip install -r requirements.txt` |
| Frontend can't reach the API | Make sure the backend is running on port 8000 before starting the frontend |
| Blob write fails with auth error | Run `az login` and try again |
| PDF upload returns an error | Only `.pdf` files are accepted |
| Document classified as "unknown" | The Prompts tab will show what text was sent to the LLM — check if OCR extracted meaningful content |
