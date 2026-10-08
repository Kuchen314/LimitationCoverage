import json
from pathlib import Path
from typing import Any
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

def load_papers_from_folder(folder_path: str) -> list[dict[str, Any]]:
    """Read every .json file in a folder and map it to paper table columns."""
    records = []
    for filepath in Path(folder_path).glob("*.json"):
        with open(filepath, "r") as f:
            data = json.load(f)

        metadata = data.get("metadata", {})

        record = {
            "title": metadata.get("title"),          # often null in this dataset
            "abstract": metadata.get("abstractText"),
            "json": data,                              # whole file goes into the json column
        }
        records.append(record)

    return records


def seed_papers_from_folder(folder_path: str, batch_size: int = 10) -> None:
    """Load all JSON files in a folder and insert them into the paper table."""
    records = load_papers_from_folder(folder_path)

    if not records:
        print("No JSON files found.")
        return

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        response = supabase.table("paper").insert(batch).execute()
        print(f"Inserted rows {i} to {i + len(batch)}")


seed_papers_from_folder("iclr_2017/train/parsed_pdfs",3)