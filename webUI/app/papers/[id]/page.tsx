import { createClient } from "@/utils/supabase/server";
import JsonBox from "@/app/components/JsonBox";
import PaperJsonView from "@/app/components/PaperJsonView";
import ReviewView from "@/app/components/ReviewView";
import LimitationsView from  "@/app/components/LimitationsView";
import ComparisonView from "@/app/components/ComparisonView";
import EditWrapper from "@/app/components/EditWrapper";
import PlainTextView from "@/app/components/PlainTextView"
import PaperIgnoreToggle from "@/app/components/PaperIgnoreToggle";


export default async function PaperPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ rev?: string }>;
}) {
  const { id } = await params;
  const { rev = "1" } = await searchParams;

  // Review set 1 uses the plain "review"/"review_edited"/"comparison" columns,
  // sets 2 and 3 use the suffixed ones ("review2", "comparison2", ...)
  const suffix = rev === "2" || rev === "3" ? rev : "";
  const reviewCol = `review${suffix}`;
  const reviewEditedCol = `review_edited${suffix}`;
  const comparisonCol = `comparison${suffix}`;
  const reviewLabel = suffix ? `Review ${suffix}` : "Review";
  const comparisonLabel = suffix ? `Comparison ${suffix}` : "Comparison";

  const supabase = await createClient();

 const { data, error: paperError } = await supabase
  .from("paper")
  .select(`id, title, json, json_edited, ${reviewCol}, ${reviewEditedCol}, ${comparisonCol}, limitations, ignore`)
  .eq("id", id)
  .single();

  // The dynamic column names defeat Supabase's compile-time query parser,
  // so type the row manually
  const paper = data as Record<string, any> | null;

  if (paperError || !paper) {
    return <p>Error loading paper: {paperError?.message ?? "Paper not found."}</p>;
  }

  return (
    <main
      style={{
        padding: "2rem",
        maxWidth: "1500px",
        margin: "0 auto",
        textAlign: "center",
      }}
    >
      <h1>{paper.title}</h1>
      <PaperIgnoreToggle id={paper.id} ignore={!!paper.ignore} />
<div className="json-row">
  <EditWrapper table="paper" column="json" rowId={paper.id} value={paper.json} mode="raw">
    <PaperJsonView label="Raw Paper" data={paper.json} emptyMessage="No raw data yet." />
  </EditWrapper>
  <EditWrapper
    table="paper"
    column="json_edited"
    rowId={paper.id}
    value={paper.json_edited}
    mode={typeof paper.json_edited === "string" ? "plain" : "raw"}
  >
    {typeof paper.json_edited === "string" ? (
      <PlainTextView label="Edited Paper" text={paper.json_edited} emptyMessage="No edited data yet." />
    ) : (
      <PaperJsonView label="Edited Paper" data={paper.json_edited} emptyMessage="No edited data yet." />
    )}
  </EditWrapper>
</div>

<div className="json-row">
  <EditWrapper table="paper" column={reviewCol} rowId={paper.id} value={paper[reviewCol]} mode="review">
    <ReviewView label={reviewLabel} data={paper[reviewCol]} emptyMessage="No review data yet." />
  </EditWrapper>
  <EditWrapper table="paper" column={reviewEditedCol} rowId={paper.id} value={paper[reviewEditedCol]} mode="review">
    <ReviewView label={`${reviewLabel} Edited`} data={paper[reviewEditedCol]} emptyMessage="No edited review yet." />
  </EditWrapper>
</div>

<div className="json-row">
  <EditWrapper table="paper" column={comparisonCol} rowId={paper.id} value={paper[comparisonCol]} mode="raw">
    <ComparisonView label={comparisonLabel} data={paper[comparisonCol]} emptyMessage="No comparison yet." />
  </EditWrapper>
  <EditWrapper table="paper" column="limitations" rowId={paper.id} value={paper.limitations} mode="limitations">
    <LimitationsView label="Limitations" data={paper.limitations} emptyMessage="No limitations yet." />
  </EditWrapper>
</div>
    </main>

  );
}