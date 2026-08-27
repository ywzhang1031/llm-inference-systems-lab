# Career Target

## Current target

- Primary role: LLM training/inference framework engineer and AI infrastructure engineer
- Adjacent acceptable roles: deep-learning systems engineer and Agent infrastructure engineer
- Secondary track: Agent runtime, evaluation, and Agent RL systems
- Goal: Build and explain a reproducible vLLM/SGLang benchmark lab for AI infrastructure roles.
- Deadline: No hard deadline recorded yet.

## Evidence from job-market scans

- 2026-08-27: DeepSeek's training/inference framework role emphasizes distributed training and inference, long context, MoE, low precision, RL systems, KV-cache storage, and load balancing.
- 2026-08-27: The role requires strong engineering fundamentals and PyTorch familiarity; CUDA, RDMA, profiling, and open-source work are differentiating evidence.

## Resume fit

- Strong matches:
  - HPC-related engineering and systems debugging
  - Existing training-loop, checkpoint, KV-cache, RL, and Agent runtime work
  - Master's-level research and code-first learning experience
- Gaps:
  - Reproducible serving benchmark evidence
  - Real multi-request GPU profiling and bottleneck diagnosis
  - Public inference-framework contribution

## Active sprint

- Next 7-day plan:
  - Validate streamed latency measurement locally
  - Implement the first OpenAI-compatible SSE client
  - Specify the first controlled vLLM workload
- Active project commitments:
  - `llm-inference-systems-lab`
- Paused or deferred learning threads:
  - Deep CUDA kernel optimization remains a later specialization
  - Agent feature breadth is secondary to inference-system evidence

## Resume and application trigger

- Update the resume after one controlled vLLM GPU baseline and one profiler-backed analysis are published.
