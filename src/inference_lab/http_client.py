from __future__ import annotations

import http.client
import json
from time import perf_counter
from typing import Callable, Mapping

from .openai_stream import OpenAIStreamAccumulator
from .outcomes import FailedRequest, RequestOutcome, SuccessfulRequest
from .sse import SSEDecoder
from .stream_timer import StreamTimer


class OpenAIHTTPClient:
    """Measure one OpenAI-compatible SSE request over a preconnected socket."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        timeout_s: float = 30.0,
        read_size: int = 64 * 1024,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if read_size < 1:
            raise ValueError("read_size must be at least 1")

        self._connection = http.client.HTTPConnection(
            host,
            port,
            timeout=timeout_s,
        )
        self._read_size = read_size
        self._clock = clock

    def connect(self) -> None:
        """Establish the connection before request timing begins."""

        if self._connection.sock is None:
            self._connection.connect()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> OpenAIHTTPClient:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def measure(
        self,
        payload: Mapping[str, object],
        *,
        path: str = "/v1/chat/completions",
    ) -> RequestOutcome:
        if self._connection.sock is None:
            raise RuntimeError("call connect() before measuring a request")

        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        timer = StreamTimer(clock=self._clock)

        try:
            self._connection.request(
                "POST",
                path,
                body=body,
                headers={
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                },
            )
            response = self._connection.getresponse()
        except (OSError, http.client.HTTPException) as error:
            failure = self._transport_failure(timer, error)
            self.close()
            return failure

        if response.status != 200:
            failure = FailedRequest(
                status="http_error",
                timing=timer.fail(),
                error_type="http_status",
                message=f"HTTP {response.status} {response.reason}",
                http_status=response.status,
            )
            try:
                response.read()
            except (OSError, http.client.HTTPException):
                self.close()
            return failure

        decoder = SSEDecoder()
        accumulator = OpenAIStreamAccumulator(timer=timer)

        try:
            while chunk := response.read1(self._read_size):
                for event in decoder.feed(chunk):
                    accumulator.handle_payload(event)
            for event in decoder.finish():
                accumulator.handle_payload(event)
            return SuccessfulRequest(measurement=accumulator.finish())
        except (
            OSError,
            http.client.HTTPException,
            UnicodeError,
            json.JSONDecodeError,
            RuntimeError,
        ) as error:
            failure = self._transport_failure(timer, error)
            self.close()
            return failure

    @staticmethod
    def _transport_failure(
        timer: StreamTimer,
        error: BaseException,
    ) -> FailedRequest:
        status = (
            "partial_stream"
            if timer.has_observed_first_token
            else "transport_error"
        )
        if isinstance(error, TimeoutError):
            error_type = "timeout"
        elif isinstance(error, (json.JSONDecodeError, UnicodeError, RuntimeError)):
            error_type = "stream_protocol"
        else:
            error_type = "transport"
        return FailedRequest(
            status=status,
            timing=timer.fail(),
            error_type=error_type,
            message=str(error),
        )
