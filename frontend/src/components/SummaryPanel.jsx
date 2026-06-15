import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function SummaryPanel({ result }) {
  const [copied, setCopied] = useState(false);
  const { title, authors, year, venue, summary, char_count } = result;

  const metaBits = [authors, venue, year].filter(Boolean).join(" · ");

  async function copy() {
    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="card summary-card">
      <div className="summary-head">
        <div>
          {title && <h2 className="paper-title">{title}</h2>}
          {metaBits && <p className="paper-meta">{metaBits}</p>}
        </div>
        <button className="copy-btn" onClick={copy} type="button">
          {copied ? "Copied ✓" : "Copy summary"}
        </button>
      </div>

      <div className="summary-body">
        <ReactMarkdown>{summary}</ReactMarkdown>
      </div>

      <p className="char-count">
        Summarized from {char_count.toLocaleString()} characters of source text.
      </p>
    </section>
  );
}
