import os
from supabase import create_client
from dotenv import load_dotenv
from pipeline.llm import call_llm_json

from typing import Any


load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)
edit_prompt = os.environ["SUPABASE_EDIT_PROMPT"]

# Insert a paper
response = supabase.table("paper").insert({
    "title": "Example Paper123",
    "abstract": "...",
    "pdf_link": "https://...",
    "json": {"some": "data"}
}).execute()

# Fetch all papers
response = supabase.table("paper").select("*").execute()
print(response.data)

# Fetch a paper with its review joined in (foreign key relationship)
response = supabase.table("paper").select("*, review(*)").execute()

# Update a paper's edited json
response = supabase.table("paper").update({
    "json_edited": {"corrected": "data"}
}).eq("id", 1).execute()


def create_edit(data: dict[str, Any]) -> dict[str, Any]:
    """Send the paper's json to the LLM and return the edited version."""
    edit = call_llm_json(edit_prompt, data)
    return edit


def write_edit(id: int) -> dict[str, Any]:
    """Fetch a paper's json, run it through create_edit, and save the result to json_edited."""
    response = supabase.table("paper").select("json").eq("id", id).execute()

    if not response.data:
        raise ValueError(f"No paper found with id {id}")

    original_json = response.data[0]["json"]
    edit = create_edit(original_json)

    response = (
        supabase.table("paper")
        .update({"json_edited": edit})
        .eq("id", id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(f"Update failed for paper id {id}")

    return response.data[0]

def get_unedited_ids() -> list[int]:
    """Get ids of papers that don't have json_edited filled in yet."""
    ids = []
    page_size = 1000
    offset = 0
    while True:
        response = (
            supabase.table("paper")
            .select("id")
            .is_("json_edited", "null")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        if not response.data:
            break
        ids.extend(row["id"] for row in response.data)
        offset += page_size
    return ids


def edit_all() -> None:
    """Run write_edit on every paper that hasn't been edited yet."""
    ids = get_unedited_ids()

    if not ids:
        print("No unedited papers found.")
        return

    for paper_id in ids:
        try:
            write_edit(paper_id)
            print(f"Edited paper {paper_id}")
        except Exception as e:
            print(f"Failed to edit paper {paper_id}: {e}")