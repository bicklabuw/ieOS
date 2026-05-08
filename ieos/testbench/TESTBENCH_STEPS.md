# ieOS Testbench Steps

This document explains the autonomous testbenches available from **Settings > Run testbench**.

Both runs require a writable USB drive and at least one USB input microphone. When launched from Settings, ieOS temporarily takes over input with synthetic button presses, saves a JSON report to the USB drive under `testbench-reports/`, shows pass/fail status, and reboots.

## Quick Testbench

Scenario file: `ieos/testbench/scenarios/quick.json`

Expected duration: a few minutes, mostly driven by one short recording flow.


| Step             | What it does                                                                                                                                             | What it proves                                                                        |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `preflight`      | Mounts USB storage, prepares `/WAV`, and checks for at least one USB input microphone.                                                                   | Recording hardware and storage are available before UI automation starts.             |
| `main_ready`     | Waits until the main menu is the active screen.                                                                                                          | The app is at the expected starting point.                                            |
| `cancel_at_name` | Opens Record, reaches the recording name keyboard, then backs out with KEY2.                                                                             | The record entry path opens correctly and cancellation returns to the main menu.      |
| `record_short`   | Opens Record again, enters a short name, chooses a 60-second-class duration, confirms mics, waits for recording to finish, and returns to the main menu. | The core record flow can create a short recording from name entry through completion. |
| `have_wav`       | Remounts/checks the USB recordings directory and asserts at least one `.wav` file exists.                                                                | A recording was actually written to the USB drive.                                    |
| `done_log`       | Writes a final log marker.                                                                                                                               | The scenario reached the end cleanly.                                                 |


## Long Testbench

Scenario file: `ieos/testbench/scenarios/default.json`

Expected duration: about one hour nominal, including long idle waits and two longer recordings.


| Step             | What it does                                                                                        | What it proves                                                         |
| ---------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `preflight`      | Mounts USB storage, prepares `/WAV`, and checks for at least one USB input microphone.              | Recording hardware and storage are available.                          |
| `main_ready`     | Waits for the main menu.                                                                            | The app begins from the expected screen.                               |
| `cancel_at_name` | Opens Record, reaches the recording name keyboard, then cancels.                                    | Record setup navigation and cancellation still work after startup.     |
| `record_short`   | Performs the short recording flow used by the quick testbench.                                      | The basic recording path works before longer soak steps begin.         |
| `have_wav`       | Confirms at least one `.wav` exists on USB.                                                         | The first recording produced a file.                                   |
| `idle_1`         | Waits for 10 minutes nominal.                                                                       | The app remains stable while idle between operations.                  |
| `long_record_a`  | Performs a default-duration recording flow.                                                         | A longer recording can run and return to the main menu.                |
| `idle_2`         | Waits for another 10 minutes nominal.                                                               | The app remains stable after a long recording.                         |
| `play_listen`    | Opens Play, enters the listen file selector, then backs out.                                        | Playback/listen navigation can read available recordings and return.   |
| `mic_visit`      | Opens Mic Test, waits briefly, then backs out.                                                      | Mic test screen can initialize and exit outside the record flow.       |
| `files_browse`   | Opens Files, enters the recordings browser, then backs out.                                         | File browsing can access recordings and return through menus.          |
| `settings`       | Opens Settings, visits Scheduled Recordings, visits Update from USB, then returns to the main menu. | Settings submenus can be entered and exited during the soak run.       |
| `idle_3`         | Waits for another 10 minutes nominal.                                                               | The app remains stable after broader menu navigation.                  |
| `long_record_b`  | Performs a second default-duration recording flow.                                                  | Recording still works late in the run after idle and navigation steps. |
| `tail`           | Waits for two minutes nominal.                                                                      | Final idle soak after the last recording.                              |
| `done_log`       | Writes a final log marker.                                                                          | The scenario reached the end cleanly.                                  |


## Macro Details

The scenario files use macros from `ieos/testbench/macros.py` to keep the JSON readable.


| Macro                          | Expanded behavior                                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `main_menu_open_record`        | Presses BUTTON on the main menu Record row.                                                                              |
| `keyboard_name_a_go`           | Enters a short recording name using the keyboard screen and confirms it.                                                 |
| `record_setup_60_seconds`      | Taps KEY3 repeatedly to reduce duration, then confirms with BUTTON.                                                      |
| `record_setup_default_confirm` | Confirms the default recording duration with BUTTON.                                                                     |
| `back_key2`                    | Presses KEY2 to go back.                                                                                                 |
| `cancel_record_at_keyboard`    | Opens Record, waits for the keyboard, presses KEY2, and waits for the main menu.                                         |
| `record_flow_60`               | Runs the full short recording path: Record, keyboard name, duration, mic confirmation, recording wait, main menu return. |
| `record_flow_600_default`      | Runs the full default-duration recording path.                                                                           |
| `play_listen_flow`             | Opens Play, enters Listen, backs out to Play, then returns to the main menu.                                             |
| `mic_test_visit`               | Opens Mic Test, waits briefly, then returns to the main menu.                                                            |
| `files_browse_flow`            | Opens Files, enters the recordings browser, backs out to Files, then returns to the main menu.                           |
| `settings_tour`                | Opens Settings, visits Scheduled Recordings and Update from USB, then returns to the main menu.                          |


## Step Types


| Type                 | Meaning                                                                                               |
| -------------------- | ----------------------------------------------------------------------------------------------------- |
| `wait`               | Sleeps for the requested nominal seconds, scaled by `IEOS_TESTBENCH_TIME_SCALE` in CLI runs.          |
| `tap`                | Sends a synthetic PRESS and RELEASE for one input code.                                               |
| `wait_for_vc`        | Waits until the named ViewController is at the top of the navigation stack.                           |
| `assert_vc_top`      | Fails if the named ViewController is not currently on top.                                            |
| `assert_stack_depth` | Fails if the navigation stack depth is unexpected.                                                    |
| `preflight_usb_mics` | Ensures USB recording storage is writable and at least one USB mic is detected.                       |
| `assert_glob_min`    | Checks that at least a minimum number of files match a glob in the USB recordings folder.             |
| `log`                | Writes an informational marker to the testbench log.                                                  |
| `macro`              | Expands to a named sequence from `macros.py`.                                                         |
| `mic_confirm_go`     | Waits for the mic screen to become ready, retries KEY1 GO, and confirms the record screen is reached. |
