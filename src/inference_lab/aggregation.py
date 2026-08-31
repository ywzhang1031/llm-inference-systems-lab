from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .outcomes import FailedRequest, RequestOutcome, SuccessfulRequest


@dataclass(frozen=True, slots=True)
class LatencyPercentiles:
    p50: float | None
    p95: float | None
    p99: float | None

    def as_dict(self) -> dict[str, float | None]:
        return {
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    duration_s: float
    ttft_slo_ms: float
    submitted_requests: int
    successful_requests: int
    slo_compliant_requests: int
    failure_counts: dict[str, int]
    arrival_rate_rps: float
    successful_throughput_rps: float
    request_goodput_rps: float
    ttft_ms: LatencyPercentiles
    tpot_ms: LatencyPercentiles
    e2e_latency_ms: LatencyPercentiles

    def as_dict(self) -> dict[str, object]:
        return {
            "duration_s": self.duration_s,
            "ttft_slo_ms": self.ttft_slo_ms,
            "submitted_requests": self.submitted_requests,
            "successful_requests": self.successful_requests,
            "slo_compliant_requests": self.slo_compliant_requests,
            "failure_counts": dict(self.failure_counts),
            "arrival_rate_rps": self.arrival_rate_rps,
            "successful_throughput_rps": self.successful_throughput_rps,
            "request_goodput_rps": self.request_goodput_rps,
            "ttft_ms": self.ttft_ms.as_dict(),
            "tpot_ms": self.tpot_ms.as_dict(),
            "e2e_latency_ms": self.e2e_latency_ms.as_dict(),
        }


def aggregate_outcomes(
    outcomes: Iterable[RequestOutcome],
    *,
    duration_s: float,
    ttft_slo_ms: float,
) -> BenchmarkSummary:
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    if ttft_slo_ms <= 0:
        raise ValueError("ttft_slo_ms must be positive")

    recorded_outcomes = list(outcomes)
    successes: list[SuccessfulRequest] = []
    failure_counts = {
        "http_error": 0,
        "transport_error": 0,
        "partial_stream": 0,
    }

    for outcome in recorded_outcomes:
        if isinstance(outcome, SuccessfulRequest):
            successes.append(outcome)
        elif isinstance(outcome, FailedRequest):
            failure_counts[outcome.status] += 1

    ttft_values = [item.measurement.timing.ttft_ms for item in successes]
    tpot_values = [
        tpot
        for item in successes
        if (tpot := item.measurement.timing.tpot_ms) is not None
    ]
    e2e_values = [
        item.measurement.timing.e2e_latency_ms for item in successes
    ]
    slo_compliant_requests = sum(
        ttft < ttft_slo_ms for ttft in ttft_values
    )

    submitted_requests = len(recorded_outcomes)
    successful_requests = len(successes)
    return BenchmarkSummary(
        duration_s=duration_s,
        ttft_slo_ms=ttft_slo_ms,
        submitted_requests=submitted_requests,
        successful_requests=successful_requests,
        slo_compliant_requests=slo_compliant_requests,
        failure_counts=failure_counts,
        arrival_rate_rps=submitted_requests / duration_s,
        successful_throughput_rps=successful_requests / duration_s,
        request_goodput_rps=slo_compliant_requests / duration_s,
        ttft_ms=_summarize_percentiles(ttft_values),
        tpot_ms=_summarize_percentiles(tpot_values),
        e2e_latency_ms=_summarize_percentiles(e2e_values),
    )


def _summarize_percentiles(values: list[float]) -> LatencyPercentiles:
    ordered = sorted(values)
    return LatencyPercentiles(
        p50=_percentile(ordered, 0.50),
        p95=_percentile(ordered, 0.95),
        p99=_percentile(ordered, 0.99),
    )


def _percentile(ordered: list[float], quantile: float) -> float | None:
    if not ordered:
        return None

    position = (len(ordered) - 1) * quantile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    lower = ordered[lower_index]
    upper = ordered[upper_index]
    return lower + (upper - lower) * fraction
