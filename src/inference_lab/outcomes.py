from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from .metrics import FailureTiming
from .openai_stream import StreamMeasurement


@dataclass(frozen=True, slots=True)
class SuccessfulRequest:
    measurement: StreamMeasurement

    @property
    def status(self) -> Literal["success"]:
        return "success"


@dataclass(frozen=True, slots=True)
class FailedRequest:
    status: Literal["http_error", "transport_error", "partial_stream"]
    timing: FailureTiming
    error_type: str
    message: str
    http_status: int | None = None


RequestOutcome: TypeAlias = SuccessfulRequest | FailedRequest
