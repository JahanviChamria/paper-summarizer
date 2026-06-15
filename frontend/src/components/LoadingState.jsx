import { useEffect, useState } from "react";

const MESSAGES = [
  "Reading the paper…",
  "Translating science into English…",
  "Finding the actual point…",
  "Almost done…",
];

export default function LoadingState() {
  const [i, setI] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setI((prev) => (prev + 1) % MESSAGES.length);
    }, 2000);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="card loading-card">
      <div className="spinner" aria-hidden="true" />
      <p className="loading-msg">{MESSAGES[i]}</p>
    </section>
  );
}
