import unittest

from inference_lab.stream_timer import StreamTimer


class StepClock:
    def __init__(self, *timestamps: float) -> None:
        self._timestamps = iter(timestamps)

    def __call__(self) -> float:
        return next(self._timestamps)


class StreamTimerTests(unittest.TestCase):
    def test_separates_first_token_time_from_final_token_count(self) -> None:
        clock = StepClock(10.0, 10.2, 15.2)
        timer = StreamTimer(clock=clock)

        timer.mark_first_token()
        timing = timer.finish(output_tokens=101)

        self.assertAlmostEqual(timing.ttft_ms, 200.0)
        self.assertAlmostEqual(timing.tpot_ms, 50.0)
        self.assertAlmostEqual(timing.e2e_latency_ms, 5_200.0)
        self.assertEqual(timing.output_tokens, 101)

    def test_rejects_completion_without_output_tokens(self) -> None:
        timer = StreamTimer(clock=StepClock(1.0))

        with self.assertRaisesRegex(RuntimeError, "no output tokens"):
            timer.finish(output_tokens=1)


if __name__ == "__main__":
    unittest.main()
