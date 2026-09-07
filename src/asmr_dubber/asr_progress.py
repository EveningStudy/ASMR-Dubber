"""Truthful liveness feedback while native model loading/decoding is blocking."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from contextvars import copy_context


@contextmanager
def model_heartbeat(
    progress: Callable[[str, int, int], None] | None, label: str, interval: float = 2.0
) -> Iterator[Callable[[str, int, int], None] | None]:
    if progress is None:
        yield None
        return
    stopped = threading.Event()
    guard = threading.Lock()
    state = [label, 0, 1]
    started = time.monotonic()

    def update(message: str, current: int, total: int) -> None:
        with guard:
            state[:] = [message, current, total]
            progress(message, current, total)

    def heartbeat() -> None:
        while not stopped.wait(interval):
            with guard, suppress(Exception):
                progress(
                    f"{state[0]} · 仍在处理，已运行 {time.monotonic() - started:.0f} 秒",
                    int(state[1]),
                    int(state[2]),
                )

    thread = threading.Thread(
        target=copy_context().run, args=(heartbeat,), daemon=True, name="asr-progress"
    )
    thread.start()
    try:
        update(label, 0, 1)
        yield update
    finally:
        stopped.set()
        thread.join(timeout=interval + 0.5)
