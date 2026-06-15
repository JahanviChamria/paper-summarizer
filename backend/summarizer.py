"""Anthropic API calls and prompt logic for paper summarization."""
import os
from typing import Optional

from anthropic import Anthropic, APIError

from fetcher import PaperContent

MODEL = "claude-sonnet-4-6"
# Keep well under the context window; ~120k chars is plenty for a paper.
MAX_TEXT_CHARS = 120_000

SYSTEM_PROMPT = (
    "You are a research paper summarizer. Your job is to make academic papers "
    "genuinely understandable to a smart person who is not a specialist in this "
    "field. Avoid jargon. When you must use a technical term, explain it in plain "
    "English immediately after. Write like you are explaining to a curious friend "
    "who is good at science but has not read this paper."
)

USER_TEMPLATE = """Here is the full text of a research paper. Summarize it using this exact structure:

**What problem does this paper solve?**
One or two sentences. No jargon. What gap or question motivated this work.

**What did they actually do?**
A short paragraph. Describe the method or approach in plain language. If they built something, say what it does. If they ran an experiment, say what they tested.

**What did they find?**
The key results in 3-5 bullet points. Use numbers where the paper uses numbers. Avoid vague words like 'significant' or 'improved' without quantifying.

**Why does it matter?**
One paragraph. Real-world implications. Who benefits and how.

**One thing I would remember from this paper**
A single sentence. The most interesting or surprising finding.

**Jargon glossary**
List any technical terms that appeared in the summary, with a one-sentence plain English definition for each.

Paper text:
{text}"""

_client: Optional[Anthropic] = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it before starting the backend."
            )
        _client = Anthropic(api_key=key)
    return _client


def summarize(content: PaperContent, source_type: str) -> dict:
    text = content.text[:MAX_TEXT_CHARS]
    client = _get_client()

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {"role": "user", "content": USER_TEMPLATE.format(text=text)}
            ],
        )
    except APIError as e:
        raise RuntimeError(f"Anthropic API error: {e}") from e

    summary = "".join(
        block.text for block in resp.content if getattr(block, "type", None) == "text"
    ).strip()

    note = ""
    if content.partial:
        note = (
            "> _Note: full text was unavailable, so this summary is based on the "
            "abstract and metadata only._\n\n"
        )

    return {
        "title": content.title,
        "authors": content.authors,
        "year": content.year,
        "venue": content.venue,
        "summary": note + summary,
        "source_type": source_type,
        "char_count": len(content.text),
    }
