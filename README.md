# LLM Inference Systems Lab

A learning-driven, reproducible lab for understanding and benchmarking LLM
serving systems. The project will use vLLM and SGLang as real systems under
test while keeping workload generation, measurement, experiment design, and
analysis in this repository.

## Current checkpoint

Phase 1 establishes trustworthy latency measurements before any GPU benchmark:

- `RequestTiming` calculates time to first token (TTFT), time per output token
  (TPOT), and end-to-end latency.
- `StreamTimer` records streamed token events with a monotonic clock.
- Tests cover the metric formulas, invalid event order, single-token output,
  and a deterministic streamed-token timeline.

The repository does **not** claim vLLM or SGLang performance results yet.
Local development currently validates benchmark correctness on Apple Silicon;
framework performance experiments will run later on a controlled NVIDIA GPU
environment.

## Quick start

Run the tests without installing third-party dependencies:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Reproduce the first learning checkpoint: TTFT is 200 ms, 101 output tokens
complete at 5.2 seconds, and TPOT is 50 ms/token.

```bash
PYTHONPATH=src python3 -m inference_lab \
  --started-at 0 \
  --first-token-at 0.2 \
  --completed-at 5.2 \
  --output-tokens 101
```

## Metric definitions

For a request that produces `N` output tokens:

```text
TTFT = first_token_at - request_started_at
TPOT = (request_completed_at - first_token_at) / (N - 1)
E2E  = request_completed_at - request_started_at
```

TPOT is undefined when `N == 1`, because there is no inter-token interval
after the first token.

## Project boundary

Upstream projects provide the serving engines:

- [vLLM](https://github.com/vllm-project/vllm)
- [SGLang](https://github.com/sgl-project/sglang)

This repository owns:

- OpenAI-compatible streaming benchmark clients
- reproducible workload descriptions
- latency and throughput metric collection
- concurrency and arrival-rate experiments
- raw result schemas and analysis reports
- profiler-driven failure and bottleneck analysis

## Roadmap

- [x] Define and test TTFT, TPOT, and end-to-end latency
- [ ] Measure a local mock SSE stream end to end
- [ ] Run a controlled vLLM GPU baseline
- [ ] Sweep prompt length, output length, and concurrency
- [ ] Evaluate prefix caching and chunked prefill
- [ ] Compare vLLM and SGLang on the same workload and hardware
- [ ] Trace one bottleneck from profiler evidence into framework source
- [ ] Contribute one focused upstream issue or pull request

## Reproducibility contract

Published performance results must record the model and revision, tokenizer,
server and framework version, hardware, dtype and quantization, server flags,
workload distribution, warmup policy, repetition count, and raw measurements.
Results from different hardware or uncontrolled network paths are not treated
as direct framework comparisons.

The Chinese learning notes and durable checkpoints live in [`docs/`](docs/)
and [`teacher/`](teacher/).

## License

MIT
