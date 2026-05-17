from __future__ import annotations

import logging
import time
from contextlib import contextmanager


log = logging.getLogger(__name__)


@contextmanager
def timed_operation(name: str):
    started = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000
        log.info("Timing: %s %.1f ms", name, elapsed_ms)
