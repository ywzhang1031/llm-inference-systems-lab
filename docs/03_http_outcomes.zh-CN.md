# 03：真实 HTTP 流的计时边界与失败语义

## TTFT 只描述实际发生的首 token 事件

客户端等待两秒后超时，不代表：

```text
TTFT = 2000 ms
```

因为首 token 从未到达。正确记录是：

```text
TTFT = undefined
time_to_timeout = 2000 ms
```

同理，HTTP 500 没有 TTFT，但可以记录 time-to-error。一个已经返回首 token、随后
断流的请求具有 observed TTFT，但它不是成功请求，不能进入成功请求的延迟分布。

## 当前 benchmark 的连接边界

主服务 benchmark 采用下面的时间线：

```text
TCP connection established
  -> request timer starts
  -> POST request
  -> queue/tokenization/prefill/first sampling
  -> first non-empty content delta
  -> complete stream or failure
```

因此，`OpenAIHTTPClient.measure()` 要求先调用 `connect()`。这使 TCP 建连成本不会因为
客户端是否复用连接而被悄悄混入 TTFT。将来如需衡量用户冷启动体验，应建立另一个明确
包含 DNS、TCP 和 TLS 的 cold-connection 指标，而不是改变当前指标的含义。

## 四种 outcome

| status | 是否有成功 TTFT/TPOT | 保留的失败证据 |
| --- | --- | --- |
| `success` | 是 | 不适用 |
| `http_error` | 否 | HTTP status、time-to-error |
| `transport_error` | 否 | error type、time-to-failure，TTFT 未定义 |
| `partial_stream` | 否 | observed TTFT、time-to-failure |

`partial_stream` 的 observed TTFT 只能用于故障分析。即使已经看到了首 token，也不能把
整个请求伪装成成功样本；如果没有最终 `usage.completion_tokens`，也不能用 SSE event 数
计算 TPOT。

## 为什么使用 `HTTPResponse.read1()`

流式响应的目标是尽快处理目前已经可读的数据。固定长度的普通 `read(n)` 可能继续等待，
尝试填满更多字节，从而让客户端自己增加观测到的 TTFT。`read1(n)` 每次最多执行一次底层
读取，更符合增量处理 SSE 的需要。

这不是模型优化，却是 benchmark correctness：如果测量工具自己缓冲了首 token，得到的
TTFT 就无法忠实表示服务行为。

## 可执行证据

`tests/test_http_client.py` 启动真实 localhost HTTP/1.1 server，并覆盖：

- 完整 chunked SSE success；
- HTTP 500；
- 首 token 前 timeout；
- 首 token 后连接中断。

这个 checkpoint 证明的是协议、计时和失败分类正确，不是 vLLM、SGLang 或 GPU 性能。
