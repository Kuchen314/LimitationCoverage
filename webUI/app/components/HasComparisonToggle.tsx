"use client";

import { useRouter, useSearchParams } from "next/navigation";

export default function HasComparisonToggle() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const active = searchParams.get("hascomparison") === "1";

  function toggle() {
    const params = new URLSearchParams(searchParams.toString());
    if (active) {
      params.delete("hascomparison");
    } else {
      params.set("hascomparison", "1");
    }
    params.delete("page"); // back to page 1, the paper set changes
    router.replace(`?${params.toString()}`);
  }

  return (
    <label className="ignore-toggle">
      <input type="checkbox" checked={active} onChange={toggle} />
      Hide papers without comparison
    </label>
  );
}
