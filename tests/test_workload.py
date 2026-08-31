import json
import threading
import time
import unittest
from contextlib import contextmanager
from typing import Iterator

from inference_lab.http_client import OpenAIHTTPClient
from inference_lab.metrics import RequestTiming
from inference_lab.openai_stream import StreamMeasurement
from inference_lab.outcomes import SuccessfulRequest
from inference_lab.workload import RequestExecutor, run_closed_loop
from tests.test_http_client import StreamingHandler, StreamingTestServer


def successful_request() -> SuccessfulRequest:
    return SuccessfulRequest(
        StreamMeasurement(
            text="ok",
            timing=RequestTiming(
                started_at_s=0.0,
                first_token_at_s=0.1,
                completed_at_s=0.2,
                output_tokens=2,
            ),
        )
    )


class ClosedLoopRunnerTests(unittest.TestCase):
    def test_waits_for_all_worker_contexts_before_submitting(self) -> None:
        lock = threading.Lock()
        created_workers = 0
        ready_workers = 0
        observed_ready_counts: list[int] = []

        @contextmanager
        def worker_factory() -> Iterator[RequestExecutor]:
            nonlocal created_workers, ready_workers
            with lock:
                worker_index = created_workers
                created_workers += 1
            if worker_index == 1:
                time.sleep(0.05)
            with lock:
                ready_workers += 1

            def execute(request_id: int) -> SuccessfulRequest:
                with lock:
                    observed_ready_counts.append(ready_workers)
                return successful_request()

            yield execute

        run_closed_loop(
            worker_factory,
            total_requests=2,
            concurrency=2,
        )

        self.assertEqual(observed_ready_counts, [2, 2])

    def test_bounds_concurrency_and_refills_completed_slots(self) -> None:
        lock = threading.Lock()
        first_wave = threading.Barrier(3)
        active_requests = 0
        maximum_active_requests = 0
        executed_ids: list[int] = []

        def execute(request_id: int) -> SuccessfulRequest:
            nonlocal active_requests, maximum_active_requests
            with lock:
                active_requests += 1
                maximum_active_requests = max(
                    maximum_active_requests,
                    active_requests,
                )
                executed_ids.append(request_id)
            if request_id < 3:
                first_wave.wait(timeout=1)
            time.sleep(0.005)
            with lock:
                active_requests -= 1
            return successful_request()

        @contextmanager
        def worker_factory() -> Iterator[RequestExecutor]:
            yield execute

        run = run_closed_loop(
            worker_factory,
            total_requests=7,
            concurrency=3,
        )

        self.assertEqual(maximum_active_requests, 3)
        self.assertEqual(sorted(executed_ids), list(range(7)))
        self.assertEqual([record.request_id for record in run.records], list(range(7)))
        self.assertTrue(
            all(
                record.submitted_at_s <= record.completed_at_s
                for record in run.records
            )
        )

    def test_aggregates_and_serializes_every_record(self) -> None:
        @contextmanager
        def worker_factory() -> Iterator[RequestExecutor]:
            yield lambda request_id: successful_request()

        run = run_closed_loop(
            worker_factory,
            total_requests=4,
            concurrency=2,
        )

        summary = run.summarize(ttft_slo_ms=500.0)
        serialized = run.as_dict()
        json.dumps(serialized)

        self.assertEqual(summary.submitted_requests, 4)
        self.assertEqual(summary.successful_requests, 4)
        self.assertEqual(len(serialized["records"]), 4)

    def test_propagates_worker_errors_instead_of_dropping_records(self) -> None:
        def execute(request_id: int) -> SuccessfulRequest:
            if request_id == 1:
                raise RuntimeError("request 1 failed outside the outcome model")
            return successful_request()

        @contextmanager
        def worker_factory() -> Iterator[RequestExecutor]:
            yield execute

        with self.assertRaisesRegex(RuntimeError, "request 1"):
            run_closed_loop(
                worker_factory,
                total_requests=3,
                concurrency=1,
            )

    def test_rejects_non_positive_concurrency(self) -> None:
        @contextmanager
        def worker_factory() -> Iterator[RequestExecutor]:
            yield lambda request_id: successful_request()

        with self.assertRaisesRegex(ValueError, "concurrency"):
            run_closed_loop(
                worker_factory,
                total_requests=1,
                concurrency=0,
            )


class ClosedLoopHTTPIntegrationTests(unittest.TestCase):
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

    def test_runs_concurrent_localhost_requests_with_one_client_per_worker(self) -> None:
        host, port = self.server.server_address

        @contextmanager
        def worker_factory() -> Iterator[RequestExecutor]:
            with OpenAIHTTPClient(host, port) as client:
                yield lambda request_id: client.measure(
                    {"model": "mock"},
                    path="/success",
                )

        run = run_closed_loop(
            worker_factory,
            total_requests=6,
            concurrency=3,
        )
        summary = run.summarize(ttft_slo_ms=500.0)

        self.assertEqual(len(run.records), 6)
        self.assertEqual(summary.successful_requests, 6)
        self.assertEqual(summary.failure_counts["transport_error"], 0)


if __name__ == "__main__":
    unittest.main()
