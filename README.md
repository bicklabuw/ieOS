# ieos-gui

Python GUI framework for **Insect Eavesdropper OS (ieOS)**:

This PyPI distribution is named `**ieos-gui`**; the importable Python package is `**gui**`.

```bash
pip install ieos-gui
```

```python
from gui.ui_core.ViewController import ViewController
```

## Raspberry Pi hardware

For SPI/I2C display and GPIO (install on Linux, typically a Raspberry Pi):

```bash
pip install ieos-gui[rpi]
```

## Full ieOS application

The end-user application that uses this framework lives in the same repository under the `ieos` package and is not installed by `ieos-gui` alone. Clone the repo and run from the project root if you need the full app.

### Full ieOS on Raspberry Pi

On a fresh Raspberry Pi OS machine, from a clone of the repo:

1. Enable SPI (`sudo raspi-config` → Interface Options → SPI) and reboot if needed.
2. From the repository root, as your normal user: `bash scripts/pi-bootstrap.sh` (installs apt packages, creates `.venv`, runs `pip install -e ".[rpi]"`).
3. Once: `sudo bash scripts/pi-sudo-setup.sh` (passwordless sudo for USB/time features and optional `@reboot` launch).
4. Run `./ie.sh` from the repository root (or reboot if you use the crontab entry).

See `docs/pi-setup.txt` for the same steps in plain text.

## Development install

From a clone of the repository root:

```bash
pip install -e .
```

On a Raspberry Pi with hardware, prefer `bash scripts/pi-bootstrap.sh` or `pip install -e ".[rpi]"` so Linux-only dependencies are installed.

## Build verification

From the repository root, using a virtual environment:

```bash
python -m pip install -U build twine
python -m build
twine check dist/*
```

This produces `dist/*.whl` and `dist/*.tar.gz` without uploading to PyPI.