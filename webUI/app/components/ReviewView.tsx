"use client";

import { useState } from "react";

// Collapse the section list down to at most maxLines total lines
// (headings count as lines too); the last section may be cut mid-body.
function limitSections(sections: string[], maxLines: number): string[] {
  const out: string[] = [];
  let used = 0;
  for (const section of sections) {
    const lines = section.split("\n").map(l => l.trim()).filter(Boolean);
    if (used + lines.length <= maxLines) {
      out.push(section);
      used += lines.length;
    } else {
      const remaining = maxLines - used;
      if (remaining > 0) out.push(lines.slice(0, remaining).join("\n"));
      break;
    }
  }
  return out;
}

export default function ReviewView({
  label,
  data,
  emptyMessage,
  previewLines = 4,
}: {
  label: string;
  data: any;
  emptyMessage: string;
  previewLines?: number;
}) {
  const [expanded, setExpanded] = useState(false);

  // Extract the review_outline string from the object
  const text: string | null =
    typeof data === "string"
      ? data
      : data?.review_outline ?? null;

  if (!text) {
    return (
      <div className="json-box">
        <span className="json-box-label">{label}</span>
        <p className="json-box-empty">{emptyMessage}</p>
      </div>
    );
  }

  // Split into top-level numbered sections by looking for lines starting with a digit + period
  // e.g. "1. Significance and novelty"
  const sections = text
    .split(/(?=\n\d+\.\s)/)  // split just before "1. ", "2. " etc, keeping the delimiter
    .map(s => s.trim())
    .filter(Boolean);

  const totalLines = sections.reduce(
    (n, s) => n + s.split("\n").filter(l => l.trim()).length,
    0
  );
  const isTruncated = totalLines > previewLines;
  const visibleSections = expanded ? sections : limitSections(sections, previewLines);

  return (
    <div className="json-box paper-view">
      <span className="json-box-label">{label}</span>

      {visibleSections.map((section, i) => {
        // Split each section into lines for rendering
        const lines = section.split("\n").map(l => l.trim()).filter(Boolean);
        const heading = lines[0]; // e.g. "1. Significance and novelty"
        const body = lines.slice(1); // the rest of the lines

        return (
          <div className="review-section" key={i}>
            <h4 className="review-heading">{heading}</h4>
            {body.map((line, j) => {
              // Bullet points start with * or -
              const isBullet = /^[\*\-]/.test(line);
              // Sub-bullets are indented further (start with spaces + * or -)
              const isSubBullet = /^\s{2,}[\*\-]/.test(line);
              const content = line.replace(/^[\s\*\-]+/, ""); // strip leading symbols

              return (
                <p
                  key={j}
                  className={
                    isSubBullet
                      ? "review-sub-bullet"
                      : isBullet
                      ? "review-bullet"
                      : "review-body"
                  }
                >
                  {(isBullet || isSubBullet) && (
                    <span className="review-bullet-dot">•</span>
                  )}
                  {content}
                </p>
              );
            })}
          </div>
        );
      })}

      {isTruncated && (
        <button className="json-box-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less ↑" : "Show more ↓"}
        </button>
      )}
    </div>
  );
}