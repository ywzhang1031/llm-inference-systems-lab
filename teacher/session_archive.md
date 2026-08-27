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
