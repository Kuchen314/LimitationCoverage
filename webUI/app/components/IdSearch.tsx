"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

export default function IdSearch() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  function handleSearch(e: React.ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set("id", value);
    } else {
      params.delete("id");
    }
    params.delete("page"); // reset to page 1 on new search
    startTransition(() => {
      router.replace(`?${params.toString()}`);
    });
  }

  return (
    <input
      className="search-input"
      type="number"
      placeholder="Search by paper ID..."
      defaultValue={searchParams.get("id") ?? ""}
      onChange={handleSearch}
    />
  );
}