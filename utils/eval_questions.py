"""
Run a fixed set of evaluation questions through the RAG pipeline and print
the answer, the sources, and the retrieval rank of the expected document.

Two ranks are reported for the expected document:
  - context rank: position among the TOP_K_RESULTS chunks actually sent
    to the LLM (blank if it was not sent)
  - deep rank: position in the retriever's results with k=RANK_DEPTH
With hybrid (BM25 + vector) retrieval the fused order depends on k, so
the deep rank is indicative only; "sent to LLM" is the ground truth.

Usage:
    python -m utils.eval_questions [--output eval/some_run.txt]
"""

import argparse
import sys
from datetime import datetime

from config.config import TOP_K_RESULTS
from rag.pipeline import ask_question
from rag.prompt_builder import FALLBACK_ANSWER
from rag.retriever import get_retriever

RANK_DEPTH = 50

# expected_doc is None when the question should get the fallback answer
EVAL_QUESTIONS = [
    {
        "question": "What is the M.Tech tuition fee?",
        "expected_doc": "FeePG2025-26.pdf",
        "expected_answer": "Rs 35,000 per semester (2025-26, general); "
                           "mentions older 2024-25 value",
    },
    {
        "question": "What is the CGPA to percentage conversion formula?",
        "expected_doc": "CGPAConversion Formula2016.pdf",
        "expected_answer": "% Marks = CGPA x 10 (2016 order, supersedes 2014)",
    },
    {
        "question": "What is the CGPA requirement for direct PhD admission "
                    "for B.Tech students?",
        "expected_doc": "Revision of CGPA req from 9 to 8 for direct admission "
                        "to PhD for BTechB.Arch qualified students.pdf",
        "expected_answer": "CGPA 8 (reduced from 9 by the 2021 order); "
                           "PG_Manual2024S may state a different scheme value",
    },
    {
        "question": "What is the internship duration for PG students?",
        "expected_doc": "InternshipGuidelinesUGPG.pdf",
        "expected_answer": "More than 6 months, up to one year; no duplicate sources",
    },
    {
        "question": "Who is the director of IIT Bombay?",
        "expected_doc": None,
        "expected_answer": FALLBACK_ANSWER,
    },
]


def retrieval_rank(question: str, expected_doc: str, k: int):
    """
    Return the 1-based rank of the first chunk from expected_doc
    when retrieving k chunks, or None if it is not among them.
    """
    retriever = get_retriever(k=k)
    documents = retriever.invoke(question)

    for rank, doc in enumerate(documents, 1):
        if doc.metadata.get("file_name") == expected_doc:
            return rank

    return None


def run_eval():
    """
    Run all evaluation questions and print a report.
    """
    print(f"Eval run: {datetime.now():%Y-%m-%d %H:%M} | TOP_K_RESULTS={TOP_K_RESULTS}")
    summary = []

    for i, item in enumerate(EVAL_QUESTIONS, 1):
        question = item["question"]
        expected_doc = item["expected_doc"]

        response = ask_question(question)
        answer = response.answer.strip()
        is_fallback = answer.strip("\"'").strip() == FALLBACK_ANSWER

        if expected_doc:
            ctx_rank = retrieval_rank(question, expected_doc, TOP_K_RESULTS)
            deep_rank = retrieval_rank(question, expected_doc, RANK_DEPTH)
            in_context = "yes" if any(
                source.get("file_name") == expected_doc
                for source in response.sources
            ) else "no"
            ctx_text = f"{ctx_rank}" if ctx_rank else "-"
            rank_text = f"{deep_rank}" if deep_rank else f">{RANK_DEPTH}"
        else:
            ctx_text, rank_text, in_context = "-", "-", "-"

        print("=" * 80)
        print(f"Q{i}: {question}")
        print(f"Expected doc:    {expected_doc or '(none, fallback expected)'}")
        print(f"Expected answer: {item['expected_answer']}")
        print(
            f"Retrieval rank:  context {ctx_text} / deep {rank_text} "
            f"(sent to LLM: {in_context})"
        )
        print("-" * 80)
        print(answer)
        print("-" * 80)
        print("Sources" + (" (hidden in app: exact fallback)" if is_fallback else "") + ":")

        for source in response.sources:
            print(
                f"  - {source['file_name']} | page {source['page_label']} | "
                f"{source['category']} | year {source['doc_year']}"
            )
        print()

        summary.append((i, expected_doc or "-", ctx_text, rank_text, in_context))

    print("=" * 80)
    print("SUMMARY")
    print(f"{'Q':<3} {'ctx':>4} {'deep':>5} {'to LLM':>7}  expected doc")
    for i, doc, ctx_text, rank_text, in_context in summary:
        print(f"Q{i:<2} {ctx_text:>4} {rank_text:>5} {in_context:>7}  {doc}")


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Also save the report to this file")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    if args.output:
        import os
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as file:
            sys.stdout = Tee(sys.__stdout__, file)
            run_eval()
            sys.stdout = sys.__stdout__
    else:
        run_eval()
