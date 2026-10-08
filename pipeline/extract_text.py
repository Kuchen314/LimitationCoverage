"""
Extract the text layer from a PDF, truncate references/appendix, and save as JSON.

Requirements:
    pip install pymupdf

Usage:
    python extract_text.py paper.pdf
    python extract_text.py paper.pdf output.json
"""

import sys
import json
import re
from pathlib import Path
import fitz  # PyMuPDF


# Headings that typically mark the end of the "main content" we care about.
# Matched case-insensitively, must appear on their own line (common in papers).
CUTOFF_HEADINGS = [
    "references",
    "bibliography",
    "appendix",
    "supplementary material",
    "acknowledgements",
    "acknowledgments",
]


def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages = [page.get_text("text") for page in doc]
    return "\n".join(pages)


def truncate_after_references(text: str) -> str:
    """
    Cut the text at the first occurrence of a 'References'-like heading
    (or appendix/acknowledgements), discarding everything after it.
    """
    pattern = re.compile(
        r"^\s*(" + "|".join(CUTOFF_HEADINGS) + r")\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    if match:
        return text[: match.start()].rstrip()
    return text  # no heading found, return as-is


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py <input.pdf> [output.json]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else str(Path(pdf_path).with_suffix(".json"))

    full_text = extract_text(pdf_path)
    main_text = truncate_after_references(full_text)

    data = {"filename": pdf_path, "text": main_text}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved JSON to {out_path}")
    print(f"Original length: {len(full_text)} chars -> Truncated length: {len(main_text)} chars")