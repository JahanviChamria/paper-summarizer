import { useRef, useState } from "react";

const TABS = [
  { id: "url", label: "URL" },
  { id: "doi", label: "DOI" },
  { id: "pdf", label: "PDF" },
];

export default function InputPanel({ handlers, loading, error }) {
  const [tab, setTab] = useState("url");
  const [url, setUrl] = useState("");
  const [doi, setDoi] = useState("");
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef(null);

  function submit(e) {
    e.preventDefault();
    if (loading) return;
    if (tab === "url" && url.trim()) handlers.url(url.trim());
    else if (tab === "doi" && doi.trim()) handlers.doi(doi.trim());
    else if (tab === "pdf" && file) handlers.pdf(file);
  }

  function pickFile(f) {
    if (f && f.type === "application/pdf") setFile(f);
    else if (f && f.name?.toLowerCase().endsWith(".pdf")) setFile(f);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files?.[0]);
  }

  const canSubmit =
    (tab === "url" && url.trim()) ||
    (tab === "doi" && doi.trim()) ||
    (tab === "pdf" && file);

  return (
    <section className="card input-card">
      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
            type="button"
          >
            {t.label}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="input-form">
        {tab === "url" && (
          <input
            className="text-input"
            type="text"
            placeholder="https://arxiv.org/abs/1706.03762"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            autoFocus
          />
        )}

        {tab === "doi" && (
          <input
            className="text-input"
            type="text"
            placeholder="10.1000/xyz123"
            value={doi}
            onChange={(e) => setDoi(e.target.value)}
            autoFocus
          />
        )}

        {tab === "pdf" && (
          <div
            className={`dropzone ${dragging ? "dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileInput.current?.click()}
          >
            <input
              ref={fileInput}
              type="file"
              accept="application/pdf,.pdf"
              hidden
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
            {file ? (
              <span className="filename">📄 {file.name}</span>
            ) : (
              <span className="drop-hint">
                Drag a PDF here, or <u>click to browse</u>
              </span>
            )}
          </div>
        )}

        <button
          className="submit-btn"
          type="submit"
          disabled={loading || !canSubmit}
        >
          {loading ? "Summarizing…" : "Summarize"}
        </button>
      </form>

      {error && <div className="error-inline">{error}</div>}
    </section>
  );
}
