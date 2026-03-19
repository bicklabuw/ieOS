# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Insect Eavesdropper OS (ieOS)** — a Python GUI framework running on a Raspberry Pi with a 128×64 SH1106 OLED display. Designed for audio recording and system configuration, with support for joystick/button/keyboard input.

## Running the Application

```bash
# Run on Raspberry Pi (hardware display + joystick input)
python3 ieOSMain.py

# Debug modes (for development on macOS/Linux desktop)
python3 ieOSMain.py -k   # keyboard input
python3 ieOSMain.py -s   # OS screen output
python3 ieOSMain.py -o   # keyboard + screen (most useful for dev)
```

Individual ViewControllers can be run standalone (each has `if __name__ == "__main__"`):
```bash
python3 ExampleController.py
python3 DateTimeViewController.py
python3 KeyboardViewController.py
```

## Installing Dependencies

```bash
pip install -r requirements.txt
```

Linux-only packages (`smbus`, `spidev`, `RPi.GPIO`, `lgpio`) are conditionally installed.

## Architecture

### Threading Model (3 threads)

1. **Render Thread** (`RenderThread.py`) — draws views to display at ~10 FPS; skips if no dirty flag
2. **Polling Thread** (`PollingThread.py`) — polls hardware/keyboard input every 50ms; dispatches events to the active ViewController
3. **VC Transition Thread** (`Main.py`) — processes the navigation stack queue (PUSH, SWAP, CLEAR, POP, POP_TO_ROOT); calls `on_appear()` / `on_disappear()` lifecycle hooks

### View System (`View.py`)

Views form a tree (parent/child via `add_subview()`). Key concepts:
- **Dirty flag** — set automatically when properties change; triggers re-render
- **Selectable** — views with `selectable=True` participate in joystick navigation
- **Event dispatch** — input events flow: ViewController → selected View → subview tree; return `True` to consume

Input handlers are named `on_<code>_<phase>` (e.g., `on_up_press`, `on_button_release(held)`). `RELEASE` handlers receive a `held: bool` argument.

### ViewController System (`ViewController.py`)

`ViewController[T]` is generic — the type parameter is the return value type. Navigation:

```python
# Pushing a child VC with a typed return callback
self.push_view_controller(SomeVC(), return_callback=self.handle_result)

# Popping with a return value (calls parent's return_callback)
self.pop_view_controller(return_value)

# Other transitions
self.change_view_controller(vc, ChangeViewControllerType.SWAP)
self.change_view_controller(vc, ChangeViewControllerType.CLEAR)
```

Override `on_appear()` for initialization that needs the display (runs in VC transition thread). Override `handle_override()` methods via `on_<code>_<phase>` naming to intercept input before it reaches the selected view.

### SelectionManager (`SelectionManager.py`)

Manages which view is "selected" and handles directional navigation:
- `move(Direction)` — finds nearest selectable view in that direction (proximity-based, wraps if `wrap=True`)
- `drill_in()` / `exit()` — enter/exit nested selection hierarchies (e.g., pressing BUTTON on a container)
- `select(view)` — direct selection

### Key Constants (`OSGlobals.py`)

- `FRAME_TIME = 0.1s` — render frequency
- `POLLING_SLEEP_TIME = 0.05s` — input poll frequency
- `KEY_INIT_CHG_WAIT_TIME = 0.5s` — hold detection threshold

### Display (`Display.py`, `SH1106.py`)

- Resolution: 128×64, monochrome
- `Display.ON = 0` (black), `Display.OFF = 1` (white) — inverted convention
- Text: `CHAR_HEIGHT = 9px`, `LINE_HEIGHT = 10px`, default PIL font

## Creating a New ViewController

1. Subclass `ViewController[ReturnType]`
2. In `__init__`, build your view hierarchy and call `self.present_view(self.view)` (or add subviews to `self.view`)
3. Override `on_appear()` for async initialization
4. Use `push_view_controller(vc, return_callback=fn)` to navigate forward
5. Call `pop_view_controller(value)` to return to parent

See `ExampleController.py` for a minimal working example.

## Input Codes

```python
# InputUtils.py
InputCode: UP, DOWN, LEFT, RIGHT, BUTTON, KEY1, KEY2, KEY3
InputPhase: PRESS, HOLD, RELEASE
```

Hardware pins are defined in `config.py`.
