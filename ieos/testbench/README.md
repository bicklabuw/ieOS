# ieOS autonomous testbench

Scenario-driven UI exercise for a Raspberry Pi with OLED, USB pendrive (`/WAV`), and USB microphones. Input is **synthetic** (queued events drained from the polling thread); GPIO and keyboard polling are disabled so scripts are deterministic.

## Run

From the repository root:

```bash
python3 -m ieos.ieOSMain --testbench
```

Always pass `--testbench` so `Main` disables joystick/keyboard polling and enables the synthetic queue.

## Environment

| Variable | Meaning |
|----------|---------|
| `IEOS_TESTBENCH_SCENARIOS` | Comma-separated paths to JSON scenario files (default: `default.json` or `quick.json` when quick mode is on) |
| `IEOS_TESTBENCH_QUICK` | If `1`, `true`, or `yes`, default scenario is **`scenarios/quick.json`** (~few minutes: one short recording, no long idles). Otherwise **`default.json`** (~1 hour nominal with 10-minute idle gaps). |
| `IEOS_TESTBENCH_TIME_SCALE` | Multiply all `wait` and `wait_for_vc` timeouts by this factor (e.g. `0.1` shrinks sleeps; does not shorten real recording countdowns inside `RecordViewController`) |
| `IEOS_TESTBENCH_REPORT_PATH` | JSON report output path (default: `/tmp/ieos_testbench_report.json`) |

## Scenario JSON

Top-level object: `name`, optional `description`, and `steps` (array).

Step types:

- `wait` — `seconds` (nominal; scaled by `IEOS_TESTBENCH_TIME_SCALE`)
- `tap` — `code`: `BUTTON`, `KEY1`, `KEY2`, `KEY3`, `UP`, `DOWN`, `LEFT`, `RIGHT`
- `wait_for_vc` — `class` (top ViewController class name), `timeout_sec`
- `assert_vc_top`, `assert_stack_depth`
- `preflight_usb_mics` — `ensure_recordings_ready()` and at least one USB input mic
- `assert_glob_min` — `pattern` (glob under recordings root), `min` count. Calls `ensure_recordings_ready()` first because `RecordViewController` unmounts the USB after each recording.
- `log` — `text` (info log only)
- `macro` — `name` (see `ieos/testbench/macros.py`)
- `mic_confirm_go` — optional `max_wait_sec` (default 90). After `MicTestViewController` appears (record flow, `show_go=True`), waits for streams then retries **KEY1** (GO; see mic screen hint `K1=GO`) until `RecordViewController` is on top.

Record-flow macros in `macros.py` follow the live UI: **`RecordSetupViewController`** confirms duration with **BUTTON** (not KEY3); finer −1 min taps use **KEY3**. **`MicTestViewController`** GO is **KEY1** when `show_go=True`.

## Default catalog

`scenarios/default.json` targets roughly **60 minutes** of nominal waits and two **10-minute** recordings (default duration on the setup screen) before time scaling.

## Exit code

The process exits with `0` on success and `1` on failure after writing the report.
