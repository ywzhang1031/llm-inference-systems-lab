import unittest

from inference_lab.sse import SSEDecoder


class SSEDecoderTests(unittest.TestCase):
    def test_decodes_events_across_arbitrary_byte_and_utf8_boundaries(self) -> None:
        stream = (
            'data: {"choices":[{"delta":{"content":"你"}}]}\r\n\r\n'
            'data: [DONE]\n\n'
        ).encode("utf-8")
        chinese_start = stream.index("你".encode("utf-8"))
        chunks = [
            stream[:2],
            stream[2 : chinese_start + 1],
            stream[chinese_start + 1 : chinese_start + 2],
            stream[chinese_start + 2 : -3],
            stream[-3:],
        ]
        decoder = SSEDecoder()

        events: list[str] = []
        for chunk in chunks:
            events.extend(decoder.feed(chunk))
        events.extend(decoder.finish())

        self.assertEqual(
            events,
            [
                '{"choices":[{"delta":{"content":"你"}}]}',
                "[DONE]",
            ],
        )

    def test_joins_multiple_data_lines_in_one_event(self) -> None:
        decoder = SSEDecoder()

        events = decoder.feed(b"data: first\ndata: second\n\n")

        self.assertEqual(events, ["first\nsecond"])


if __name__ == "__main__":
    unittest.main()
