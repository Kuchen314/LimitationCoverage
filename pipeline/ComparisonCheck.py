import os
import json
import re
from supabase import create_client
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def get_total(comparison, review_idx=1):
    """Extract the total (the denominator, e.g. the 3 in "2/3") from the
    "Review N Coverage" string of one comparison. Returns None if missing."""
    if isinstance(comparison, str):
        try:
            comparison = json.loads(comparison)
        except json.JSONDecodeError:
            return None
    if not isinstance(comparison, dict):
        return None
    coverage = comparison.get(f"Review {review_idx} Coverage", "")
    m = re.search(r"\d+/(\d+)", str(coverage))
    return int(m.group(1)) if m else None


def fetch_rows():
    response = (
        supabase.table("paper")
        .select("id, comparison, comparison2")
        .execute()
    )
    return response.data


def main():
    rows = fetch_rows()
    table = []
    mismatches = 0
    checked = 0

    for row in rows:
        paper_id = row["id"]
        # total according to each comparison column (taken from Review 1
        # Coverage; the R2 total is also checked for internal consistency)
        totals = {}
        for col in ("comparison", "comparison2"):
            t_r1 = get_total(row.get(col), 1)
            t_r2 = get_total(row.get(col), 2)
            # if R1 and R2 disagree within the same comparison, flag it as-is
            totals[col] = (t_r1, t_r2)

        t1_r1, t1_r2 = totals["comparison"]
        t2_r1, t2_r2 = totals["comparison2"]

        # skip papers where the totals aren't available on both sides —
        # without both comparisons there is nothing to compare
        vals = [t1_r1, t1_r2, t2_r1, t2_r2]
        if any(v is None for v in vals):
            continue

        checked += 1
        if len(set(vals)) == 1:
            identical = "Yes"
        else:
            identical = "NO"
            mismatches += 1

        table.append([paper_id, t1_r1, t1_r2, t2_r1, t2_r2, identical])

    headers = ["Paper ID", "comp R1 total", "comp R2 total", "comp2 R1 total", "comp2 R2 total", "Identical"]
    print(tabulate(table, headers=headers, tablefmt="rounded_outline",
                   colalign=["left"] + ["center"] * 5))
    print(f"\n{checked} papers checked, {mismatches} with mismatching totals "
          f"({checked - mismatches} identical).")


if __name__ == "__main__":
    main()