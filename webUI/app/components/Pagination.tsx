"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

export default function Pagination({
  currentPage,
  totalPages,
}: {
  currentPage: number;
  totalPages: number;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  function goToPage(page: number) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(page));
    startTransition(() => {
      router.replace(`?${params.toString()}`);
    });
  }

  if (totalPages <= 1) return null; // no pagination needed for a single page

  return (
    <div className="pagination">
      <button
        className="pagination-btn"
        onClick={() => goToPage(currentPage - 1)}
        disabled={currentPage <= 1}
      >
        ← Prev
      </button>

      <span className="pagination-info">
        Page {currentPage} of {totalPages}
      </span>

      <button
        className="pagination-btn"
        onClick={() => goToPage(currentPage + 1)}
        disabled={currentPage >= totalPages}
      >
        Next →
      </button>
    </div>
  );
}