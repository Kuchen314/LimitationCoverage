import Link from "next/link";
import { createClient } from "@/utils/supabase/server";
import Pagination from "@/app/components/Pagination";
import IdSearch from "@/app/components/IdSearch";
import IgnoreToggle from "@/app/components/IgnoreToggle";
import ReviewSetPicker from "@/app/components/ReviewSetPicker";
import HasReviewToggle from "@/app/components/HasReviewToggle";
import HasComparisonToggle from "@/app/components/HasComparisonToggle";
import { Suspense } from "react";

const PAGE_SIZE = 50;
const REVIEW_SETS = ["1", "2", "3"];

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{
    page?: string;
    id?: string;
    ignored?: string;
    rev?: string;
    hasreview?: string;
    hascomparison?: string;
  }>;
}) {
  const {
    page = "1",
    id = "",
    ignored = "",
    rev = "1",
    hasreview = "",
    hascomparison = "",
  } = await searchParams;
  const currentPage = Math.max(1, parseInt(page, 10) || 1);
  const showIgnored = ignored === "1";
  const reviewSet = REVIEW_SETS.includes(rev) ? rev : "1";
  const onlyWithReview = hasreview === "1";
  const onlyWithComparison = hascomparison === "1";
  const suffix = reviewSet === "1" ? "" : reviewSet;
  const from = (currentPage - 1) * PAGE_SIZE;
  const to = from + PAGE_SIZE - 1;

  const supabase = await createClient();

  let query = supabase
    .from("paper")
    .select("id, title, ignore", { count: "exact" })
    .order("id")
    .range(from, to);

  if (!showIgnored) {
    // Existing rows may have ignore = null, so filter on "not true"
    query = query.or("ignore.is.null,ignore.eq.false");
  }

  if (onlyWithReview) {
    // Keep papers where at least one review column of the selected set is filled;
    // chained .or() filters are ANDed with the one above
    query = query.or(
      `review${suffix}.not.is.null,review_edited${suffix}.not.is.null`
    );
  }

  if (onlyWithComparison) {
    query = query.not(`comparison${suffix}`, "is", null);
  }

  if (id) {
    query = query.eq("id", parseInt(id, 10));
  }

  const { data: papers, error, count } = await query;
  const totalPages = Math.ceil((count ?? 0) / PAGE_SIZE);

  if (error) {
    return <p>Error loading papers: {error.message}</p>;
  }

  return (
    <main className="catalog">
      <Suspense>
        <IdSearch />
      </Suspense>
      <Suspense>
        <IgnoreToggle />
      </Suspense>
      <Suspense>
        <HasReviewToggle />
      </Suspense>
      <Suspense>
        <HasComparisonToggle />
      </Suspense>
      <Suspense>
        <ReviewSetPicker />
      </Suspense>

      {papers?.map((paper) => (
        <div
          className={`catalog-entry${paper.ignore ? " catalog-entry-ignored" : ""}`}
          key={paper.id}
        >
          <span className="catalog-number">
            {String(paper.id).padStart(3, "0")}
          </span>
          <Link
            href={
              reviewSet === "1"
                ? `/papers/${paper.id}`
                : `/papers/${paper.id}?rev=${reviewSet}`
            }
          >
            {paper.title || "Untitled paper"}
          </Link>
        </div>
      ))}

      {papers?.length === 0 && (
        <p className="json-box-empty">No paper found with ID "{id}".</p>
      )}

      <Suspense>
        <Pagination currentPage={currentPage} totalPages={totalPages} />
      </Suspense>
    </main>
  );
}