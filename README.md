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

## Development install

From a clone of the repository root:

```bash
pip install -e .
```

## Build verification

From the repository root, using a virtual environment:

```bash
python -m pip install -U build twine
python -m build
twine check dist/*
```

This produces `dist/*.whl` and `dist/*.tar.gz` without uploading to PyPI.