# Progress

## Current status

- Current module: real OpenAI-compatible HTTP streaming transport
- Last completed checkpoint: decoded arbitrary byte and UTF-8 boundaries, accumulated OpenAI content deltas, and measured a mock SSE stream without equating network chunks or SSE events with tokenizer tokens
- Main confusion: where the request timer should start relative to connection setup, request write, and server queueing
- Next session opener: define client-observed latency boundaries before selecting an HTTP library
- Next coding task: implement a minimal streaming HTTP client against a deterministic local server
- Acceptance criteria: measure one real localhost HTTP stream with explicit timeout and error behavior, while preserving the tested SSE and token-accounting layers

## Recent sessions

- 2026-08-27: started the public inference-systems lab; implemented and tested TTFT, TPOT, E2E, and monotonic stream timing
- 2026-08-27: passed SSE and token-accounting checkpoint with incremental UTF-8 decoding, server-reported completion tokens, and an end-to-end mock byte stream
