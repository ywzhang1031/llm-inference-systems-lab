import json
import unittest

from inference_lab.openai_stream import OpenAIStreamAccumulator
from inference_lab.sse import SSEDecoder
from inference_lab.stream_timer import StreamTimer


class StepClock:
    def __init__(self, *timestamps: float) -> None:
        self._timestamps = iter(timestamps)

    def __call__(self) -> float:
        return next(self._timestamps)


class OpenAIStreamAccumulatorTests(unittest.TestCase):
    def test_measures_a_mock_sse_byte_stream_end_to_end(self) -> None:
        stream = (
            'data: {"choices":[{"delta":{"role":"assistant"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"Hello world"}}]}\n\n'
            'data: {"choices":[],"usage":{"completion_tokens":2}}\n\n'
            'data: [DONE]\n\n'
        ).encode("utf-8")
        decoder = SSEDecoder()
        timer = StreamTimer(clock=StepClock(10.0, 10.2, 10.5))
        accumulator = OpenAIStreamAccumulator(timer=timer)

        for start in range(0, len(stream), 17):
            for payload in decoder.feed(stream[start : start + 17]):
                accumulator.handle_payload(payload)
        for payload in decoder.finish():
            accumulator.handle_payload(payload)
        measurement = accumulator.finish()

        self.assertEqual(measurement.text, "Hello world")
        self.assertEqual(measurement.timing.output_tokens, 2)
        self.assertAlmostEqual(measurement.timing.ttft_ms, 200.0)
        self.assertAlmostEqual(measurement.timing.tpot_ms, 300.0)

    def test_uses_usage_tokens_instead_of_counting_content_events(self) -> None:
        timer = StreamTimer(clock=StepClock(10.0, 10.2, 10.5))
        accumulator = OpenAIStreamAccumulator(timer=timer)

        accumulator.handle_payload(
            json.dumps({"choices": [{"delta": {"role": "assistant"}}]})
        )
        accumulator.handle_payload(
            json.dumps({"choices": [{"delta": {"content": "Hello world"}}]})
        )
        accumulator.handle_payload(
            json.dumps({"choices": [], "usage": {"completion_tokens": 2}})
        )
        accumulator.handle_payload("[DONE]")
        measurement = accumulator.finish()

        self.assertEqual(measurement.text, "Hello world")
        self.assertEqual(measurement.timing.output_tokens, 2)
        self.assertAlmostEqual(measurement.timing.ttft_ms, 200.0)
        self.assertAlmostEqual(measurement.timing.tpot_ms, 300.0)

    def test_accumulates_multiple_content_events_without_restarting_ttft(self) -> None:
        timer = StreamTimer(clock=StepClock(1.0, 1.1, 1.4))
        accumulator = OpenAIStreamAccumulator(timer=timer)

        accumulator.handle_payload(
            json.dumps({"choices": [{"delta": {"content": "Hel"}}]})
        )
        accumulator.handle_payload(
            json.dumps({"choices": [{"delta": {"content": "lo"}}]})
        )
        accumulator.handle_payload(
            json.dumps({"choices": [], "usage": {"completion_tokens": 3}})
        )
        accumulator.handle_payload("[DONE]")
        measurement = accumulator.finish()

        self.assertEqual(measurement.text, "Hello")
        self.assertEqual(measurement.timing.output_tokens, 3)
        self.assertAlmostEqual(measurement.timing.ttft_ms, 100.0)
        self.assertAlmostEqual(measurement.timing.tpot_ms, 150.0)

    def test_requires_server_usage_for_exact_token_counting(self) -> None:
        timer = StreamTimer(clock=StepClock(1.0, 1.1))
        accumulator = OpenAIStreamAccumulator(timer=timer)
        accumulator.handle_payload(
            json.dumps({"choices": [{"delta": {"content": "Hello"}}]})
        )
        accumulator.handle_payload("[DONE]")

        with self.assertRaisesRegex(RuntimeError, "completion_tokens"):
            accumulator.finish()


if __name__ == "__main__":
    unittest.main()
