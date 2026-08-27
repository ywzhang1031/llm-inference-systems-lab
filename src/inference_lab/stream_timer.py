from __future__ import annotations

from time import perf_counter
from typing import Callable

from .metrics import RequestTiming


class StreamTimer:
    """Record token events using a monotonic clock."""

    def __init__(self, clock: Callable[[], float] = perf_counter) -> None:
        self._clock = clock
        self._started_at_s = clock()
        self._first_token_at_s: float | None = None
        self._output_tokens = 0
        self._finished = False

    def record_tokens(self, count: int) -> None:
        if self._finished:
            raise RuntimeError("cannot record tokens after the request is finished")
        if count < 1:
            raise ValueError("token count must be at least 1")

        observed_at_s = self._clock()
        if self._first_token_at_s is None:
            self._first_token_at_s = observed_at_s
        self._output_tokens += count

    def finish(self) -> RequestTiming:
        if self._finished:
            raise RuntimeError("request timing has already been finished")
        if self._first_token_at_s is None:
            raise RuntimeError("cannot finish a request with no output tokens")

        timing = RequestTiming(
            started_at_s=self._started_at_s,
            first_token_at_s=self._first_token_at_s,
            completed_at_s=self._clock(),
            output_tokens=self._output_tokens,
        )
        self._finished = True
        return timing
