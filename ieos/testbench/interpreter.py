# ieos/testbench/interpreter.py
from __future__ import annotations

import logging
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gui.core.Main as Main
from gui.core import testbench_input
from gui.core.OSGlobals import request_process_exit
from gui.core.testbench_input import TestbenchEvent
from gui.utils.durable_io import write_json_atomic
from gui.utils.InputUtils import InputCode, InputPhase
from gui.utils.recording_format import count_usb_input_mics
from gui.utils.usb.USBDriveManager import ensure_recordings_ready, get_recordings_path
from ieos.testbench.macros import expand_steps
from ieos.version import APP_VERSION

_log = logging.getLogger(__name__)

_CODE_BY_NAME = {c.name: c for c in InputCode}

_DEFAULT_REPORT_PATH = "/tmp/ieos_testbench_report.json"


@dataclass(frozen=True)
class TestbenchRunResult:
    success: bool
    message: str
    step_results: list[dict[str, Any]]
    scenario_sources: list[str]
    time_scale: float
    report_path: str
    exit_code: int


def _scaled(sec: float, scale: float) -> float:
    return max(0.0, float(sec) * float(scale))


def _tap(code_name: str, scale: float) -> None:
    code = _CODE_BY_NAME[code_name]
    testbench_input.enqueue(TestbenchEvent(code, InputPhase.PRESS))
    time.sleep(max(0.06, 0.08 * max(scale, 0.05)))
    testbench_input.enqueue(TestbenchEvent(code, InputPhase.RELEASE, False))
    time.sleep(max(0.06, 0.08 * max(scale, 0.05)))


def _run_wait(seconds_nominal: float, scale: float, *, step_id: str) -> None:
    total = _scaled(seconds_nominal, scale)
    _log.info(
        "testbench wait[%s]: %.1fs wall (nominal=%.1fs, scale=%s)",
        step_id,
        total,
        seconds_nominal,
        scale,
    )
    if total <= 0:
        return
    # Long nominal waits (default catalog idles) look like a hang without heartbeats.
    heartbeat = 30.0 if total > 90 else total
    elapsed = 0.0
    while elapsed < total:
        chunk = min(heartbeat, total - elapsed)
        time.sleep(chunk)
        elapsed += chunk
        if elapsed < total and total > 90:
            _log.info(
                "testbench wait[%s]: progress %.0fs / %.0fs (%.0f%%)",
                step_id,
                elapsed,
                total,
                100.0 * elapsed / total,
            )


def _run_wait_for_vc(class_name: str, timeout_sec: float, scale: float) -> None:
    deadline = time.monotonic() + max(0.5, _scaled(timeout_sec, scale))
    while time.monotonic() < deadline:
        stack = Main.get_view_controller_stack_names()
        if stack and stack[-1] == class_name:
            return
        time.sleep(0.05)
    stack = Main.get_view_controller_stack_names()
    raise AssertionError(f"expected top VC {class_name!r}, stack={stack!r}")


def _run_assert_vc_top(class_name: str) -> None:
    stack = Main.get_view_controller_stack_names()
    if not stack or stack[-1] != class_name:
        raise AssertionError(f"assert_vc_top wanted {class_name!r}, stack={stack!r}")


def _run_assert_stack_depth(depth: int) -> None:
    stack = Main.get_view_controller_stack_names()
    if len(stack) != depth:
        raise AssertionError(f"assert_stack_depth wanted {depth}, got {len(stack)}: {stack!r}")


def _run_preflight_usb_mics() -> None:
    ensure_recordings_ready()
    if count_usb_input_mics() <= 0:
        raise AssertionError("preflight: no USB input mics detected")


def _run_assert_glob_min(pattern: str, min_count: int) -> None:
    # RecordViewController unmounts the pendrive after a session; remount before globbing WAVs.
    ensure_recordings_ready()
    root = Path(get_recordings_path())
    n = len(list(root.glob(pattern)))
    if n < min_count:
        raise AssertionError(f"assert_glob_min {pattern!r}: need >= {min_count}, got {n}")


def _run_mic_confirm_go(max_wait_sec: float, scale: float) -> None:
    """MicTestViewController (show_go): GO is KEY1 per on-screen hint "K1=GO"; see on_key1_press.

    Streams may open slowly; KEY1 is ignored until at least one mic is enabled.
    """
    deadline = time.monotonic() + max(3.0, _scaled(max_wait_sec, scale))
    time.sleep(_scaled(4.0, scale))
    while time.monotonic() < deadline:
        stack = Main.get_view_controller_stack_names()
        if stack and stack[-1] == "RecordViewController":
            _log.info("testbench: mic check finished, top VC is RecordViewController")
            return
        if stack and stack[-1] == "MicTestViewController":
            _tap("KEY1", scale)
            time.sleep(_scaled(2.5, scale))
        else:
            time.sleep(0.08)
    stack = Main.get_view_controller_stack_names()
    raise AssertionError(
        f"mic_confirm_go: RecordViewController not reached within {max_wait_sec}s (stack={stack!r})"
    )


def _write_report(
    *,
    success: bool,
    message: str,
    step_results: list[dict[str, Any]],
    scenario_sources: list[str],
    time_scale: float,
    report_path: str | None,
) -> str:
    path = Path(report_path or os.environ.get("IEOS_TESTBENCH_REPORT_PATH", "") or _DEFAULT_REPORT_PATH)
    payload = {
        "success": success,
        "message": message,
        "hostname": socket.gethostname(),
        "app_version": APP_VERSION,
        "time_scale": time_scale,
        "scenario_sources": scenario_sources,
        "steps": step_results,
        "finished": True,
    }
    write_json_atomic(path, payload)
    _log.info("testbench report written: %s", path)
    return str(path)


def _finish_run(
    *,
    success: bool,
    message: str,
    step_results: list[dict[str, Any]],
    scenario_sources: list[str],
    time_scale: float,
    report_path: str | None,
    exit_on_finish: bool,
) -> TestbenchRunResult:
    written_report_path = _write_report(
        success=success,
        message=message,
        step_results=step_results,
        scenario_sources=scenario_sources,
        time_scale=time_scale,
        report_path=report_path,
    )
    code = 0 if success else 1
    if exit_on_finish:
        _log.info(
            "testbench finished (success=%s); requesting process exit with code %s",
            success,
            code,
        )
        request_process_exit(code)
    else:
        _log.info("testbench finished (success=%s); returning result", success)
    return TestbenchRunResult(
        success=success,
        message=message,
        step_results=step_results,
        scenario_sources=list(scenario_sources),
        time_scale=time_scale,
        report_path=written_report_path,
        exit_code=code,
    )


def abort_with_report(
    step_results: list[dict[str, Any]],
    *,
    success: bool,
    message: str,
    scenario_sources: list[str] | None = None,
    time_scale: float = 1.0,
    report_path: str | None = None,
    exit_on_finish: bool = True,
) -> TestbenchRunResult:
    return _finish_run(
        success=success,
        message=message,
        step_results=step_results,
        scenario_sources=list(scenario_sources or []),
        time_scale=time_scale,
        report_path=report_path,
        exit_on_finish=exit_on_finish,
    )


def run_steps(
    steps: list[dict[str, Any]],
    *,
    time_scale: float,
    scenario_sources: list[str],
    report_path: str | None,
    exit_on_finish: bool = True,
) -> TestbenchRunResult:
    step_results: list[dict[str, Any]] = []
    message = "ok"
    success = True
    try:
        expanded = expand_steps(steps)
    except Exception as e:
        _log.exception("testbench expand failed")
        return abort_with_report(
            [],
            success=False,
            message=f"expand failed: {e}",
            scenario_sources=scenario_sources,
            time_scale=time_scale,
            report_path=report_path,
            exit_on_finish=exit_on_finish,
        )

    for i, raw in enumerate(expanded):
        sid = raw.get("id", f"step_{i}")
        stype = raw.get("type")
        t0 = time.time()
        err: str | None = None
        try:
            if stype == "wait":
                _run_wait(float(raw["seconds"]), time_scale, step_id=str(sid))
            elif stype == "tap":
                _tap(str(raw["code"]), time_scale)
            elif stype == "wait_for_vc":
                _run_wait_for_vc(str(raw["class"]), float(raw.get("timeout_sec", 30)), time_scale)
            elif stype == "assert_vc_top":
                _run_assert_vc_top(str(raw["class"]))
            elif stype == "assert_stack_depth":
                _run_assert_stack_depth(int(raw["depth"]))
            elif stype == "preflight_usb_mics":
                _run_preflight_usb_mics()
            elif stype == "assert_glob_min":
                _run_assert_glob_min(str(raw["pattern"]), int(raw["min"]))
            elif stype == "log":
                _log.info("testbench log[%s]: %s", sid, raw.get("text", ""))
            elif stype == "mic_confirm_go":
                _run_mic_confirm_go(float(raw.get("max_wait_sec", 90)), time_scale)
            else:
                raise ValueError(f"unknown step type: {stype!r}")
        except Exception as e:
            err = str(e)
            _log.error("testbench step %s failed: %s", sid, e)
            success = False
            message = f"step {sid}: {err}"
            step_results.append(
                {
                    "id": sid,
                    "type": stype,
                    "ok": False,
                    "error": err,
                    "elapsed_ms": int((time.time() - t0) * 1000),
                }
            )
            break

        step_results.append(
            {
                "id": sid,
                "type": stype,
                "ok": True,
                "error": None,
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        )

    return _finish_run(
        success=success,
        message=message,
        step_results=step_results,
        scenario_sources=scenario_sources,
        time_scale=time_scale,
        report_path=report_path,
        exit_on_finish=exit_on_finish,
    )
