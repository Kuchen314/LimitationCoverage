"use client";

import { useState } from "react";

interface ComparisonData {
  "Review 1 Coverage"?: string;
  "Review 2 Coverage"?: string;
  Differences?: string[] | string;
  Scores?: {
    "Review 1"?: Record<string, number>;
    "Review 2"?: Record<string, number>;
    Disagreements?: string;
  };
  Decision?: string;
}

export default function ComparisonView({
  label,
  data,
  emptyMessage,
}: {
  label: string;
  data: any;
  emptyMessage: string;
}) {
  const [expanded, setExpanded] = useState(false);

  // Parse if it's a raw string, use directly if already an object
  let parsed: ComparisonData | null = null;
  let parseFailed = false;
  if (data) {
    if (typeof data === "string") {
      try {
        parsed = JSON.parse(data);
      } catch {
        // Not valid JSON — fall through to the raw-text fallback below
        parseFailed = true;
      }
    } else {
      parsed = data;
    }
  }

  if (parseFailed) {
    return (
      <div className="json-box paper-view" style={{ textAlign: "left" }}>
        <span className="json-box-label">{label}</span>
        <p className="comparison-coverage-text">{data}</p>
      </div>
    );
  }

  if (!parsed) {
    return (
      <div className="json-box">
        <span className="json-box-label">{label}</span>
        <p className="json-box-empty">{emptyMessage}</p>
      </div>
    );
  }

  // Scores table: collect the criteria rows from both reviews (union, order kept)
  const scores = parsed.Scores;
  const r1Scores = scores?.["Review 1"] ?? {};
  const r2Scores = scores?.["Review 2"] ?? {};
  const criteria = [
    ...Object.keys(r1Scores),
    ...Object.keys(r2Scores).filter((c) => !(c in r1Scores)),
  ];

  const rawDiffs = parsed["Differences"] ?? [];
const differences: string[] = Array.isArray(rawDiffs)
  ? rawDiffs
  : typeof rawDiffs === "string"
  ? rawDiffs
      .split(/\n-\s*/)      // split on newline + dash (the bullet separator)
      .map(s => s.replace(/^-\s*/, "").trim())  // clean any leading dash on first item
      .filter(Boolean)      // remove empty strings
  : [];
  const PREVIEW_COUNT = 2;
  const visibleDiffs = expanded ? differences : differences.slice(0, PREVIEW_COUNT);

  return (
    <div className="json-box paper-view" style={{ textAlign: "left" }}>
      <span className="json-box-label">{label}</span>

      {/* Coverage summary rows */}
      <div className="comparison-coverage">
        <div className="comparison-coverage-row">
          <span className="comparison-coverage-tag">Review 1</span>
          <span className="comparison-coverage-text">{parsed["Review 1 Coverage"]}</span>
        </div>
        <div className="comparison-coverage-row">
          <span className="comparison-coverage-tag">Review 2</span>
          <span className="comparison-coverage-text">{parsed["Review 2 Coverage"]}</span>
        </div>
      </div>

      {/* Differences list */}
      {differences.length > 0 && (
        <>
          <p className="comparison-diff-heading">Differences</p>
          <ul className="limitations-list">
            {visibleDiffs.map((diff, i) => (
              <li key={i} className="limitations-item">
                {diff}
              </li>
            ))}
          </ul>

          {differences.length > PREVIEW_COUNT && (
            <button className="json-box-toggle" onClick={() => setExpanded(!expanded)}>
              {expanded
                ? "Show less ↑"
                : `Show ${differences.length - PREVIEW_COUNT} more ↓`}
            </button>
          )}
        </>
      )}

      {/* Scores table */}
      {criteria.length > 0 && (
        <div className="comparison-scores">
          <p className="comparison-diff-heading">Scores</p>
          <table className="comparison-scores-table">
            <thead>
              <tr>
                <th></th>
                <th>Review 1</th>
                <th>Review 2</th>
              </tr>
            </thead>
            <tbody>
              {criteria.map((criterion) => {
                const v1 = r1Scores[criterion];
                const v2 = r2Scores[criterion];
                const mismatch = v1 != null && v2 != null && v1 !== v2;
                return (
                  <tr key={criterion}>
                    <td className="comparison-score-name">{criterion}</td>
                    <td className={mismatch ? "comparison-score-diff" : ""}>
                      {v1 ?? "–"}
                    </td>
                    <td className={mismatch ? "comparison-score-diff" : ""}>
                      {v2 ?? "–"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {scores?.Disagreements && (
            <p className="comparison-disagreements">
              <strong>Disagreements: </strong>
              {scores.Disagreements}
            </p>
          )}
        </div>
      )}

      {/* Decision */}
      {parsed.Decision && (
        <div className="comparison-decision">
          <p className="comparison-diff-heading">Decision</p>
          <p className="comparison-coverage-text">{parsed.Decision}</p>
        </div>
      )}
    </div>
  );
}