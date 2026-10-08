import requests
import os
import json
from supabase import create_client
from dotenv import load_dotenv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

load_dotenv()

modelenv = os.getenv("MODEL_NAME")


def call_llm(prompt, model= modelenv):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    return response.json()["choices"][0]["message"]["content"]


def call_llm_json(prompt, json_data=None, model=modelenv):
    content = prompt + (
        "\n\nRespond with ONLY a single valid JSON object, no markdown formatting, "
        "no explanation, no surrounding text. The object must have exactly this shape:\n"
        '{"result_a": {...}, "result_b": {...}}'
    )
    if json_data is not None:
        content += f"\n\nInput data: {json.dumps(json_data, separators=(',', ':'))}"

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 200000,
        },
        timeout=360,
    )
    body = response.json()

    # goes wrong (bad model name, rate limit, no credits, etc). Surface that
    # message clearly instead of letting a bare KeyError hide the real cause.
    if "choices" not in body:
        raise RuntimeError(f"OpenRouter error (status {response.status_code}): {body}")

    raw = body["choices"][0]["message"]["content"].strip()

    # strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # surface what the model actually sent instead of a bare parse error
        finish = body["choices"][0].get("finish_reason")
        snippet = raw[:300] if raw else "<empty response>"
        raise RuntimeError(
            f"Model did not return valid JSON (finish_reason={finish}): {snippet}"
        ) from e

def save_json(data, filepath):
    # makes sure the parent folder (e.g. "limitations/") exists before writing
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def update_supabase_json_edited(paper_id, result_b):
    # updates the existing row where id matches, setting json_edited to result_b
    response = (
        supabase.table("paper")
        .update({"json_edited": result_b})
        .eq("id", paper_id)
        .execute()
    )
    return response

def update_supabase_limitations(paper_id, result_a):
    # updates the existing row where id matches, setting json_edited to result_b
    response = (
        supabase.table("paper")
        .update({"limitations": result_a})
        .eq("id", paper_id)
        .execute()
    )
    return response
def call_llm_single(prompt, json_data=None, model=modelenv):
    content = prompt + (
        "\n\nRespond with ONLY a single valid JSON object, no markdown formatting, "
        "no explanation, no surrounding text."
    )
    if json_data is not None:
        content += f"\n\nInput data: {json.dumps(json_data, separators=(',', ':'))}"

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 200000,
        },
        timeout=120,
    )
    body = response.json()

    if "choices" not in body:
        raise RuntimeError(f"OpenRouter error (status {response.status_code}): {body}")

    raw = body["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # surface what the model actually sent instead of a bare parse error
        finish = body["choices"][0].get("finish_reason")
        snippet = raw[:300] if raw else "<empty response>"
        raise RuntimeError(
            f"Model did not return valid JSON (finish_reason={finish}): {snippet}"
        ) from e


def get_paper_json(paper_id):
    # fetches the 'json' column for the row matching this id
    print("fetching paper json")
    response = (
        supabase.table("paper")
        .select("json")
        .eq("id", paper_id)
        .single()  # expects exactly one matching row, raises if 0 or 2+
        .execute()
    )
    print("paper fetched successfully")
    return response.data["json"]


def process_paper(paper_id, prompt, second_prompt):
    # pull the paper's JSON straight from Supabase instead of receiving it as an argument
    json_data = get_paper_json(paper_id)
    print("paper fetched")
    parsed = call_llm_json(prompt, json_data)

    if "result_a" not in parsed or "result_b" not in parsed:
        raise RuntimeError(
            f"LLM response missing expected keys 'result_a'/'result_b'. Got: {list(parsed.keys())}"
        )

    result_a, result_b = parsed["result_a"], parsed["result_b"]

    save_json(result_a, f"limitations/{paper_id}.json")

    result_b_refined = call_llm_single(second_prompt, json_data=result_b)

    save_json(result_b_refined, f"edited/{paper_id}.json")
    update_supabase_json_edited(paper_id, result_b_refined)

    return result_a, result_b_refined

def get_unprocessed_paper_ids():
    # fetches all ids where json_edited is empty (NULL) — adjust if "empty" means "" instead of NULL
    response = (
        supabase.table("paper")
        .select("id")
        .is_("json_edited", "null")
        .execute()
    )
    return [row["id"] for row in response.data]


def process_all_papers(prompt, second_prompt, limit=None):
    print(f"Starting now.")
    paper_ids = get_unprocessed_paper_ids()

    processed_count = 0

    for paper_id in paper_ids:
        # stop once we've hit the limit, if one was given
        if limit is not None and processed_count >= limit:
            print(f"Reached limit of {limit} papers, stopping.")
            break

        print(f"Processing paper {paper_id}...")

        try:
            result_a, result_b_refined = process_paper(paper_id, prompt, second_prompt)
        except Exception as e:
            # one bad paper shouldn't kill the whole batch
            print(f"Failed to process paper {paper_id}: {e}")
            continue

        processed_count += 1

    print(f"Done. Processed {processed_count} paper(s).")


def process_all_papers_new(prompt, limit=None):
    start_time = time.time()
    print(f"Starting now.")
    paper_ids = get_unprocessed_paper_ids()

    processed_count = 0

    for paper_id in paper_ids:
        # stop once we've hit the limit, if one was given
        if limit is not None and processed_count >= limit:
            print(f"Reached limit of {limit} papers, stopping.")
            break

        print(f"Processing paper {paper_id}...")

        try:
            json_data = get_paper_json(paper_id)
            parsed = call_llm_json(prompt, json_data)

            if "result_a" not in parsed or "result_b" not in parsed:
                raise RuntimeError(
                    f"LLM response missing expected keys 'result_a'/'result_b'. Got: {list(parsed.keys())}"
                )

            result_a, result_b = parsed["result_a"], parsed["result_b"]

            save_json(result_a, f"limitations/{paper_id}.json")
            save_json(result_b, f"edited/{paper_id}.json")
            update_supabase_json_edited(paper_id, result_b)
            update_supabase_limitations(paper_id, result_a)
            elapsed = time.time() - start_time
            print(f"Done. Processed {processed_count} paper(s) in {elapsed:.2f} seconds.")
        except Exception as e:
            # one bad paper shouldn't kill the whole batch
            print(f"Failed to process paper {paper_id}: {e}")
            continue

        processed_count += 1

    print(f"Done. Processed {processed_count} paper(s).")


def _process_one_paper_new(paper_id, prompt):
    # per-paper work for the parallel version: fetch, call LLM, save, update supabase
    json_data = get_paper_json(paper_id)
    parsed = call_llm_json(prompt, json_data)

    if "result_a" not in parsed or "result_b" not in parsed:
        raise RuntimeError(
            f"LLM response missing expected keys 'result_a'/'result_b'. Got: {list(parsed.keys())}"
        )

    result_a, result_b = parsed["result_a"], parsed["result_b"]

    save_json(result_a, f"limitations/{paper_id}.json")
    save_json(result_b, f"edited/{paper_id}.json")
    update_supabase_json_edited(paper_id, result_b)
    update_supabase_limitations(paper_id, result_a)


def process_all_papers_new_parallel(prompt, limit=None, max_workers=4):
    start_time = time.time()
    print(f"Starting now.")
    paper_ids = get_unprocessed_paper_ids()

    # unlike the sequential version, failed papers count toward the limit here,
    # since all papers are submitted up front
    if limit is not None:
        paper_ids = paper_ids[:limit]

    print(f"Processing {len(paper_ids)} paper(s) with {max_workers} worker(s)...")

    processed_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process_one_paper_new, paper_id, prompt): paper_id
            for paper_id in paper_ids
        }

        for future in as_completed(futures):
            paper_id = futures[future]
            try:
                future.result()
            except Exception as e:
                # one bad paper shouldn't kill the whole batch
                failed_count += 1
                print(f"Failed to process paper {paper_id}: {e}")
                continue

            processed_count += 1
            elapsed = time.time() - start_time
            print(f"Finished paper {paper_id}. Processed {processed_count} paper(s) in {elapsed:.2f} seconds.")

    elapsed = time.time() - start_time
    print(f"Done. Processed {processed_count} paper(s), {failed_count} failed, in {elapsed:.2f} seconds.")


def get_paper_json_edited(paper_id):
    # fetches the 'json_edited' column for the row matching this id
    print("fetching paper json_edited")
    response = (
        supabase.table("paper")
        .select("json_edited")
        .eq("id", paper_id)
        .single()
        .execute()
    )
    print("paper json_edited fetched successfully")
    return response.data["json_edited"]


def insert_review(paper_id, result, column="review"):
    # updates the paper row, storing the review in the given column
    response = (
        supabase.table("paper")
        .update({column: result})
        .eq("id", paper_id)
        .execute()
    )
    return response


def insert_review_edited(paper_id, result, column="review_edited"):
    # updates the paper row, storing the review in the given column
    response = (
        supabase.table("paper")
        .update({column: result})
        .eq("id", paper_id)
        .execute()
    )
    return response


def get_unreviewed_paper_ids(review_col="review", edited_col="review_edited"):
    # papers with json and json_edited populated but the given review columns still empty
    print(f"Fetching paper ids without {review_col}/{edited_col}...")
    response = (
        supabase.table("paper")
        .select("id")
        .not_.is_("json", "null")
        .not_.is_("json_edited", "null")
        .is_(review_col, "null")
        .is_(edited_col, "null")
        .execute()
    )
    unreviewed = [row["id"] for row in response.data]
    print(f"{len(unreviewed)} paper(s) still need {review_col} + {edited_col}.")
    return unreviewed

def create_review(paper_id, prompt, column="review"):
    json_data = get_paper_json(paper_id)
    result = call_llm_single(prompt, json_data=json_data)
    save_json(result, f"{column}/{paper_id}.json")
    insert_review(paper_id, result, column=column)
    return result


def create_review_edited(paper_id, prompt, column="review_edited"):
    json_data = get_paper_json_edited(paper_id)
    result = call_llm_single(prompt, json_data=json_data)
    save_json(result, f"{column}/{paper_id}.json")
    insert_review_edited(paper_id, result, column=column)
    return result

def process_all_reviews(review_prompt, review_edited_prompt, limit):
    print("Starting review processing...")
    start_time = time.time()

    paper_ids = get_unreviewed_paper_ids()

    processed_count = 0

    for paper_id in paper_ids:
        if processed_count >= limit:
            print(f"Reached limit of {limit} paper(s), stopping.")
            break

        print(f"Processing paper {paper_id}...")

        try:
            print(f"  Creating review for paper {paper_id}...")
            create_review(paper_id, review_prompt)
            print(f"  Review created for paper {paper_id}.")

            print(f"  Creating review_edited for paper {paper_id}...")
            create_review_edited(paper_id, review_edited_prompt)
            print(f"  Review_edited created for paper {paper_id}.")
        except Exception as e:
            print(f"Failed to process paper {paper_id}: {e}")
            continue

        processed_count += 1
        print(f"Finished paper {paper_id} ({processed_count}/{limit}).")
        elapsed = time.time() - start_time
        print(f"Processed {processed_count} paper(s) in {elapsed:.2f} seconds.")


def process_one_review(paper_id, review_prompt, review_col="review", edited_col="review_edited"):
    # per-paper work for the parallel version: create review, then review_edited
    # (the two stay sequential within a paper; papers run in parallel)
    print(f"  Creating {review_col} for paper {paper_id}...")
    create_review(paper_id, review_prompt, column=review_col)
    print(f"  {review_col} created for paper {paper_id}.")

    print(f"  Creating {edited_col} for paper {paper_id}...")
    create_review_edited(paper_id, review_prompt, column=edited_col)
    print(f"  {edited_col} created for paper {paper_id}.")


def process_all_reviews_parallel(review_prompt, limit=None, max_workers=4,
                                 review_col="review", edited_col="review_edited"):
    print("Starting review processing...")
    start_time = time.time()

    paper_ids = get_unreviewed_paper_ids(review_col=review_col, edited_col=edited_col)

    # failed papers count toward the limit, since all papers are submitted up front
    if limit is not None:
        paper_ids = paper_ids[:limit]

    print(f"Processing {len(paper_ids)} paper(s) with {max_workers} worker(s)...")

    processed_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_one_review, paper_id, review_prompt, review_col, edited_col): paper_id
            for paper_id in paper_ids
        }

        for future in as_completed(futures):
            paper_id = futures[future]
            try:
                future.result()
            except Exception as e:
                # one bad paper shouldn't kill the whole batch
                failed_count += 1
                print(f"Failed to process paper {paper_id}: {e}")
                continue

            processed_count += 1
            elapsed = time.time() - start_time
            print(f"Finished paper {paper_id}. Processed {processed_count} paper(s) in {elapsed:.2f} seconds.")

    elapsed = time.time() - start_time
    print(f"Done. Processed {processed_count} paper(s), {failed_count} failed, in {elapsed:.2f} seconds.")


def process_all_reviews_parallel2(review_prompt, limit=None, max_workers=4):
    # same pipeline, but writes to the review2 / review_edited2 columns
    process_all_reviews_parallel(
        review_prompt,
        limit=limit,
        max_workers=max_workers,
        review_col="review2",
        edited_col="review_edited2",
    )

def get_comparable_paper_ids(review_col="review", edited_col="review_edited", comparison_col="comparison"):
    # fetches all rows where the review columns and limitations are all non-null
    # but the comparison column is still empty
    response = (
        supabase.table("paper")
        .select("id")
        .not_.is_(review_col, "null")
        .not_.is_(edited_col, "null")
        .not_.is_("limitations", "null")
        .is_(comparison_col, "null")
        .execute()
    )
    return [row["id"] for row in response.data]


def create_comparison(paper_id, prompt, review_col="review", edited_col="review_edited",
                      comparison_col="comparison"):
    # fetch the three fields needed for comparison from this row
    response = (
        supabase.table("paper")
        .select(f"{review_col}, {edited_col}, limitations")
        .eq("id", paper_id)
        .single()
        .execute()
    )
    row = response.data

    # pack all three into the input data so the model sees them together
    # (keys stay 'review'/'review_edited' regardless of source columns,
    # so the prompt sees the same shape in both versions)
    input_data = {
        "review": row[review_col],
        "review_edited": row[edited_col],
        "limitations": row["limitations"],
    }

    result = call_llm_single(prompt, json_data=input_data)

    # save the comparison result back to the DB under the given column
    supabase.table("paper").update({comparison_col: result}).eq("id", paper_id).execute()

    return result


def create_all_comparisons(prompt, limit=None, max_workers=4,
                           review_col="review", edited_col="review_edited",
                           comparison_col="comparison"):
    print("Starting comparisons.")
    paper_ids = get_comparable_paper_ids(review_col, edited_col, comparison_col)

    if limit is not None:
        paper_ids = paper_ids[:limit]  # slice upfront so the thread pool doesn't even start extra work

    processed_count = 0
    failed_count = 0

    # ThreadPoolExecutor runs multiple create_comparison calls in parallel,
    # max_workers controls how many run at the same time.
    # as_completed() yields each future as it finishes (not in submission order),
    # so results are processed as soon as they're ready rather than waiting for all.
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(create_comparison, paper_id, prompt, review_col, edited_col, comparison_col): paper_id
            for paper_id in paper_ids
        }

        for future in as_completed(futures):
            paper_id = futures[future]
            try:
                future.result()
                processed_count += 1
                print(f"Done: paper {paper_id} ({processed_count}/{len(paper_ids)})")
            except Exception as e:
                failed_count += 1
                print(f"Failed: paper {paper_id}: {e}")

    print(f"Finished. {processed_count} succeeded, {failed_count} failed.")


def create_all_comparisons2(prompt, limit=None, max_workers=4):
    # same pipeline, but compares review2/review_edited2 and writes to comparison2
    create_all_comparisons(
        prompt,
        limit=limit,
        max_workers=max_workers,
        review_col="review2",
        edited_col="review_edited2",
        comparison_col="comparison2",
    )

def create_all_comparisons3(prompt, limit=None, max_workers=4):
    # same pipeline, but compares review2/review_edited2 and writes to comparison2
    create_all_comparisons(
        prompt,
        limit=limit,
        max_workers=max_workers,
        review_col="review3",
        edited_col="review_edited3",
        comparison_col="comparison3",
    )

if __name__ == "__main__":
    #prompt = os.getenv("EDIT_PROMPT")
    #process_all_papers_new_parallel(prompt,100,25)

    rompt = os.getenv('REVIEW_PROMPT')
    process_all_reviews_parallel(rompt,10,10    ,"review3","review_edited3")
    comparison = os.getenv('COMPARISON_PROMPT')
    create_all_comparisons3(comparison,30,10)
    #create_all_comparisons2(comparison,100,10)

