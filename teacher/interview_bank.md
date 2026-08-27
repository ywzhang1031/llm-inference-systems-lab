# Interview Bank

## Questions to revisit

- Which stages contribute to TTFT, and why does high TTFT not prove that prefill kernels are the bottleneck?
- Why is TPOT undefined for a response containing only one output token?
- How should a benchmark count tokens when SSE chunks do not align with tokenizer tokens?

## Strong answers

- A long-prompt, short-output request is usually prefill-heavy; a short-prompt, long-output request is usually decode-heavy.
- For `TTFT=200 ms`, `E2E=5.2 s`, and `101` output tokens, TPOT is `(5.2-0.2)/(101-1)=50 ms/token`.
