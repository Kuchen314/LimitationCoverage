"use client";

import { useRouter, useSearchParams } from "next/navigation";

const SETS = ["1", "2", "3"];

export default function ReviewSetPicker() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const current = searchParams.get("rev") ?? "1";

  function select(set: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (set === "1") {
      params.delete("rev"); // set 1 is the default, keep the URL clean
    } else {
      params.set("rev", set);
    }
    router.replace(`?${params.toString()}`);
  }

  return (
    <div className="review-set-picker">
      <span className="review-set-label">Review set:</span>
      {SETS.map((s) => (
        <button
          key={s}
          className={`pagination-btn${s === current ? " review-set-active" : ""}`}
          onClick={() => select(s)}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
