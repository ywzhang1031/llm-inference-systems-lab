from __future__ import annotations

import codecs


class SSEDecoder:
    """Incrementally decode Server-Sent Events from arbitrary byte chunks."""

    def __init__(self) -> None:
        self._utf8_decoder = codecs.getincrementaldecoder("utf-8")()
        self._text_buffer = ""
        self._data_lines: list[str] = []

    def feed(self, chunk: bytes) -> list[str]:
        self._text_buffer += self._utf8_decoder.decode(chunk)
        return self._drain_complete_lines()

    def finish(self) -> list[str]:
        self._text_buffer += self._utf8_decoder.decode(b"", final=True)
        events = self._drain_complete_lines()

        if self._text_buffer:
            event = self._process_line(self._text_buffer.removesuffix("\r"))
            self._text_buffer = ""
            if event is not None:
                events.append(event)

        event = self._dispatch_event()
        if event is not None:
            events.append(event)
        return events

    def _drain_complete_lines(self) -> list[str]:
        events: list[str] = []
        while "\n" in self._text_buffer:
            line, self._text_buffer = self._text_buffer.split("\n", 1)
            event = self._process_line(line.removesuffix("\r"))
            if event is not None:
                events.append(event)
        return events

    def _process_line(self, line: str) -> str | None:
        if not line:
            return self._dispatch_event()
        if line.startswith(":"):
            return None

        field, separator, value = line.partition(":")
        if field != "data":
            return None
        if separator and value.startswith(" "):
            value = value[1:]
        self._data_lines.append(value)
        return None

    def _dispatch_event(self) -> str | None:
        if not self._data_lines:
            return None
        payload = "\n".join(self._data_lines)
        self._data_lines.clear()
        return payload
