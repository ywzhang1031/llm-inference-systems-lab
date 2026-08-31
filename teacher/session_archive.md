# Session Archive

Move stale progress snapshots and retired plan items here instead of deleting them.

## 2026-08-27 — Project start

- Target changed to AI infrastructure first, Agent systems second.
- Passed the initial prefill/decode classification and TPOT calculation.
- Established a tested metric core before introducing vLLM, SGLang, or rented GPU hardware.
- Next stage: real SSE streaming semantics and token accounting.

## 2026-08-27 — SSE and token accounting

- Separated network chunks, SSE events, OpenAI content deltas, and tokenizer tokens.
- Refactored timing so first-output observation and final token count are independent.
- Passed a complete mock byte-stream measurement with exact server-reported usage.
- Next stage: real localhost HTTP streaming, connection timing, timeout, and failure semantics.

## 2026-08-28 — HTTP timing and failure semantics

- Defined the primary service benchmark around a reused connection and client-observed request latency.
- Correctly rejected HTTP 500 responses from successful TTFT statistics and retained their time-to-error separately.
- Distinguished an observed first-token timestamp on a partial stream from a successfully completed request.
- Correctly rejected SSE content-event counts as output-token counts.
- Implemented these semantics in a real localhost HTTP streaming client and deterministic test server.
- Next stage: aggregate success percentiles, failure rate, throughput, and goodput without mixing their populations.

## 2026-08-31 — Aggregation and TTFT goodput

- Corrected the rate-unit calculation from `0.1/0.8/0.6` to `10/8/6 requests/s` for 100/80/60 requests over 10 seconds.
- Implemented serializable success percentiles, failure counts, arrival rate, successful throughput, and TTFT goodput.
- Kept partial-stream observed TTFT out of successful TTFT percentiles.
- Next stage: bounded concurrent workload generation and raw per-request result persistence.

## 2026-08-31 — Bounded closed-loop concurrency

- Passed the closed-loop estimate `concurrency=2`, latency `1 s` -> about `2 requests/s`.
- Passed the open-loop Little's Law estimate `4 requests/s`, latency `2 s` -> average concurrency about 8.
- Implemented worker-scoped reusable HTTP clients, closed-loop slot refill, timestamped per-request records, serialization, and aggregation.
- Verified concurrent requests against the deterministic localhost HTTP/SSE server.
- Next stage: fixed-rate open-loop scheduling, scheduling lag, and versioned JSONL artifacts.
