# Retrieval ablation (Phase 5)

Run: 2026-11-18 23:36 | model: openai/gpt-oss-120b | k=6 | LLM runs per question: 1

Accuracy = keyword/number match against `answer_keywords` in `eval/questions.json`, averaged over runs. Out-of-scope = exact fallback sentence.

| Retrieval | Chunk headers | hit@6 | page hit@6 | OCR hit@6 | accuracy (in-scope) | accuracy (OCR) | out-of-scope | accuracy (all) |
|---|---|---|---|---|---|---|---|---|
| vector | off | 83% | 73% | 73% | 70% | 64% | 100% | 73% |
| hybrid | off | 97% | 80% | 100% | 77% | 73% | 100% | 79% |
| vector | on | 80% | 73% | 73% | 68% (28/30 q) | 55% | - | 68% (28/33 q) |
| hybrid | on | 97% | 80% | 100% | 75% (4/30 q) | 100% (1/11 q) | 100% (1/3 q) | 80% (5/33 q) |

## Per-question results

Each cell: retrieval (H = expected file in context, P = also expected page, - = missed) / correct answers out of runs.

| id | type | OCR | vector_headers-off | hybrid_headers-off | vector_headers-on | hybrid_headers-on |
|---|---|---|---|---|---|---|
| q01 | fee |  | - / 0/1 | H / 0/1 | - / 0/1 | H / 0/1 |
| q02 | fee |  | H / 0/1 | H / 0/1 | H / 0/1 | H / - |
| q03 | fee |  | - / 0/1 | P / 0/1 | P / 1/1 | P / - |
| q04 | fee |  | P / 1/1 | H / 1/1 | P / 1/1 | H / - |
| q05 | fee |  | H / 1/1 | - / 0/1 | - / 0/1 | - / - |
| q06 | fee | yes | - / 0/1 | H / 0/1 | - / 0/1 | H / - |
| q07 | fee |  | P / 1/1 | P / 1/1 | - / 1/1 | P / - |
| q08 | fee | yes | H / 0/1 | H / 0/1 | H / 0/1 | H / - |
| q09 | CGPA |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q10 | CGPA | yes | P / 0/1 | P / 0/1 | P / 0/1 | P / - |
| q11 | CGPA |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q12 | CGPA | yes | - / 1/1 | P / 1/1 | - / 0/1 | P / 1/1 |
| q13 | CGPA | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q14 | CGPA | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q15 | CGPA |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q16 | promotion |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q17 | promotion | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q18 | promotion |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q19 | promotion |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q20 | PhD |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q21 | PhD | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q22 | PhD | yes | - / 0/1 | P / 1/1 | - / 0/1 | P / - |
| q23 | PhD |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q24 | internship |  | P / 1/1 | P / 1/1 | P / 1/1 | P / 1/1 |
| q25 | internship |  | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q26 | regulation |  | P / 0/1 | P / 1/1 | P / 0/1 | P / - |
| q27 | regulation | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q28 | regulation | yes | P / 1/1 | P / 1/1 | P / 1/1 | P / - |
| q29 | UFM |  | P / 0/1 | P / 1/1 | P / - | P / - |
| q30 | UFM |  | P / 1/1 | P / 1/1 | P / - | P / - |
| q31 | out-of-scope |  | n/a / 1/1 | n/a / 1/1 | n/a / - | n/a / 1/1 |
| q32 | out-of-scope |  | n/a / 1/1 | n/a / 1/1 | n/a / - | n/a / - |
| q33 | out-of-scope |  | n/a / 1/1 | n/a / 1/1 | n/a / - | n/a / - |

## Incomplete runs

- vector_headers-on: not all LLM answers available (Groq daily token limit); re-run to resume, answers are cached.
- hybrid_headers-on: not all LLM answers available (Groq daily token limit); re-run to resume, answers are cached.
