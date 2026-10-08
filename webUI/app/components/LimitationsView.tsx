"use client";

import { useState } from "react";

export default function LimitationsView({
  label,
  data,
  emptyMessage,
}: {
  label: string;
  data: any;
  emptyMessage: string;
}) {
  const [expanded, setExpanded] = useState(false);

  // Parse the data into a clean array of strings
  // Array.isArray handles jsonb columns (already parsed by Supabase)
  // JSON.parse handles text columns (still a raw string)
  let items: string[] = [];
  if (Array.isArray(data)) {
    items = data;
  } else if (typeof data === "string") {
    try {
      const parsed = JSON.parse(data);
      items = Array.isArray(parsed) ? parsed : [data];
    } catch {
      // Not valid JSON — show the raw text as a single item
      items = [data];
    }
  }

  if (!items.length) {
    return (
      <div className="json-box">
        <span className="json-box-label">{label}</span>
        <p className="json-box-empty">{emptyMessage}</p>
      </div>
    );
  }

  const PREVIEW_COUNT = 3;
  const visibleItems = expanded ? items : items.slice(0, PREVIEW_COUNT);

  return (
    <div className="json-box paper-view" style={{ textAlign: "left" }}>
      <span className="json-box-label">{label}</span>

      {visibleItems.map((item, i) => (
        <p key={i} className="limitations-item">
          {item}
        </p>
      ))}

      {items.length > PREVIEW_COUNT && (
        <button className="json-box-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less ↑" : `Show ${items.length - PREVIEW_COUNT} more ↓`}
        </button>
      )}
    </div>
  );
}