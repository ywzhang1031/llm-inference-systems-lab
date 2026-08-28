import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from inference_lab.http_client import OpenAIHTTPClient
from inference_lab.outcomes import FailedRequest, SuccessfulRequest


class StreamingTestServer(ThreadingHTTPServer):
    daemon_threads = True


class StreamingHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(content_length)

        if self.path == "/success":
            self._start_event_stream()
            self._write_chunk(
                b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
            )
            self._write_chunk(
                b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
            )
            self._write_chunk(
                b'data: {"choices":[],"usage":{"completion_tokens":2}}\n\n'
            )
            self._write_chunk(b"data: [DONE]\n\n")
            self._finish_chunks()
            return

        if self.path == "/http-error":
            body = b'{"error":"overloaded"}'
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/timeout":
            self._start_event_stream()
            time.sleep(0.1)
            return

        if self.path == "/partial":
            self._start_event_stream()
            self._write_chunk(
                b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
            )
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return

        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _start_event_stream(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

    def _write_chunk(self, chunk: bytes) -> None:
        self.wfile.write(f"{len(chunk):X}\r\n".encode("ascii"))
        self.wfile.write(chunk)
        self.wfile.write(b"\r\n")
        self.wfile.flush()

    def _finish_chunks(self) -> None:
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()


class OpenAIHTTPClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = StreamingTestServer(("127.0.0.1", 0), StreamingHandler)
        cls.server_thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=1)

    def test_measures_real_localhost_streams_on_a_reused_connection(self) -> None:
        with self._client() as client:
            outcome = client.measure({"model": "mock"}, path="/success")
            second_outcome = client.measure({"model": "mock"}, path="/success")

        self.assertIsInstance(outcome, SuccessfulRequest)
        assert isinstance(outcome, SuccessfulRequest)
        self.assertEqual(outcome.status, "success")
        self.assertEqual(outcome.measurement.text, "Hello world")
        self.assertEqual(outcome.measurement.timing.output_tokens, 2)
        self.assertGreaterEqual(outcome.measurement.timing.ttft_ms, 0.0)
        self.assertIsInstance(second_outcome, SuccessfulRequest)

    def test_records_http_500_as_time_to_error(self) -> None:
        with self._client() as client:
            outcome = client.measure({"model": "mock"}, path="/http-error")

        self.assertIsInstance(outcome, FailedRequest)
        assert isinstance(outcome, FailedRequest)
        self.assertEqual(outcome.status, "http_error")
        self.assertEqual(outcome.http_status, 500)
        self.assertIsNone(outcome.timing.observed_ttft_ms)
        self.assertGreaterEqual(outcome.timing.time_to_failure_ms, 0.0)

    def test_records_pre_token_timeout_without_ttft(self) -> None:
        with self._client(timeout_s=0.02) as client:
            outcome = client.measure({"model": "mock"}, path="/timeout")

        self.assertIsInstance(outcome, FailedRequest)
        assert isinstance(outcome, FailedRequest)
        self.assertEqual(outcome.status, "transport_error")
        self.assertEqual(outcome.error_type, "timeout")
        self.assertIsNone(outcome.timing.observed_ttft_ms)
        self.assertGreaterEqual(outcome.timing.time_to_failure_ms, 10.0)

    def test_keeps_partial_stream_out_of_success_results(self) -> None:
        with self._client() as client:
            outcome = client.measure({"model": "mock"}, path="/partial")

        self.assertIsInstance(outcome, FailedRequest)
        assert isinstance(outcome, FailedRequest)
        self.assertEqual(outcome.status, "partial_stream")
        self.assertIsNotNone(outcome.timing.observed_ttft_ms)

    def _client(self, *, timeout_s: float = 1.0) -> OpenAIHTTPClient:
        host, port = self.server.server_address
        client = OpenAIHTTPClient(host, port, timeout_s=timeout_s)
        client.connect()
        return client


if __name__ == "__main__":
    unittest.main()
