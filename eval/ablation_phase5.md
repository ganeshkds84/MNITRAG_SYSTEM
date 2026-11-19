# Retrieval ablation (Phase 5)

Run: 2026-11-19 17:15 | model: openai/gpt-oss-120b | k=6 | LLM runs per question: 1

Accuracy = keyword/number match against `answer_keywords` in `eval/questions.json`, averaged over runs. Out-of-scope = exact fallback sentence.

| Retrieval | Chunk headers | hit@6 | page hit@6 | OCR hit@6 | accuracy (in-scope) | accuracy (OCR) | out-of-scope | accuracy (all) |
|---|---|---|---|---|---|---|---|---|
| vector | off | 90% | 80% | 82% | 73% | 64% | 100% | 76% |
| hybrid | off | 97% | 80% | 100% | 77% | 73% | 100% | 79% |
| vector | on | 83% | 77% | 82% | 67% | 55% | 100% | 70% |
| hybrid | on | 97% | 80% | 100% | 73% | 73% | 100% | 76% |

## Per-question results

Each cell: retrieval (H = expected file in context, P = also expected page, - = missed) / correct answers out of runs.

| id | type | OCR | vector_headers-off | hybrid_headers-off | vector_headers-on | hybrid_headers-on |
|---|---|---|---|---|---|---|
| q01 | fee |  | - / 0/1 | H / 0/1 | - / 0/1 | H / 0/1 |
| q02 | fee |  | H / 0/1 | H / 0/1 | H / 0/1 | H / 0/1 |
| q03 | fee |  | P / 1/1 | P / 0/1 | P / 0/1 | P / 0/1 |
| q04 | fee |  | P / 1/1 | H / 1/1 | P / 1/1 | H / 1/1 |
| q05 | fee |  | H / 1/1 | - / 0/1 | - / 0/1 | - / 0/1 |
| q06 | fee | yes | - / 0/1 | H / 0/1 | - / 0/1 | H / 0/1 |
| q07 | fee |  | P / 1/1 | P / 1/1 | - / 1/1 | P / 1/1 |
| q08 | fee | yes | H / 0/1 | H / 0/1 | H / 0/1 | H / 0/1 |
| q09 | CGPA |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q10 | CGPA | yes | P / 0/1 | P / 0/1 | P / 0/1 | P / 0/1 |
| q11 | CGPA |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q12 | CGPA | yes | P / 1/1 | P / 1/1 | P / 0/1 | P / 1/1 |
| q13 | CGPA | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q14 | CGPA | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q15 | CGPA |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q16 | promotion |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q17 | promotion | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q18 | promotion |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q19 | promotion |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q20 | PhD |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q21 | PhD | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q22 | PhD | yes | - / 0/1 | P / 1/1 | - / 0/1 | P / 1/1 |
| q23 | PhD |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q24 | internship |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q25 | internship |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q26 | regulation |  | P / 0/1 | P / 1/1 | P / 0/1 | P / 1/1 |
| q27 | regulation | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q28 | regulation | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q29 | UFM |  | P / 0/1 | P / 1/1 | P / 1/1 | P / 0/1 |
| q30 | UFM |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q31 | out-of-scope |  | n/a / 1/1 | n/a / 1/1 | n/a / 1/1 | n/a / 1/1 |
| q32 | out-of-scope |  | n/a / 1/1 | n/a / 1/1 | n/a / 1/1 | n/a / 1/1 |
| q33 | out-of-scope |  | n/a / 1/1 | n/a / 1/1 | n/a / 1/1 | n/a / 1/1 |
