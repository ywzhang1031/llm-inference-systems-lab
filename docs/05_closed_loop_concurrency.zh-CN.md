# 05：Closed-loop concurrency 与 bounded workload runner

## concurrency 是在途请求数量

`concurrency=3` 表示客户端最多同时等待三个未完成请求：

```text
worker 0: request A in flight
worker 1: request B in flight
worker 2: request C in flight
```

某个 worker 完成请求后，才领取下一个 request ID：

```text
B completes
  -> worker 1 submits D
```

这就是当前 runner 的 closed-loop 行为。服务响应越快，worker 补位越快，实际 arrival
rate 越高；服务响应越慢，arrival rate 越低。

## 与 open-loop 的区别

```text
closed-loop: fixed concurrency -> arrival rate depends on service latency
open-loop: fixed arrival rate -> concurrency and queueing depend on service latency
```

稳态直觉来自 Little's Law：

$$
\mathrm{average\ concurrency}
\approx
\mathrm{arrival\ rate}\times\mathrm{average\ latency}
$$

因此，固定发送 `4 requests/s`、平均延迟 `2 s` 时，平均 concurrency 约为 8。反过来，
closed-loop 固定 concurrency 为 2、平均延迟为 1 秒时，实际 arrival rate 约为 2
requests/s。

## 为什么每个 worker 拥有自己的 HTTP client

`HTTPConnection` 不是供多个线程同时写入的共享请求通道。当前接口要求
`worker_factory` 为每个 worker 创建独立上下文：

```text
worker 0 -> preconnected HTTP client 0
worker 1 -> preconnected HTTP client 1
worker 2 -> preconnected HTTP client 2
```

同一个 worker 可以在连续请求之间复用自己的连接，同时避免多个线程交叉写入同一连接。
runner 会等待所有 worker 上下文准备完成，再统一开放请求提交，避免连接建立速度差异导致
初始实际 concurrency 低于配置值。

## 为什么保存每个 RequestRecord

只保留最终 p50/p95 会丢失大量诊断证据。每个 request record 保存：

- `request_id`；
- `submitted_at_s`；
- `completed_at_s`；
- client-observed latency；
- 完整的 success 或 failure outcome。

最终 summary 可以从这些 records 重新计算。这样发现 percentile 或 failure-rate 错误时，
不需要重新运行昂贵的 GPU 实验。

## 当前验证

`tests/test_workload.py` 验证：

- configured concurrency 不会被突破；
- 完成一个请求后会补充下一个请求；
- 所有 request ID 都有 record；
- raw records 可以 JSON 序列化，同一批 in-memory outcomes 可以重新聚合；
- worker 的非 outcome 异常会传播，而不是静默丢样本；
- 三个 worker 使用各自的持久 client，并发完成真实 localhost HTTP/SSE 请求。

## 尚未覆盖

- 固定 arrival rate 的 open-loop generator；
- burst、Poisson arrival 或 trace replay；
- 服务端 continuous batching 的内部 batch 观测；
- 将 raw records 写入版本化 JSONL artifact；
- vLLM/SGLang 和 NVIDIA GPU 性能。

因此，客户端 concurrency 仍然不能被解释为 GPU batch size，也不能把 localhost 测试结果
写成推理框架性能结论。
