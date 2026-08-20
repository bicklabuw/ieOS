# gui/core/testbench_input.py
"""Thread-safe queue of synthetic input events for autonomous testbench runs.

``ieos.ieOSMain --testbench`` turns off GPIO and keyboard polling (see
``gui/core/Main.py``); only this queue feeds ``ViewController.on_event``. That
path does not generate automatic hold-repeat: the interpreter emits explicit
``PRESS``/``RELEASE`` pairs (see ``ieos/testbench/interpreter.py`` ``_tap``), so
hold-repeat logic in ``PollingThread`` never competes with synthetic taps.
"""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue

from gui.utils.InputUtils import InputCode, InputPhase


@dataclass(frozen=True)
class TestbenchEvent:
    code: InputCode
    phase: InputPhase
    held: bool = False


_queue: Queue[TestbenchEvent] = Queue()


def enqueue(event: TestbenchEvent) -> None:
    _queue.put(event)


def clear() -> None:
    while True:
        try:
            _queue.get_nowait()
        except Empty:
            return


def drain_queue_to(vc) -> None:
    """Deliver at most one synthetic event per poll so PRESS/RELEASE split across ticks."""
    try:
        ev = _queue.get_nowait()
    except Empty:
        return
    vc.on_event(ev.code, ev.phase, ev.held)
