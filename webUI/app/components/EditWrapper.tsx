"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { saveField } from "@/app/actions";

type EditMode = "raw" | "plain" | "review" | "limitations";

// Convert stored value -> human-editable text
function toText(value: unknown, mode: EditMode): string {
  if (value == null) return "";

  switch (mode) {
    case "plain":
      return typeof value === "string" ? value : JSON.stringify(value, null, 2);

    case "review": {
      // { review_outline: "..." } -> just the outline text
      const v = value as any;
      const outline = typeof v === "string" ? v : v?.review_outline;
      return outline ?? "";
    }

    case "limitations": {
      // ["item1", "item2"] -> one item per paragraph (blank line between)
      const arr = Array.isArray(value)
        ? value
        : typeof value === "string"
        ? JSON.parse(value)
        : [];
      return arr.join("\n\n");
    }

    default: // "raw"
      return typeof value === "string" ? value : JSON.stringify(value, null, 2);
  }
}

// Convert edited text -> the string we send to the server action
function fromText(text: string, mode: EditMode): string {
  switch (mode) {
    case "plain":
      return text;

    case "review":
      // Wrap the text back into the { review_outline } object
      return JSON.stringify({ review_outline: text });

    case "limitations":
      // Split paragraphs back into an array
      return JSON.stringify(
        text
          .split(/\n\s*\n/)
          .map((s) => s.trim())
          .filter(Boolean)
      );

    default: // "raw"
      return text;
  }
}

export default function EditWrapper({
  table,
  column,
  rowId,
  value,
  mode = "raw",
  children,
}: {
  table: string;
  column: string;
  rowId: number | string | null | undefined;
  value: unknown;
  mode?: EditMode;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function startEditing() {
    try {
      setText(toText(value, mode));
    } catch {
      setText(typeof value === "string" ? value : JSON.stringify(value, null, 2));
    }
    setMessage(null);
    setEditing(true);
  }

  async function handleSave() {
    if (rowId == null) return;
    setSaving(true);
    const result = await saveField(table, column, rowId, fromText(text, mode));
    setSaving(false);
    setMessage(result.message);
    if (result.success) {
      setEditing(false);
      router.refresh();
    }
  }

  if (!editing) {
    return (
      <div className="edit-wrapper">
        {children}
        {rowId != null && (
          <button className="edit-btn" onClick={startEditing}>
            Edit
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="json-box edit-wrapper" style={{ textAlign: "left" }}>
      <span className="json-box-label">Editing: {column}</span>
      <textarea
        className="edit-textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={16}
      />
      <div className="edit-actions">
        <button className="json-box-toggle" onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          className="json-box-toggle"
          onClick={() => setEditing(false)}
          disabled={saving}
        >
          Cancel
        </button>
      </div>
      {message && <p className="edit-message">{message}</p>}
    </div>
  );
}