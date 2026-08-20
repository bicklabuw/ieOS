# ieos/testbench/runner.py
from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import gui.core.Main as Main
from gui.core.OSGlobals import set_runtime_testbench_input_enabled
from gui.core import testbench_input
from ieos.testbench import report_storage

if TYPE_CHECKING:
    from ieos.testbench import interpreter

_log = logging.getLogger(__name__)

_ENV_SCENARIOS = "IEOS_TESTBENCH_SCENARIOS"
_ENV_TIME_SCALE = "IEOS_TESTBENCH_TIME_SCALE"
_ENV_REPORT = "IEOS_TESTBENCH_REPORT_PATH"
_ENV_QUICK = "IEOS_TESTBENCH_QUICK"
_TMP_REPORT_DIR = Path("/tmp")


@dataclass(frozen=True)
class SettingsTestbenchResult:
    mode: str
    run_result: "interpreter.TestbenchRunResult"
    usb_report_result: report_storage.UsbReportResult


def scenario_path_for_mode(mode: str) -> Path:
    base = Path(__file__).resolve().parent / "scenarios"
    if mode == "quick":
        return base / "quick.json"
    if mode == "long":
        return base / "default.json"
    raise ValueError(f"unknown testbench mode: {mode!r}")


def _default_scenario_filenames() -> tuple[str, ...]:
    q = os.environ.get(_ENV_QUICK, "").strip().lower()
    if q in ("1", "true", "yes", "on"):
        return ("quick.json",)
    return ("default.json",)


def _scenario_paths() -> list[Path]:
    raw = os.environ.get(_ENV_SCENARIOS, "").strip()
    if raw:
        paths: list[Path] = []
        for part in raw.split(","):
            p = part.strip()
            if p:
                paths.append(Path(p).expanduser())
        return paths
    base = Path(__file__).resolve().parent / "scenarios"
    return [base / name for name in _default_scenario_filenames()]


def _load_all_steps() -> tuple[list[dict], list[str]]:
    steps: list[dict] = []
    sources: list[str] = []
    for path in _scenario_paths():
        if not path.is_file():
            _log.error("testbench scenario file missing: %s", path)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("name", path.stem)
        part = data.get("steps", [])
        if not isinstance(part, list):
            _log.error("scenario %s: steps must be a list", path)
            continue
        _log.info("loaded scenario %r (%s) with %d steps", name, path, len(part))
        if path.name == "default.json" and _default_scenario_filenames() == ("default.json",):
            _log.warning(
                "testbench: default.json can take ~an hour wall time (long idles + long recordings); "
                "set IEOS_TESTBENCH_QUICK=1 or IEOS_TESTBENCH_SCENARIOS=... quick.json "
                "or shorten with IEOS_TESTBENCH_TIME_SCALE"
            )
        sources.append(str(path))
        for i, step in enumerate(part):
            if isinstance(step, dict):
                step = dict(step)
                step.setdefault("_file", str(path))
                step.setdefault("_index", i)
                steps.append(step)
    return steps, sources


def _load_steps_from_paths(paths: list[Path]) -> tuple[list[dict], list[str]]:
    steps: list[dict] = []
    sources: list[str] = []
    for path in paths:
        if not path.is_file():
            _log.error("testbench scenario file missing: %s", path)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("name", path.stem)
        part = data.get("steps", [])
        if not isinstance(part, list):
            _log.error("scenario %s: steps must be a list", path)
            continue
        _log.info("loaded scenario %r (%s) with %d steps", name, path, len(part))
        sources.append(str(path))
        for i, step in enumerate(part):
            if isinstance(step, dict):
                step = dict(step)
                step.setdefault("_file", str(path))
                step.setdefault("_index", i)
                steps.append(step)
    return steps, sources


def load_steps_for_mode(mode: str) -> tuple[list[dict], list[str]]:
    return _load_steps_from_paths([scenario_path_for_mode(mode)])


def _local_report_path(mode: str) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return str(_TMP_REPORT_DIR / f"ieos-testbench-{mode}-{ts}.json")


def _wait_until_main_menu(timeout: float = 30.0, poll: float = 0.05) -> bool:
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        stack = Main.get_view_controller_stack_names()
        if stack == ["MainMenuViewController"]:
            return True
        time.sleep(poll)
    return False


def _thread_main() -> None:
    from ieos.testbench import interpreter

    if not _wait_until_main_menu():
        _log.error("testbench: main menu not reached in time")
        interpreter.abort_with_report([], success=False, message="main menu timeout")
        return
    steps, sources = _load_all_steps()
    if not steps:
        _log.error("testbench: no steps loaded")
        interpreter.abort_with_report([], success=False, message="no steps loaded")
        return
    scale = float(os.environ.get(_ENV_TIME_SCALE, "1") or "1")
    report_path = os.environ.get(_ENV_REPORT, "").strip() or None
    interpreter.run_steps(steps, time_scale=scale, scenario_sources=sources, report_path=report_path)


def start_when_main_menu_ready() -> None:
    t = threading.Thread(target=_thread_main, name="ieos-testbench", daemon=True)
    t.start()


def _settings_thread_main(
    *,
    mode: str,
    completion: Callable[[SettingsTestbenchResult], None],
    time_scale: float = 1.0,
) -> None:
    from ieos.testbench import interpreter

    report_path = _local_report_path(mode)
    set_runtime_testbench_input_enabled(True)
    testbench_input.clear()
    try:
        if not _wait_until_main_menu():
            run_result = interpreter.abort_with_report(
                [],
                success=False,
                message="main menu timeout",
                scenario_sources=[],
                time_scale=time_scale,
                report_path=report_path,
                exit_on_finish=False,
            )
        else:
            steps, sources = load_steps_for_mode(mode)
            if not steps:
                run_result = interpreter.abort_with_report(
                    [],
                    success=False,
                    message="no steps loaded",
                    scenario_sources=sources,
                    time_scale=time_scale,
                    report_path=report_path,
                    exit_on_finish=False,
                )
            else:
                run_result = interpreter.run_steps(
                    steps,
                    time_scale=time_scale,
                    scenario_sources=sources,
                    report_path=report_path,
                    exit_on_finish=False,
                )
    finally:
        testbench_input.clear()
        set_runtime_testbench_input_enabled(False)

    usb_result = report_storage.copy_report_to_usb(run_result.report_path, mode)
    completion(
        SettingsTestbenchResult(
            mode=mode,
            run_result=run_result,
            usb_report_result=usb_result,
        )
    )


def start_settings_run(
    mode: str,
    completion: Callable[[SettingsTestbenchResult], None],
    *,
    time_scale: float = 1.0,
) -> None:
    t = threading.Thread(
        target=_settings_thread_main,
        kwargs={"mode": mode, "completion": completion, "time_scale": time_scale},
        name=f"ieos-settings-testbench-{mode}",
        daemon=True,
    )
    t.start()
