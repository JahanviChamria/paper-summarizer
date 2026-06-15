import { useState } from "react";
import InputPanel from "./components/InputPanel.jsx";
import SummaryPanel from "./components/SummaryPanel.jsx";
import LoadingState from "./components/LoadingState.jsx";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function runRequest(promiseFactory) {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const resp = await promiseFactory();
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(
          data.detail || "Something went wrong. Please try again."
        );
      }
      setResult(data);
    } catch (e) {
      setError(e.message || "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  const handlers = {
    url: (url) =>
      runRequest(() =>
        fetch("/summarize/url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        })
      ),
    doi: (doi) =>
      runRequest(() =>
        fetch("/summarize/doi", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doi }),
        })
      ),
    pdf: (file) => {
      const form = new FormData();
      form.append("file", file);
      return runRequest(() =>
        fetch("/summarize/pdf", { method: "POST", body: form })
      );
    },
  };

  return (
    <div className="app">
      <header className="masthead">
        <h1>Paper Summarizer</h1>
        <p className="tagline">
          Drop in a paper. Get back plain English a curious person can actually
          read.
        </p>
      </header>

      <InputPanel handlers={handlers} loading={loading} error={error} />

      {loading && <LoadingState />}
      {!loading && result && <SummaryPanel result={result} />}
    </div>
  );
}
