# 01：流式推理的基础延迟指标

## 请求时间线

```text
请求发送
  -> 排队与调度
  -> prefill
  -> 第一个输出 token
  -> 逐 token decode
  -> 请求完成
```

`prefill` 处理输入 prompt，并为输入 token 建立 KV cache。`decode` 是自回归
过程：每一步根据已有上下文生成下一个 token，再把新 token 加入上下文。

## TTFT

`TTFT`（Time To First Token）表示从请求发送到收到第一个输出 token 的时间：

$$
\text{TTFT} = t_{\text{first token}} - t_{\text{start}}
$$

它可能包含排队、调度、tokenization、prefill、首个 decode step 和网络传输。
所以 TTFT 高不能自动证明 prefill kernel 慢，必须继续分解和 profiling。

## TPOT

`TPOT`（Time Per Output Token）表示第一个 token 之后，后续输出 token 的平均
生成间隔。若总共输出 `N` 个 token：

$$
\text{TPOT}
=
\frac{t_{\text{complete}} - t_{\text{first token}}}{N - 1}
$$

分母是 `N-1`，因为第一个 token 的等待已经包含在 TTFT 中。当 `N=1` 时，
没有后续 token 间隔，因此 TPOT 未定义，代码返回 `None`。

## E2E latency

端到端延迟是从请求发送到整个响应完成：

$$
\text{E2E} = t_{\text{complete}} - t_{\text{start}}
$$

在使用平均 TPOT 做近似时：

$$
\text{E2E} \approx \text{TTFT} + (N-1)\times\text{TPOT}
$$

## 第一个已验证例子

- TTFT：`200 ms`
- E2E：`5.2 s`
- 输出：`101 tokens`

$$
\text{TPOT}
=
\frac{5.2 - 0.2}{101 - 1}
=
0.05\text{ s/token}
=
50\text{ ms/token}
$$

对应的代码与测试位于：

- `src/inference_lab/metrics.py`
- `src/inference_lab/stream_timer.py`
- `tests/test_metrics.py`
- `tests/test_stream_timer.py`
