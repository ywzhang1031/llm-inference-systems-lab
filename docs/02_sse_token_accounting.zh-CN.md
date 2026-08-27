# 02：SSE 传输与 token 计数为什么必须分离

## 三种边界不是一回事

流式推理同时涉及三个层次：

```text
HTTP network bytes
  -> SSE event
  -> OpenAI content delta
  -> tokenizer tokens
```

它们之间不存在一一对应关系：

- 一个网络 chunk 可能只有半行 JSON；
- 一个网络 chunk 也可能包含多个完整 SSE event；
- 一个 UTF-8 字符可能被拆到两个网络 chunk；
- role、usage 和 `[DONE]` event 不包含输出文本；
- 一个 `content` delta 可能包含零个、一个或多个 tokenizer token。

因此下面的计数是错误的：

```python
for network_chunk in response:
    output_tokens += 1
```

下面这种做法同样不可靠：

```python
for sse_event in events:
    output_tokens += 1
```

## TTFT 怎样记录

当前项目把 TTFT 的观测点定义为：客户端收到第一个非空 `content` delta 的时间。

role-only delta 不触发 TTFT：

```json
{"choices":[{"delta":{"role":"assistant"}}]}
```

第一个非空 content 才触发：

```json
{"choices":[{"delta":{"content":"Hello world"}}]}
```

即使 `"Hello world"` 对应多个 tokenizer token，也只记录一次 first-token 时间点。

## output token 怎样计算

当前 checkpoint 要求服务端在流结束前提供：

```json
{"choices":[],"usage":{"completion_tokens":2}}
```

然后使用 `completion_tokens=2` 计算 TPOT。它不会因为 `"Hello world"` 只在一个
content event 中到达，就把它误记为一个 token。

如果服务端不返回 usage，后续 adapter 必须使用该模型对应的精确 tokenizer 对完整输出
重新编码。不能使用字符数、单词数或 SSE event 数作为替代。

## 当前实现边界

- `SSEDecoder`：把任意 byte chunks 恢复成完整 SSE data payload；
- `OpenAIStreamAccumulator`：解析 payload、累计文本和最终 usage；
- `StreamTimer`：记录 request start、first content 和 completion；
- `RequestTiming`：根据时间点和精确 token 数计算 TTFT、TPOT 与 E2E。

端到端测试位于 `tests/test_openai_stream.py`。测试故意每 17 bytes 切一次网络流，
证明 byte chunk 的形状不会改变文本、token 数或延迟指标。

## 尚未覆盖

- 真实 HTTP 连接、超时和取消；
- 多请求并发与 arrival-rate 控制；
- reasoning content 与 visible content 的独立指标；
- 服务端不返回 usage 时的精确 tokenizer adapter。

这些内容必须作为后续独立 checkpoint 添加，不能在当前层假装已经完成。
