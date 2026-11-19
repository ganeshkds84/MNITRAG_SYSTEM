"""
Evaluate the RAG pipeline on the question set in eval/questions.json.

For every question it reports:
  - hit@k:       expected file is among the TOP_K_RESULTS chunks sent to the LLM
  - page hit@k:  expected file AND page are among those chunks
                 (an optional "alternative_sources" list of {file, page} gives
                 other sources that answer the question equally well)
  - rank:        position of the first chunk from the expected file
  - correctness: keyword/number match of the answer against answer_keywords,
                 averaged over --runs LLM calls (answers vary between runs).
                 Out-of-scope questions are correct only for the exact
                 fallback sentence.

LLM answers are cached in eval/cache/ (keyed on model, prompt, question and
retrieved context), so an interrupted run (e.g. Groq daily token limit)
resumes where it stopped.

Usage:
    python -m utils.eval_questions                       # config defaults
    python -m utils.eval_questions --retrieval vector --headers off
    python -m utils.eval_questions --ids q01,q09 --runs 1
    python -m utils.eval_questions --no-llm              # retrieval only
    python -m utils.eval_questions --ablation --output eval/ablation_phase5.md

Headers on/off selects the vector store:
    on  -> VECTOR_DB_DIRECTORY             (python -m rag.ingest)
    off -> VECTOR_DB_DIRECTORY + "_noheaders"
           (python -m rag.ingest --headers off --db-dir vector_store_noheaders)
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime

from config.config import (
    LLM_MODEL,
    TOP_K_RESULTS,
    USE_CHUNK_HEADERS,
    USE_HYBRID_RETRIEVAL,
    VECTOR_DB_DIRECTORY,
)
from rag.metadata import page_number
from rag.pipeline import generate_answer, retrieve_documents
from rag.prompt_builder import FALLBACK_ANSWER, RAG_PROMPT_TEMPLATE, format_context
from rag.vectordb import get_vector_store

QUESTIONS_FILE = "eval/questions.json"
CACHE_DIR = "eval/cache"
NOHEADERS_SUFFIX = "_noheaders"

MAX_RATE_LIMIT_RETRIES = 20


class DailyLimitReached(Exception):
    """Raised when the LLM provider's daily quota is exhausted."""


# ---------------------------------------------------------------------------
# Answer scoring
# ---------------------------------------------------------------------------

def normalize_answer(text: str) -> str:
    """
    Lowercase, drop thousands separators (35,000 -> 35000), unify the
    multiplication sign and whitespace, so keyword matching is robust.
    """
    text = text.lower()
    text = re.sub(r"(?<=\d)[,  ](?=\d{3})", "", text)
    text = re.sub(r"[×✕*]", " x ", text)
    text = text.replace("‑", "-").replace("‐", "-")

    return re.sub(r"\s+", " ", text)


def keyword_matches(keyword: str, text: str) -> bool:
    """
    A keyword is a plain substring, or a regex when prefixed with "re:".
    """
    if keyword.startswith("re:"):
        return re.search(keyword[3:], text) is not None

    return normalize_answer(keyword) in text


def is_fallback(answer: str) -> bool:
    return answer.strip().strip("\"'").strip() == FALLBACK_ANSWER


def score_answer(item: dict, answer: str) -> bool:
    """
    Out-of-scope: correct only for the exact fallback sentence.
    In-scope: every keyword group must match (a group is a keyword or a
    list of alternative keywords), and the answer must not be the fallback.
    """
    if item["expected_file"] is None:
        return is_fallback(answer)

    if is_fallback(answer):
        return False

    text = normalize_answer(answer)

    for group in item["answer_keywords"]:
        alternatives = group if isinstance(group, list) else [group]
        if not any(keyword_matches(k, text) for k in alternatives):
            return False

    return True


# ---------------------------------------------------------------------------
# LLM calls with cache and rate-limit handling
# ---------------------------------------------------------------------------

def cache_key(question: str, context: str, run: int) -> str:
    raw = "\n".join([LLM_MODEL, RAG_PROMPT_TEMPLATE, question, context, str(run)])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_cache(path: str) -> dict:
    cache = {}

    if os.path.exists(path):
        with open(path, encoding="utf-8") as file:
            for line in file:
                entry = json.loads(line)
                cache[entry["key"]] = entry

    return cache


def retry_delay(message: str) -> float:
    """
    Parse "Please try again in 1m2.5s" / "in 12.3s" / "in 450ms".
    """
    match = re.search(r"try again in (?:(\d+)m)?([\d.]+)(ms|s)", message)

    if not match:
        return 20.0

    minutes = float(match.group(1) or 0)
    value = float(match.group(2))
    seconds = value / 1000 if match.group(3) == "ms" else value

    return minutes * 60 + seconds + 1.0


def answer_with_retry(question: str, documents) -> str:
    """
    Call the LLM, waiting on per-minute rate limits and stopping on daily limits.
    """
    for _ in range(MAX_RATE_LIMIT_RETRIES):
        try:
            return generate_answer(question, documents).answer.strip()
        except Exception as error:
            message = str(error)
            lowered = message.lower()

            if "rate limit" not in lowered and "429" not in message:
                raise

            if "per day" in lowered or "(tpd)" in lowered or "(rpd)" in lowered:
                raise DailyLimitReached(message) from error

            delay = retry_delay(message)
            print(f"    rate limited, waiting {delay:.0f}s ...", file=sys.__stdout__)
            time.sleep(delay)

    raise RuntimeError("Too many rate-limit retries")


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def store_directory(headers: bool) -> str:
    return VECTOR_DB_DIRECTORY if headers else VECTOR_DB_DIRECTORY + NOHEADERS_SUFFIX


def check_store(directory: str, headers: bool):
    """
    Make sure the store exists and was built with/without chunk headers.
    """
    data = get_vector_store(directory).get(limit=1, include=["metadatas"])

    if not data["metadatas"]:
        flag = "on" if headers else "off"
        sys.exit(
            f"Vector store '{directory}' is empty. Build it with:\n"
            f"  python -m rag.ingest --headers {flag} --db-dir {directory}"
        )

    has_headers = "chunk_header" in data["metadatas"][0]

    if has_headers != headers:
        sys.exit(
            f"Vector store '{directory}' was built with headers "
            f"{'on' if has_headers else 'off'}, expected {'on' if headers else 'off'}."
        )


def evaluate_config(
    items, hybrid: bool, headers: bool, runs: int, use_llm: bool,
    cached_only: bool = False,
):
    """
    Evaluate one configuration. Returns a list of per-question result dicts.
    With cached_only, only answers already in eval/cache/ are scored
    (no new LLM calls).
    """
    name = f"{'hybrid' if hybrid else 'vector'}_headers-{'on' if headers else 'off'}"
    directory = store_directory(headers)
    check_store(directory, headers)

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{name}.jsonl")
    cache = load_cache(cache_path)

    print(f"\n### Config: {name} (store: {directory}, k={TOP_K_RESULTS}, runs={runs})")
    results = []
    daily_limit = None

    with open(cache_path, "a", encoding="utf-8") as cache_file:
        for item in items:
            documents = retrieve_documents(
                item["question"],
                k=TOP_K_RESULTS,
                hybrid=hybrid,
                persist_directory=directory,
            )

            # The expected source plus any equally valid alternative sources
            valid_sources = [
                (item["expected_file"], item["expected_page"])
            ] + [
                (source["file"], source.get("page"))
                for source in item.get("alternative_sources", [])
            ]

            rank, page_hit = None, False
            for position, doc in enumerate(documents, 1):
                for file_name, page in valid_sources:
                    if doc.metadata.get("file_name") == file_name:
                        rank = rank or position
                        if str(page_number(doc.metadata)) == str(page):
                            page_hit = True

            context = format_context(documents)
            answers = []

            for run in range(runs if use_llm else 0):
                key = cache_key(item["question"], context, run)

                if key not in cache:
                    if daily_limit or cached_only:
                        break
                    try:
                        answer = answer_with_retry(item["question"], documents)
                    except DailyLimitReached as error:
                        daily_limit = str(error)
                        print(f"  !! Daily LLM limit reached, stopping LLM calls:\n     {daily_limit[:300]}")
                        break

                    cache[key] = {"key": key, "id": item["id"], "run": run, "answer": answer}
                    cache_file.write(json.dumps(cache[key], ensure_ascii=False) + "\n")
                    cache_file.flush()

                answers.append(cache[key]["answer"])

            correct = [score_answer(item, a) for a in answers]

            result = {
                "item": item,
                "rank": rank,
                "hit": rank is not None,
                "page_hit": page_hit,
                "answers": answers,
                "correct": correct,
                "sources": sorted({
                    f"{d.metadata.get('file_name')} p{page_number(d.metadata)}"
                    for d in documents
                }),
            }
            results.append(result)

            in_scope = item["expected_file"] is not None
            acc = f"{sum(correct)}/{len(correct)}" if answers else "-"
            print(
                f"  {item['id']} {item['type']:<12} "
                f"hit={'Y' if result['hit'] else ('-' if not in_scope else 'N')} "
                f"page={'Y' if page_hit else ('-' if not in_scope else 'N')} "
                f"rank={rank or '-'} correct={acc}"
            )

    return name, results, daily_limit


def mean(values):
    return sum(values) / len(values) if values else None


def summarize(results) -> dict:
    """
    Aggregate metrics for one configuration.
    """
    in_scope = [r for r in results if r["item"]["expected_file"]]
    out_scope = [r for r in results if not r["item"]["expected_file"]]
    ocr = [r for r in in_scope if r["item"].get("ocr")]

    def accuracy(rows):
        per_question = [mean(r["correct"]) for r in rows if r["correct"]]
        return mean(per_question), len(per_question)

    return {
        "hit": mean([r["hit"] for r in in_scope]),
        "page_hit": mean([r["page_hit"] for r in in_scope]),
        "ocr_hit": mean([r["hit"] for r in ocr]),
        "acc": accuracy(in_scope),
        "ocr_acc": accuracy(ocr),
        "oos_acc": accuracy(out_scope),
        "all_acc": accuracy(results),
        "n_in": len(in_scope),
        "n_ocr": len(ocr),
        "n_oos": len(out_scope),
    }


def pct(value):
    return "-" if value is None else f"{value * 100:.0f}%"


def pct_n(pair, total):
    value, answered = pair
    if value is None:
        return "-"
    suffix = "" if answered == total else f" ({answered}/{total} q)"
    return f"{value * 100:.0f}%{suffix}"


def print_details(name, results):
    """
    Full answers and sources for one configuration.
    """
    print(f"\n{'=' * 80}\nDETAILS: {name}")

    for r in results:
        item = r["item"]
        print("=" * 80)
        print(f"{item['id']} [{item['type']}{', OCR' if item.get('ocr') else ''}] {item['question']}")
        print(f"Expected: {item['expected_file'] or '(fallback)'}"
              f"{' p' + str(item['expected_page']) if item['expected_page'] else ''}"
              f" | {item['expected_answer']}")
        print(f"Retrieval: hit={r['hit']} page_hit={r['page_hit']} rank={r['rank']}")
        print(f"Context: {', '.join(r['sources'])}")

        for run, (answer, ok) in enumerate(zip(r["answers"], r["correct"]), 1):
            print(f"--- run {run}: {'CORRECT' if ok else 'WRONG'}")
            print(answer)


def print_summary(name, results):
    s = summarize(results)
    print(f"\nSUMMARY {name}")
    print(f"  hit@{TOP_K_RESULTS}:            {pct(s['hit'])}  ({s['n_in']} in-scope questions)")
    print(f"  page hit@{TOP_K_RESULTS}:       {pct(s['page_hit'])}")
    print(f"  OCR hit@{TOP_K_RESULTS}:        {pct(s['ocr_hit'])}  ({s['n_ocr']} OCR questions)")
    print(f"  accuracy in-scope: {pct_n(s['acc'], s['n_in'])}")
    print(f"  accuracy OCR:      {pct_n(s['ocr_acc'], s['n_ocr'])}")
    print(f"  out-of-scope:      {pct_n(s['oos_acc'], s['n_oos'])}")
    print(f"  accuracy overall:  {pct_n(s['all_acc'], s['n_in'] + s['n_oos'])}")


def write_ablation_markdown(path, all_results, runs, use_llm, limits):
    """
    Save the four-configuration comparison as a Markdown table.
    """
    lines = [
        "# Retrieval ablation (Phase 5)",
        "",
        f"Run: {datetime.now():%Y-%m-%d %H:%M} | model: {LLM_MODEL} | "
        f"k={TOP_K_RESULTS} | LLM runs per question: {runs if use_llm else 0}",
        "",
        "Accuracy = keyword/number match against `answer_keywords` in "
        "`eval/questions.json`, averaged over runs. Out-of-scope = exact fallback sentence.",
        "",
        "| Retrieval | Chunk headers | hit@6 | page hit@6 | OCR hit@6 | "
        "accuracy (in-scope) | accuracy (OCR) | out-of-scope | accuracy (all) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for name, results in all_results:
        s = summarize(results)
        retrieval, headers = name.split("_headers-")
        lines.append(
            f"| {retrieval} | {headers} | {pct(s['hit'])} | {pct(s['page_hit'])} | "
            f"{pct(s['ocr_hit'])} | {pct_n(s['acc'], s['n_in'])} | "
            f"{pct_n(s['ocr_acc'], s['n_ocr'])} | {pct_n(s['oos_acc'], s['n_oos'])} | "
            f"{pct_n(s['all_acc'], s['n_in'] + s['n_oos'])} |"
        )

    names = [name for name, _ in all_results]
    lines += [
        "",
        "## Per-question results",
        "",
        "Each cell: retrieval (H = expected file in context, P = also expected page, "
        "- = missed) / correct answers out of runs.",
        "",
        "| id | type | OCR | " + " | ".join(names) + " |",
        "|---|---|---|" + "---|" * len(names),
    ]

    by_config = [{r["item"]["id"]: r for r in results} for _, results in all_results]

    for item_result in all_results[0][1]:
        item = item_result["item"]
        cells = []
        for config in by_config:
            r = config[item["id"]]
            if item["expected_file"]:
                retrieval = "P" if r["page_hit"] else ("H" if r["hit"] else "-")
            else:
                retrieval = "n/a"
            answers = f"{sum(r['correct'])}/{len(r['correct'])}" if r["correct"] else "-"
            cells.append(f"{retrieval} / {answers}")
        lines.append(
            f"| {item['id']} | {item['type']} | {'yes' if item.get('ocr') else ''} | "
            + " | ".join(cells) + " |"
        )

    if limits:
        lines += ["", "## Incomplete runs", ""]
        lines += [f"- {name}: not all LLM answers available (Groq daily token "
                  f"limit); re-run to resume, answers are cached." for name in limits]

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")

    print(f"\nSaved ablation table to {path}")


class Tee:
    """
    Write to several streams at once (console + output file).
    """
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--questions", default=QUESTIONS_FILE)
    parser.add_argument("--retrieval", choices=["vector", "hybrid"],
                        default="hybrid" if USE_HYBRID_RETRIEVAL else "vector")
    parser.add_argument("--headers", choices=["on", "off"],
                        default="on" if USE_CHUNK_HEADERS else "off")
    parser.add_argument("--runs", type=int, default=3, help="LLM runs per question")
    parser.add_argument("--ids", help="Comma-separated question ids, e.g. q01,q09")
    parser.add_argument("--no-llm", action="store_true", help="Retrieval metrics only")
    parser.add_argument("--cached-only", action="store_true",
                        help="Score cached answers only, make no new LLM calls")
    parser.add_argument("--ablation", action="store_true",
                        help="Run vector/hybrid x headers off/on")
    parser.add_argument("--output", help="Report file (.md for --ablation, else text)")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    with open(args.questions, encoding="utf-8") as file:
        items = json.load(file)

    if args.ids:
        wanted = args.ids.split(",")
        items = [item for item in items if item["id"] in wanted]

    use_llm = not args.no_llm

    if args.ablation:
        configs = [(h, hd) for hd in (False, True) for h in (False, True)]
    else:
        configs = [(args.retrieval == "hybrid", args.headers == "on")]

    log_file = None
    if args.output and not args.ablation:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        log_file = open(args.output, "w", encoding="utf-8")
        sys.stdout = Tee(sys.__stdout__, log_file)

    print(f"Eval run: {datetime.now():%Y-%m-%d %H:%M} | {len(items)} questions | "
          f"model {LLM_MODEL} | k={TOP_K_RESULTS}")

    all_results, limits = [], []

    for hybrid, headers in configs:
        name, results, daily_limit = evaluate_config(
            items, hybrid, headers, args.runs, use_llm, args.cached_only
        )
        if args.cached_only and any(len(r["answers"]) < args.runs for r in results):
            daily_limit = daily_limit or "cached-only: some answers missing"
        all_results.append((name, results))
        if daily_limit:
            limits.append(name)

    for name, results in all_results:
        if not args.ablation:
            print_details(name, results)
        print_summary(name, results)

    if args.ablation:
        write_ablation_markdown(
            args.output or "eval/ablation_phase5.md",
            all_results, args.runs, use_llm, limits,
        )

    if log_file:
        sys.stdout = sys.__stdout__
        log_file.close()


if __name__ == "__main__":
    main()
