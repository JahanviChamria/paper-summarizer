"""Fetch and extract paper content from URLs, DOIs, or PDF bytes."""
import io
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx
import pdfplumber
import trafilatura
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept": "*/*"}

# Minimum characters of extracted text we consider a "real" full-text extraction.
MIN_FULLTEXT_CHARS = 400


class FetchError(Exception):
    """Raised with a user-facing message when content cannot be fetched."""

    def __init__(self, message: str, code: str = "fetch_failed"):
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass
class PaperContent:
    text: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[str] = None
    venue: Optional[str] = None
    partial: bool = False  # True when only an abstract / limited text was found
    meta: dict = field(default_factory=dict)


def _client() -> httpx.Client:
    return httpx.Client(
        headers=HEADERS,
        follow_redirects=True,
        timeout=30.0,
    )


def extract_pdf_text(data: bytes) -> str:
    """Extract text from raw PDF bytes. Returns '' if nothing extractable."""
    chunks = []
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                if t.strip():
                    chunks.append(t)
    except Exception as e:  # corrupt / unreadable PDF
        raise FetchError(
            "This PDF could not be parsed. It may be corrupt or password protected.",
            code="pdf_parse_failed",
        ) from e
    return "\n\n".join(chunks).strip()


def from_pdf_bytes(data: bytes) -> PaperContent:
    text = extract_pdf_text(data)
    if len(text) < 20:
        raise FetchError(
            "This PDF appears to be a scanned image. Text extraction failed.",
            code="scanned_pdf",
        )
    title = _guess_pdf_title(text)
    return PaperContent(text=text, title=title)


def _guess_pdf_title(text: str) -> Optional[str]:
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 15 and not line.lower().startswith(("abstract", "introduction")):
            return line[:300]
    return None


def _extract_html(html: str, url: str) -> PaperContent:
    """Pull readable text + basic metadata from an HTML page."""
    text = ""
    extracted = trafilatura.extract(
        html, include_comments=False, include_tables=False, favor_recall=True
    )
    if extracted:
        text = extracted.strip()

    soup = BeautifulSoup(html, "html.parser")

    if len(text) < MIN_FULLTEXT_CHARS:
        # Fall back to crude body text.
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        body_text = soup.get_text(separator="\n")
        body_text = re.sub(r"\n{3,}", "\n\n", body_text).strip()
        if len(body_text) > len(text):
            text = body_text

    title = _meta(soup, ["citation_title", "og:title"]) or (
        soup.title.string.strip() if soup.title and soup.title.string else None
    )
    authors = _meta_all(soup, "citation_author")
    year = _meta(soup, ["citation_publication_date", "citation_date"])
    if year:
        m = re.search(r"\d{4}", year)
        year = m.group(0) if m else None
    venue = _meta(soup, ["citation_journal_title", "citation_conference_title"])

    return PaperContent(
        text=text,
        title=title,
        authors=", ".join(authors) if authors else None,
        year=year,
        venue=venue,
        partial=len(text) < MIN_FULLTEXT_CHARS,
    )


def _meta(soup: BeautifulSoup, names: list) -> Optional[str]:
    for name in names:
        tag = soup.find("meta", attrs={"name": name}) or soup.find(
            "meta", attrs={"property": name}
        )
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _meta_all(soup: BeautifulSoup, name: str) -> list:
    return [
        t["content"].strip()
        for t in soup.find_all("meta", attrs={"name": name})
        if t.get("content")
    ]


def from_url(url: str) -> PaperContent:
    """Fetch a URL; parse as PDF if it is one, otherwise as HTML."""
    try:
        with _client() as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status in (401, 403, 429):
            raise FetchError(
                "Could not access full text. Showing abstract-only summary if available.",
                code="access_blocked",
            ) from e
        raise FetchError(
            f"The page returned an error (HTTP {status}).", code="http_error"
        ) from e
    except httpx.HTTPError as e:
        raise FetchError(
            "Could not reach that URL. Check the address and try again.",
            code="network_error",
        ) from e

    ctype = resp.headers.get("content-type", "").lower()
    is_pdf = "application/pdf" in ctype or url.lower().split("?")[0].endswith(".pdf")
    if is_pdf or resp.content[:5] == b"%PDF-":
        content = from_pdf_bytes(resp.content)
        return content

    content = _extract_html(resp.text, str(resp.url))
    if not content.text:
        raise FetchError(
            "Could not access full text. Showing abstract-only summary if available.",
            code="access_blocked",
        )
    return content


def _semantic_scholar(doi: str) -> Optional[PaperContent]:
    api = (
        f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        "?fields=title,abstract,authors,year,venue"
    )
    try:
        with _client() as client:
            resp = client.get(api)
            if resp.status_code != 200:
                return None
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    abstract = data.get("abstract")
    if not abstract:
        return None
    authors = ", ".join(a.get("name", "") for a in data.get("authors") or [])
    return PaperContent(
        text=f"Title: {data.get('title','')}\n\nAbstract: {abstract}",
        title=data.get("title"),
        authors=authors or None,
        year=str(data["year"]) if data.get("year") else None,
        venue=data.get("venue") or None,
        partial=True,
    )


def from_doi(doi: str) -> PaperContent:
    doi = doi.strip()
    if doi.lower().startswith("doi:"):
        doi = doi[4:].strip()
    if not re.match(r"^10\.\d{4,9}/\S+$", doi):
        raise FetchError(
            "DOI not found. Check the format: 10.xxxx/xxxxx", code="bad_doi"
        )

    url = f"https://doi.org/{doi}"
    content = None
    try:
        content = from_url(url)
    except FetchError:
        content = None

    # If full-text fetch failed or was thin, try Semantic Scholar abstract.
    if content is None or content.partial or len(content.text) < MIN_FULLTEXT_CHARS:
        ss = _semantic_scholar(doi)
        if ss is not None:
            # Prefer richer metadata from full-text fetch if we had any.
            if content is not None:
                ss.title = ss.title or content.title
                ss.venue = ss.venue or content.venue
            return ss
        if content is None:
            raise FetchError(
                "DOI not found. Check the format: 10.xxxx/xxxxx", code="bad_doi"
            )

    return content
