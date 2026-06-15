# Paper Summarizer

Turn a research paper (URL, DOI, or PDF) into a plain-English summary using Claude.

## Stack
- **Frontend:** Vite + React, single `index.css`, no UI libraries
- **Backend:** FastAPI + Python (pdfplumber, trafilatura/BeautifulSoup, httpx)
- **LLM:** Anthropic Python SDK, model `claude-sonnet-4-6`

## Setup

Set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Run everything (macOS/Linux/Git Bash)

```bash
./start.sh
```

Prints `Ready at http://localhost:5173` when both servers are up.

### Manual (Windows PowerShell)

Backend:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."
uvicorn main:app --port 8000
```

Frontend (new terminal):
```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Routes
- `POST /summarize/url`  — `{ "url": "..." }`
- `POST /summarize/doi`  — `{ "doi": "10.xxxx/xxxxx" }`
- `POST /summarize/pdf`  — multipart form, field `file`

Each returns:
```json
{ "title", "authors", "year", "venue", "summary", "source_type", "char_count" }
```
