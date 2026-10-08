"use client";

import { useState } from "react";

export default function JsonBox({
  label,
  content,
  emptyMessage,
  previewLines = 4,
  format = "json",
}: {
  label: string;
  content: unknown;
  emptyMessage: string;
  previewLines?: number;
  format?: "json" | "text";
}) {
  const [expanded, setExpanded] = useState(false);

  if (!content) {
    return (
      <div className="json-box">
        <span className="json-box-label">{label}</span>
        <p className="json-box-empty">{emptyMessage}</p>
      </div>
    );
  }

  const fullText = format === "text" ? String(content) : JSON.stringify(content, null, 2);
  const lines = fullText.split("\n");
  const isLong = lines.length > previewLines;
  const previewText = lines.slice(0, previewLines).join("\n");

  return (
    <div className="json-box">
      <span className="json-box-label">{label}</span>
      <pre>{expanded ? fullText : previewText}</pre>
      {isLong && (
        <button className="json-box-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less ↑" : "Show more ↓"}
        </button>
      )}
    </div>
  );
}