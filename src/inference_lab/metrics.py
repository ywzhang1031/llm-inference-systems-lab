from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestTiming:
    """Timestamps and latency metrics for one streamed inference request."""

    started_at_s: float
    first_token_at_s: float
    completed_at_s: float
    output_tokens: int

    def __post_init__(self) -> None:
        if self.output_tokens < 1:
            raise ValueError("output_tokens must be at least 1")
        if not (
            self.started_at_s <= self.first_token_at_s <= self.completed_at_s
        ):
            raise ValueError(
                "invalid event order: expected start <= first token <= completion"
            )

    @property
    def ttft_ms(self) -> float:
        """Time to first token in milliseconds."""

        return (self.first_token_at_s - self.started_at_s) * 1_000

    @property
    def tpot_ms(self) -> float | None:
        """Average time per output token after the first token."""

        if self.output_tokens == 1:
            return None
        decode_duration_s = self.completed_at_s - self.first_token_at_s
        return decode_duration_s * 1_000 / (self.output_tokens - 1)

    @property
    def e2e_latency_ms(self) -> float:
        """End-to-end request latency in milliseconds."""

        return (self.completed_at_s - self.started_at_s) * 1_000

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "output_tokens": self.output_tokens,
            "ttft_ms": self.ttft_ms,
            "tpot_ms": self.tpot_ms,
            "e2e_latency_ms": self.e2e_latency_ms,
        }


@dataclass(frozen=True, slots=True)
class FailureTiming:
    """Timing evidence for a request that did not complete successfully."""

    started_at_s: float
    first_token_at_s: float | None
    failed_at_s: float

    def __post_init__(self) -> None:
        if self.started_at_s > self.failed_at_s:
            raise ValueError("invalid event order: failure preceded request start")
        if self.first_token_at_s is not None and not (
            self.started_at_s <= self.first_token_at_s <= self.failed_at_s
        ):
            raise ValueError(
                "invalid event order: expected start <= first token <= failure"
            )

    @property
    def observed_ttft_ms(self) -> float | None:
        """Observed TTFT for a partial stream, otherwise undefined."""

        if self.first_token_at_s is None:
            return None
        return (self.first_token_at_s - self.started_at_s) * 1_000

    @property
    def time_to_failure_ms(self) -> float:
        return (self.failed_at_s - self.started_at_s) * 1_000
