# 04：从单请求指标到 benchmark summary

## 先保留单位

如果 10 秒内提交 100 个请求，其中 80 个成功、60 个满足 TTFT SLO：

$$
\mathrm{arrival\ rate}=\frac{100\ requests}{10\ seconds}=10\ requests/second
$$

$$
\mathrm{successful\ throughput}=\frac{80}{10}=8\ requests/second
$$

$$
\mathrm{request\ goodput}=\frac{60}{10}=6\ requests/second
$$

`0.1` 是 `10 / 100` 的结果，颠倒了请求数和时间。计算系统指标时保留单位，通常能很快
发现这种错误。

## throughput 不等于 goodput

当前项目采用一个最小、明确的 request-level 定义：

```text
arrival rate = submitted requests / experiment duration
successful throughput = completed successful requests / duration
TTFT goodput = successful requests satisfying TTFT SLO / duration
```

例如成功请求的 TTFT 是 `600 ms`，而 SLO 要求 `TTFT < 500 ms`，它会增加 successful
throughput，但不会增加 TTFT goodput。

当前 goodput 只检查 TTFT。真实服务可能同时要求：

- TTFT 小于阈值；
- TPOT 小于阈值；
- E2E latency 小于阈值；
- 请求完整成功且输出质量合格。

这些多维 SLO 必须在以后显式加入，不能声称当前实现已经覆盖。

## 哪些样本进入百分位

TTFT、TPOT 和 E2E 的 `p50/p95/p99` 只使用 `SuccessfulRequest`：

```text
success -> success latency percentiles
http_error -> failure count
transport_error -> failure count
partial_stream -> failure count and diagnostic observed TTFT
```

`partial_stream.observed_ttft` 不进入成功 TTFT 百分位。把失败请求的 timeout 数值塞进
TTFT 分布，会把“首 token 从未发生”伪装成“首 token 很慢”。

当前 percentile 使用排序后的线性插值。公开结果必须记录 percentile 定义，因为不同工具
可能采用 nearest-rank 或其他估计方法，小样本时结果尤其容易不同。

## token 数是 workload sweep，不是混杂变量

比较 vLLM 与 SGLang 时，每个实验单元固定相同 workload：

| experiment cell | vLLM | SGLang |
| --- | --- | --- |
| prompt 128 / output 128 | run | run |
| prompt 2048 / output 128 | run | run |
| prompt 128 / output 512 | run | run |

token 数可以跨实验单元变化，但同一个单元内只改变 serving framework。否则无法把性能差异
归因到框架。

## 当前实现边界

`src/inference_lab/aggregation.py` 可以聚合已经产生的 request outcomes，但尚未实现：

- 并发 workload generator；
- arrival process 和请求调度；
- token throughput；
- CSV/JSONL 原始结果文件；
- vLLM/SGLang 或 NVIDIA GPU 实验。

因此当前 checkpoint 证明 aggregation semantics 正确，不是推理性能已经完成。
