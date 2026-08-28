from __future__ import annotations

from time import perf_counter
from typing import Callable

from .metrics import FailureTiming, RequestTiming


class StreamTimer:
    """Record the first streamed output and request completion times."""

    def __init__(self, clock: Callable[[], float] = perf_counter) -> None:
        self._clock = clock
        self._started_at_s = clock()
        self._first_token_at_s: float | None = None
        self._finished = False

    def mark_first_token(self) -> None:
        if self._finished:
            raise RuntimeError("cannot record output after the request is finished")

        if self._first_token_at_s is None:
            self._first_token_at_s = self._clock()

    def finish(self, *, output_tokens: int) -> RequestTiming:
        if self._finished:
            raise RuntimeError("request timing has already been finished")
        if self._first_token_at_s is None:
            raise RuntimeError("cannot finish a request with no output tokens")

        timing = RequestTiming(
            started_at_s=self._started_at_s,
            first_token_at_s=self._first_token_at_s,
            completed_at_s=self._clock(),
            output_tokens=output_tokens,
        )
        self._finished = True
        return timing

    def fail(self) -> FailureTiming:
        if self._finished:
            raise RuntimeError("request timing has already been finished")

        timing = FailureTiming(
            started_at_s=self._started_at_s,
            first_token_at_s=self._first_token_at_s,
            failed_at_s=self._clock(),
        )
        self._finished = True
        return timing

    @property
    def has_observed_first_token(self) -> bool:
        return self._first_token_at_s is not None
