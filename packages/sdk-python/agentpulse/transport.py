"""HTTP transport for sending telemetry to the collector."""

from __future__ import annotations

import json
import logging
import threading
from collections import deque
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger("agentpulse")


class Transport:
    """Batched HTTP transport with background flushing.

    Accumulates events and flushes them in batches to minimize overhead.
    Uses only stdlib (urllib) to maintain zero-dependency constraint.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        flush_interval: float = 2.0,
        batch_size: int = 50,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._flush_interval = flush_interval
        self._batch_size = batch_size
        self._trace_queue: deque[dict[str, Any]] = deque()
        self._span_queue: deque[dict[str, Any]] = deque()
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._closed = False
        self._start_flush_timer()

    def _start_flush_timer(self) -> None:
        if self._closed:
            return
        self._timer = threading.Timer(self._flush_interval, self._flush_loop)
        self._timer.daemon = True
        self._timer.start()

    def _flush_loop(self) -> None:
        self.flush()
        self._start_flush_timer()

    def send_trace(self, trace_data: dict[str, Any]) -> None:
        with self._lock:
            self._trace_queue.append(trace_data)
            if len(self._trace_queue) >= self._batch_size:
                self._flush_traces()

    def send_span(self, span_data: dict[str, Any]) -> None:
        with self._lock:
            self._span_queue.append(span_data)
            if len(self._span_queue) >= self._batch_size:
                self._flush_spans()

    def flush(self) -> None:
        with self._lock:
            self._flush_traces()
            self._flush_spans()

    def _flush_traces(self) -> None:
        if not self._trace_queue:
            return
        batch = list(self._trace_queue)
        self._trace_queue.clear()
        self._post(f"{self._endpoint}/v1/traces", batch)

    def _flush_spans(self) -> None:
        if not self._span_queue:
            return
        batch = list(self._span_queue)
        self._span_queue.clear()
        self._post(f"{self._endpoint}/v1/spans", batch)

    def _post(self, url: str, payload: list[dict[str, Any]]) -> None:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-AgentPulse-Key"] = self._api_key

        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=10) as resp:
                resp.read()
        except (URLError, OSError) as exc:
            logger.warning("AgentPulse: failed to send telemetry to %s: %s", url, exc)

    def close(self) -> None:
        self._closed = True
        if self._timer:
            self._timer.cancel()
        self.flush()
