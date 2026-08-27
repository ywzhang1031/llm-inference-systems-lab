# Resource Map

## Local materials

- `docs/01_latency_metrics.zh-CN.md`: source of truth for the first latency checkpoint
- `docs/02_sse_token_accounting.zh-CN.md`: protocol boundaries and exact token-accounting rules
- `src/inference_lab/`: benchmark-owned metric and timing code
- `tests/`: executable definitions of accepted metric behavior

## External materials

- vLLM official repository and architecture documentation
- SGLang official repository and documentation
- PyTorch profiler and distributed documentation
- Framework source and original papers for mechanism-level claims

## Notes

- Official benchmark CLIs are validation references, not substitutes for this lab's workload and analysis code.
- Performance claims require raw measurements plus the complete environment and workload configuration.
- Network chunks, SSE events, content deltas, and tokenizer tokens must remain separate measurement concepts.
