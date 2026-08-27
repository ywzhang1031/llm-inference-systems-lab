from __future__ import annotations

import json
from dataclasses import dataclass

from .metrics import RequestTiming
from .stream_timer import StreamTimer


@dataclass(frozen=True, slots=True)
class StreamMeasurement:
    text: str
    timing: RequestTiming


class OpenAIStreamAccumulator:
    """Accumulate OpenAI-compatible content deltas and exact usage tokens."""

    def __init__(self, *, timer: StreamTimer) -> None:
        self._timer = timer
        self._text_parts: list[str] = []
        self._completion_tokens: int | None = None
        self._done = False

    def handle_payload(self, payload: str) -> None:
        if self._done:
            raise RuntimeError("cannot handle payloads after [DONE]")
        if payload == "[DONE]":
            self._done = True
            return

        message = json.loads(payload)
        usage = message.get("usage")
        if isinstance(usage, dict):
            completion_tokens = usage.get("completion_tokens")
            if isinstance(completion_tokens, int):
                self._completion_tokens = completion_tokens

        choices = message.get("choices", [])
        if not choices:
            return
        delta = choices[0].get("delta", {})
        content = delta.get("content")
        if not isinstance(content, str) or not content:
            return

        if not self._text_parts:
            self._timer.mark_first_token()
        self._text_parts.append(content)

    def finish(self) -> StreamMeasurement:
        if not self._done:
            raise RuntimeError("cannot finish before the [DONE] event")
        if self._completion_tokens is None:
            raise RuntimeError("stream did not report usage.completion_tokens")

        return StreamMeasurement(
            text="".join(self._text_parts),
            timing=self._timer.finish(output_tokens=self._completion_tokens),
        )
