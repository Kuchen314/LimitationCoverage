"use client";

import { useState } from "react";

interface Section {
  heading: string;
  text: string;
}

interface PaperMetadata {
  title?: string | null;
  authors?: string[];
  abstractText?: string;
  sections?: Section[];
}

function truncate(text: string, length: number) {
  if (!text || text.length <= length) return text;
  return text.slice(0, length) + "…";
}

export default function PaperJsonView({
  label,
  data,
  emptyMessage,
}: {
  label: string;
  data: any;
  emptyMessage: string;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!data) {
    return (
      <div className="json-box">
        <span className="json-box-label">{label}</span>
        <p className="json-box-empty">{emptyMessage}</p>
      </div>
    );
  }

  // Handles the metadata either nested (data.metadata) or flat (data) — adjust if your shape differs
  const metadata: PaperMetadata = {
  title: data.metadata?.title ?? data.title,
  authors: data.metadata?.authors ?? data.authors,
  abstractText: data.abstractText ?? data.metadata?.abstractText,
  sections: data.sections ?? data.metadata?.sections,
};
  const authors = metadata.authors?.join(", ");
  const sections = metadata.sections ?? [];
  const visibleSections = expanded ? sections : sections.slice(0, 1);
  const canExpand = sections.length > 1 || (metadata.abstractText?.length ?? 0) > 200;

  return (
    <div className="json-box paper-view">
      <span className="json-box-label">{label}</span>

      {authors && <p className="paper-authors">{authors}</p>}

      {metadata.abstractText && (
        <p className="paper-abstract">
          <strong>Abstract: </strong>
          {expanded ? metadata.abstractText : truncate(metadata.abstractText, 200)}
        </p>
      )}

      {visibleSections.map((section, i) => (
        <div className="paper-section" key={i}>
          <h4>{section.heading}</h4>
          <p>{expanded ? section.text : truncate(section.text, 200)}</p>
        </div>
      ))}

      {canExpand && (
        <button className="json-box-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less ↑" : "Show more ↓"}
        </button>
      )}
    </div>
  );
}