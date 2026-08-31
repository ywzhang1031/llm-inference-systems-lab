import json
import unittest

from inference_lab.aggregation import aggregate_outcomes
from inference_lab.metrics import FailureTiming, RequestTiming
from inference_lab.openai_stream import StreamMeasurement
from inference_lab.outcomes import FailureStatus, FailedRequest, SuccessfulRequest


def successful_request(
    *,
    ttft_ms: float,
    tpot_ms: float | None = 50.0,
) -> SuccessfulRequest:
    output_tokens = 1 if tpot_ms is None else 2
    first_token_at_s = ttft_ms / 1_000
    completed_at_s = first_token_at_s
    if tpot_ms is not None:
        completed_at_s += tpot_ms / 1_000
    timing = RequestTiming(
        started_at_s=0.0,
        first_token_at_s=first_token_at_s,
        completed_at_s=completed_at_s,
        output_tokens=output_tokens,
    )
    return SuccessfulRequest(StreamMeasurement(text="ok", timing=timing))


def failed_request(
    status: FailureStatus,
    *,
    observed_ttft_ms: float | None = None,
) -> FailedRequest:
    first_token_at_s = (
        None if observed_ttft_ms is None else observed_ttft_ms / 1_000
    )
    return FailedRequest(
        status=status,
        timing=FailureTiming(
            started_at_s=0.0,
            first_token_at_s=first_token_at_s,
            failed_at_s=1.0,
        ),
        error_type="test",
        message="synthetic failure",
    )


class AggregateOutcomesTests(unittest.TestCase):
    def test_calculates_rates_percentiles_and_failure_counts(self) -> None:
        outcomes = [successful_request(ttft_ms=400.0) for _ in range(60)]
        outcomes += [successful_request(ttft_ms=600.0) for _ in range(20)]
        outcomes += [failed_request("http_error") for _ in range(5)]
        outcomes += [failed_request("transport_error") for _ in range(10)]
        outcomes += [
            failed_request("partial_stream", observed_ttft_ms=100.0)
            for _ in range(5)
        ]

        summary = aggregate_outcomes(
            outcomes,
            duration_s=10.0,
            ttft_slo_ms=500.0,
        )

        self.assertEqual(summary.submitted_requests, 100)
        self.assertEqual(summary.successful_requests, 80)
        self.assertEqual(summary.slo_compliant_requests, 60)
        self.assertAlmostEqual(summary.arrival_rate_rps, 10.0)
        self.assertAlmostEqual(summary.successful_throughput_rps, 8.0)
        self.assertAlmostEqual(summary.request_goodput_rps, 6.0)
        self.assertEqual(
            summary.failure_counts,
            {
                "http_error": 5,
                "transport_error": 10,
                "partial_stream": 5,
            },
        )
        self.assertAlmostEqual(summary.ttft_ms.p50, 400.0)
        self.assertAlmostEqual(summary.ttft_ms.p95, 600.0)
        self.assertAlmostEqual(summary.tpot_ms.p50, 50.0)

    def test_excludes_partial_stream_ttft_from_success_percentiles(self) -> None:
        outcomes = [
            successful_request(ttft_ms=1_000.0),
            failed_request("partial_stream", observed_ttft_ms=1.0),
        ]

        summary = aggregate_outcomes(
            outcomes,
            duration_s=1.0,
            ttft_slo_ms=500.0,
        )

        self.assertAlmostEqual(summary.ttft_ms.p50, 1_000.0)
        self.assertEqual(summary.slo_compliant_requests, 0)
        self.assertAlmostEqual(summary.request_goodput_rps, 0.0)

    def test_handles_no_successful_tpot_samples(self) -> None:
        summary = aggregate_outcomes(
            [successful_request(ttft_ms=100.0, tpot_ms=None)],
            duration_s=1.0,
            ttft_slo_ms=500.0,
        )

        self.assertIsNone(summary.tpot_ms.p50)
        self.assertIsNone(summary.tpot_ms.p95)
        self.assertIsNone(summary.tpot_ms.p99)

    def test_uses_linear_interpolation_for_percentiles(self) -> None:
        summary = aggregate_outcomes(
            [
                successful_request(ttft_ms=100.0),
                successful_request(ttft_ms=300.0),
            ],
            duration_s=1.0,
            ttft_slo_ms=500.0,
        )

        self.assertAlmostEqual(summary.ttft_ms.p50, 200.0)

    def test_serializes_to_plain_data(self) -> None:
        summary = aggregate_outcomes(
            [successful_request(ttft_ms=100.0)],
            duration_s=1.0,
            ttft_slo_ms=500.0,
        )

        data = summary.as_dict()

        json.dumps(data)
        self.assertEqual(data["submitted_requests"], 1)
        self.assertEqual(data["ttft_ms"]["p50"], 100.0)
        self.assertEqual(data["failure_counts"]["transport_error"], 0)

    def test_rejects_invalid_experiment_duration(self) -> None:
        with self.assertRaisesRegex(ValueError, "duration_s"):
            aggregate_outcomes([], duration_s=0.0, ttft_slo_ms=500.0)


if __name__ == "__main__":
    unittest.main()
