from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from threading import Barrier, BrokenBarrierError, Event, Lock, Thread
from time import perf_counter
from typing import Callable, TypeAlias

from .aggregation import BenchmarkSummary, aggregate_outcomes
from .outcomes import FailedRequest, RequestOutcome, SuccessfulRequest


RequestExecutor: TypeAlias = Callable[[int], RequestOutcome]
WorkerFactory: TypeAlias = Callable[
    [],
    AbstractContextManager[RequestExecutor],
]


@dataclass(frozen=True, slots=True)
class RequestRecord:
    request_id: int
    submitted_at_s: float
    completed_at_s: float
    outcome: RequestOutcome

    def __post_init__(self) -> None:
        if self.submitted_at_s > self.completed_at_s:
            raise ValueError("request completion preceded submission")

    @property
    def client_latency_ms(self) -> float:
        return (self.completed_at_s - self.submitted_at_s) * 1_000

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "submitted_at_s": self.submitted_at_s,
            "completed_at_s": self.completed_at_s,
            "client_latency_ms": self.client_latency_ms,
            "outcome": _outcome_as_dict(self.outcome),
        }


@dataclass(frozen=True, slots=True)
class WorkloadRun:
    records: tuple[RequestRecord, ...]

    @property
    def started_at_s(self) -> float:
        return min(record.submitted_at_s for record in self.records)

    @property
    def completed_at_s(self) -> float:
        return max(record.completed_at_s for record in self.records)

    @property
    def duration_s(self) -> float:
        return self.completed_at_s - self.started_at_s

    def summarize(self, *, ttft_slo_ms: float) -> BenchmarkSummary:
        return aggregate_outcomes(
            (record.outcome for record in self.records),
            duration_s=self.duration_s,
            ttft_slo_ms=ttft_slo_ms,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "started_at_s": self.started_at_s,
            "completed_at_s": self.completed_at_s,
            "duration_s": self.duration_s,
            "records": [record.as_dict() for record in self.records],
        }


def run_closed_loop(
    worker_factory: WorkerFactory,
    *,
    total_requests: int,
    concurrency: int,
    clock: Callable[[], float] = perf_counter,
) -> WorkloadRun:
    if total_requests < 1:
        raise ValueError("total_requests must be at least 1")
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")

    next_request_id = 0
    records: list[RequestRecord | None] = [None] * total_requests
    worker_errors: list[Exception] = []
    state_lock = Lock()
    stop = Event()
    start = Event()
    worker_count = min(concurrency, total_requests)
    ready = Barrier(worker_count + 1)

    def worker() -> None:
        nonlocal next_request_id
        try:
            with worker_factory() as execute:
                ready.wait()
                start.wait()
                while not stop.is_set():
                    with state_lock:
                        if next_request_id >= total_requests:
                            return
                        request_id = next_request_id
                        next_request_id += 1

                    submitted_at_s = clock()
                    outcome = execute(request_id)
                    completed_at_s = clock()
                    records[request_id] = RequestRecord(
                        request_id=request_id,
                        submitted_at_s=submitted_at_s,
                        completed_at_s=completed_at_s,
                        outcome=outcome,
                    )
        except BrokenBarrierError:
            return
        except Exception as error:
            with state_lock:
                worker_errors.append(error)
            stop.set()
            ready.abort()
            start.set()

    workers = [
        Thread(target=worker, name=f"inference-worker-{index}")
        for index in range(worker_count)
    ]
    for thread in workers:
        thread.start()
    try:
        ready.wait()
    except BrokenBarrierError:
        pass
    start.set()
    for thread in workers:
        thread.join()

    if worker_errors:
        raise worker_errors[0]

    completed_records = tuple(record for record in records if record is not None)
    if len(completed_records) != total_requests:
        raise RuntimeError("closed-loop run completed with missing request records")
    return WorkloadRun(records=completed_records)


def _outcome_as_dict(outcome: RequestOutcome) -> dict[str, object]:
    if isinstance(outcome, SuccessfulRequest):
        timing = outcome.measurement.timing
        return {
            "status": outcome.status,
            "text": outcome.measurement.text,
            "timing": {
                "started_at_s": timing.started_at_s,
                "first_token_at_s": timing.first_token_at_s,
                "completed_at_s": timing.completed_at_s,
                **timing.as_dict(),
            },
        }

    if isinstance(outcome, FailedRequest):
        timing = outcome.timing
        return {
            "status": outcome.status,
            "error_type": outcome.error_type,
            "message": outcome.message,
            "http_status": outcome.http_status,
            "timing": {
                "started_at_s": timing.started_at_s,
                "first_token_at_s": timing.first_token_at_s,
                "failed_at_s": timing.failed_at_s,
                "observed_ttft_ms": timing.observed_ttft_ms,
                "time_to_failure_ms": timing.time_to_failure_ms,
            },
        }

    raise TypeError(f"unsupported request outcome: {type(outcome).__name__}")
