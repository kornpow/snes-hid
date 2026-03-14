# snes-hid

Python interface for a SNES USB controller on macOS, using direct HID communication.

**Controller:** Generic USB Gamepad (VID: `0x0079`, PID: `0x0011`)

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

### Read controller input

Polls the controller and prints button/D-pad events as they occur.

```bash
# Run for 50 reads (default)
uv run test_polling.py

# Run continuously until Ctrl+C
uv run test_polling.py -c

# Custom read count or polling delay
uv run test_polling.py -n 200
uv run test_polling.py -c -d 0.05

uv run test_polling.py --help
```

### Use the controller class directly

```python
from controller_hid import SNESControllerHID

controller = SNESControllerHID()
data = controller.read_input()
state = controller.parse_report(data)

# state["buttons"] -> {"A": bool, "B": bool, "X": bool, "Y": bool,
#                      "L": bool, "R": bool, "Select": bool, "Start": bool}
# state["dpad"]    -> {"Up": bool, "Down": bool, "Left": bool, "Right": bool}
```

### Re-map buttons

If the button mapping ever needs to be rediscovered (e.g. different adapter):

```bash
uv run map_buttons.py
```

This walks through each input interactively and saves the result to `button_mapping.json`.
