"use server";

import { createClient } from "@/utils/supabase/server";
import { revalidatePath } from "next/cache";

// Whitelist of which table/column combinations may be edited.
// Prevents the client from updating arbitrary tables/columns.
const ALLOWED: Record<string, string[]> = {
  paper: [
    "json",
    "json_edited",
    "review",
    "review_edited",
    "review2",
    "review_edited2",
    "review3",
    "review_edited3",
    "comparison",
    "comparison2",
    "comparison3",
    "limitations",
  ],
};

export async function saveField(
  table: string,
  column: string,
  id: number | string,
  rawText: string
) {
  if (!ALLOWED[table]?.includes(column)) {
    return { success: false, message: "This field is not editable." };
  }

  const supabase = await createClient();

  // Try to save as parsed JSON first (correct for json/jsonb columns).
  // If the column is plain text or the parse/update fails, fall back to the raw string.
  let value: unknown = rawText;
  try {
    value = JSON.parse(rawText);
  } catch {
    // Not valid JSON — keep as plain string
  }

  let { error } = await supabase.from(table).update({ [column]: value }).eq("id", id);

  if (error && value !== rawText) {
    // Retry with the raw string (covers text-typed columns)
    ({ error } = await supabase.from(table).update({ [column]: rawText }).eq("id", id));
  }

  if (error) {
    return { success: false, message: error.message };
  }

  revalidatePath("/papers/[id]", "page");
  return { success: true, message: "Saved." };
}

export async function setIgnore(id: number | string, ignore: boolean) {
  const supabase = await createClient();

  const { error } = await supabase.from("paper").update({ ignore }).eq("id", id);

  if (error) {
    return { success: false, message: error.message };
  }

  revalidatePath("/", "page");
  revalidatePath("/papers/[id]", "page");
  return { success: true, message: ignore ? "Paper ignored." : "Paper restored." };
}