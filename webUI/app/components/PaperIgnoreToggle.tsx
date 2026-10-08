"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { setIgnore } from "@/app/actions";

export default function PaperIgnoreToggle({
  id,
  ignore,
}: {
  id: number | string;
  ignore: boolean;
}) {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSaving(true);
    setMessage(null);
    const result = await setIgnore(id, e.target.checked);
    setSaving(false);
    if (result.success) {
      router.refresh();
    } else {
      setMessage(result.message);
    }
  }

  return (
    <div className="paper-ignore">
      <label className="ignore-toggle">
        <input
          type="checkbox"
          checked={ignore}
          onChange={handleChange}
          disabled={saving}
        />
        {saving ? "Saving…" : "Ignore this paper"}
      </label>
      {message && <p className="edit-message">{message}</p>}
    </div>
  );
}
