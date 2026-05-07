import asyncio
import zipfile
import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from pipeline import create_pipeline, run_pipeline, get_result
from schemas import SCHEMAS
from storage import write_extraction, KNOWN_FOLDERS
from sf_client import lookup_deals_by_email
from sorter import sort_pipeline

app = FastAPI(title="FinReview API")
executor = ThreadPoolExecutor(max_workers=4)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


ALLOWED_EXTENSIONS = (".pdf", ".xlsx", ".xls")


def _is_allowed(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


@app.post("/pipeline/run")
async def pipeline_run(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_bytes = await file.read()
    loop = asyncio.get_event_loop()

    # ZIP: extract and fan out each eligible file as its own pipeline
    if file.filename.lower().endswith(".zip"):
        try:
            zf = zipfile.ZipFile(io.BytesIO(file_bytes))
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file")

        pipeline_ids = []
        for entry in zf.infolist():
            if entry.is_dir() or not _is_allowed(entry.filename):
                continue
            name = Path(entry.filename).name  # strip any folder paths inside the zip
            entry_bytes = zf.read(entry.filename)
            pid = create_pipeline(name)
            loop.run_in_executor(executor, run_pipeline, pid, entry_bytes)
            pipeline_ids.append({"id": pid, "filename": name})

        if not pipeline_ids:
            raise HTTPException(status_code=400, detail="ZIP contains no supported files (.pdf, .xlsx, .xls)")
        return {"ids": pipeline_ids}

    # Single file
    if not _is_allowed(file.filename):
        raise HTTPException(status_code=400, detail="Only .pdf, .xlsx, .xls, and .zip files are accepted")

    pipeline_id = create_pipeline(file.filename)
    loop.run_in_executor(executor, run_pipeline, pipeline_id, file_bytes)
    return {"id": pipeline_id}


@app.get("/pipeline/{pipeline_id}")
def pipeline_status(pipeline_id: str):
    result = get_result(pipeline_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline result not found")
    return {k: v for k, v in result.items() if not k.startswith("_")}


class WriteRequest(BaseModel):
    deal_folder: str


class SortRequest(BaseModel):
    loan_number: Optional[str] = None
    am_email: Optional[str] = None


@app.post("/pipeline/{pipeline_id}/write")
def pipeline_write(pipeline_id: str, body: WriteRequest):
    result = get_result(pipeline_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline result not found")
    if result["status"] != "complete":
        raise HTTPException(status_code=400, detail="Pipeline not yet complete")
    return write_extraction(result, deal_folder=body.deal_folder)


@app.post("/pipeline/{pipeline_id}/sort")
def pipeline_sort(pipeline_id: str, body: SortRequest):
    result = get_result(pipeline_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline result not found")
    if result["status"] != "complete":
        raise HTTPException(status_code=400, detail="Pipeline not yet complete")
    file_bytes = result.get("_file_bytes")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File bytes not available — pipeline may have been restarted")
    return sort_pipeline(
        result,
        file_bytes,
        loan_number=body.loan_number,
        am_email=body.am_email,
    )


@app.get("/deals")
def get_deals(email: str):
    """Return active deals assigned to the asset manager with this email."""
    deals = lookup_deals_by_email(email)
    return {"email": email, "deals": deals}


@app.get("/folders")
def list_folders():
    return {"folders": sorted(KNOWN_FOLDERS)}


@app.get("/schemas")
def list_schemas():
    return {k: v.to_dict() for k, v in SCHEMAS.items()}


static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
