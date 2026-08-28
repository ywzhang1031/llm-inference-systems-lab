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
