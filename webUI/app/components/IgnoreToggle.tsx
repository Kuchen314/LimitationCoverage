"use client";

import { useRouter, useSearchParams } from "next/navigation";

export default function IgnoreToggle() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const showIgnored = searchParams.get("ignored") === "1";

  function toggle() {
    const params = new URLSearchParams(searchParams.toString());
    if (showIgnored) {
      params.delete("ignored");
    } else {
      params.set("ignored", "1");
    }
    params.delete("page"); // back to page 1, the paper set changes
    router.replace(`?${params.toString()}`);
  }

  return (
    <label className="ignore-toggle">
      <input type="checkbox" checked={showIgnored} onChange={toggle} />
      Show ignored papers
    </label>
  );
}
