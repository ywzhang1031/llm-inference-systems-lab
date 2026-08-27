import unittest

from inference_lab.metrics import RequestTiming


class RequestTimingTests(unittest.TestCase):
    def test_calculates_ttft_tpot_and_end_to_end_latency(self) -> None:
        timing = RequestTiming(
            started_at_s=0.0,
            first_token_at_s=0.2,
            completed_at_s=5.2,
            output_tokens=101,
        )

        self.assertAlmostEqual(timing.ttft_ms, 200.0)
        self.assertAlmostEqual(timing.tpot_ms, 50.0)
        self.assertAlmostEqual(timing.e2e_latency_ms, 5_200.0)

    def test_tpot_is_undefined_for_a_single_output_token(self) -> None:
        timing = RequestTiming(
            started_at_s=1.0,
            first_token_at_s=1.1,
            completed_at_s=1.1,
            output_tokens=1,
        )

        self.assertIsNone(timing.tpot_ms)

    def test_rejects_invalid_event_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "event order"):
            RequestTiming(
                started_at_s=1.0,
                first_token_at_s=0.9,
                completed_at_s=1.1,
                output_tokens=2,
            )

    def test_rejects_zero_output_tokens(self) -> None:
        with self.assertRaisesRegex(ValueError, "output_tokens"):
            RequestTiming(
                started_at_s=1.0,
                first_token_at_s=1.1,
                completed_at_s=1.2,
                output_tokens=0,
            )


if __name__ == "__main__":
    unittest.main()
