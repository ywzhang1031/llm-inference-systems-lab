# Progress

## Current status

- Current module: streamed request instrumentation
- Last completed checkpoint: correctly classified prefill-heavy vs decode-heavy requests and calculated `TPOT=50 ms/token` from `TTFT=200 ms`, `E2E=5.2 s`, and `101` output tokens
- Main confusion: how real SSE chunks map to token counts and timestamps
- Next session opener: distinguish network chunk boundaries from model token boundaries
- Next coding task: implement and test a minimal OpenAI-compatible SSE stream parser
- Acceptance criteria: measure one local mock stream end to end without treating arbitrary SSE chunks as one token each

## Recent sessions

- 2026-08-27: started the public inference-systems lab; implemented and tested TTFT, TPOT, E2E, and monotonic stream timing
