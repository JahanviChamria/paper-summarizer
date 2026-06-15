"""FastAPI app exposing paper summarization routes."""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import fetcher
import summarizer

app = FastAPI(title="paper-summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UrlBody(BaseModel):
    url: str


class DoiBody(BaseModel):
    doi: str


def _summarize_or_error(content, source_type):
    try:
        return summarizer.summarize(content, source_type)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/summarize/url")
def summarize_url(body: UrlBody):
    url = body.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="A URL is required.")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    try:
        content = fetcher.from_url(url)
    except fetcher.FetchError as e:
        raise HTTPException(status_code=422, detail=e.message)
    return _summarize_or_error(content, "url")


@app.post("/summarize/doi")
def summarize_doi(body: DoiBody):
    try:
        content = fetcher.from_doi(body.doi)
    except fetcher.FetchError as e:
        raise HTTPException(status_code=422, detail=e.message)
    return _summarize_or_error(content, "doi")


@app.post("/summarize/pdf")
async def summarize_pdf(file: UploadFile = File(...)):
    if file.content_type not in ("application/pdf", "application/octet-stream") and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    try:
        content = fetcher.from_pdf_bytes(data)
    except fetcher.FetchError as e:
        raise HTTPException(status_code=422, detail=e.message)
    if content.title is None:
        content.title = (file.filename or "").rsplit(".", 1)[0] or None
    return _summarize_or_error(content, "pdf")
