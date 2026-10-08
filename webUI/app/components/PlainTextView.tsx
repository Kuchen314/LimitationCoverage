"use client";

import { useState } from "react";

export default function PlainTextView({
  label,
  text,
  emptyMessage,
  previewChars = 400,
}: {
  label: string;
  text: string | null | undefined;
  emptyMessage: string;
  previewChars?: number;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!text) {
    return (
      <div className="json-box">
        <span className="json-box-label">{label}</span>
        <p className="json-box-empty">{emptyMessage}</p>
      </div>
    );
  }

  const paragraphs = text.split(/\n\s*\n/); // split on blank lines between paragraphs
  const isLong = text.length > previewChars;

  const displayText = expanded
    ? paragraphs
    : [text.slice(0, previewChars) + (isLong ? "…" : "")];

  return (
    <div className="json-box paper-view">
      <span className="json-box-label">{label}</span>

      {displayText.map((para, i) => (
        <p key={i} className="paper-paragraph">
          {para}
        </p>
      ))}

      {isLong && (
        <button className="json-box-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less ↑" : "Show more ↓"}
        </button>
      )}
    </div>
  );
}