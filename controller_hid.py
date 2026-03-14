"""
SNES USB Controller Interface using HID
Direct USB communication via hidapi on macOS

Button mapping (discovered via map_buttons.py):
  Face:     B=byte5/bit6  A=byte5/bit5  X=byte5/bit4  Y=byte5/bit7
  Shoulder: L=byte6/bit0  R=byte6/bit1
  Meta:     Select=byte6/bit4  Start=byte6/bit5
  D-Pad:    byte3=L/R axis (0=Left, 127=center, 255=Right)
            byte4=U/D axis (0=Up,   127=center, 255=Down)
"""

import hid
import time
from typing import Dict, Optional

# Button definitions: name -> (byte_index, bit_index)
_BUTTONS: dict[str, tuple[int, int]] = {
    "B": (5, 6),
    "A": (5, 5),
    "X": (5, 4),
    "Y": (5, 7),
    "L": (6, 0),
    "R": (6, 1),
    "Select": (6, 4),
    "Start": (6, 5),
}

# D-Pad: each axis byte has center=127, min=0, max=255
_DPAD_X_BYTE = 3  # 0=Left, 255=Right
_DPAD_Y_BYTE = 4  # 0=Up,   255=Down
_DPAD_CENTER = 127
_DPAD_THRESHOLD = 64  # how far from center counts as pressed


class SNESControllerHID:
    """SNES USB controller input via HID."""

    def __init__(self, vendor_id: int = 0x0079, product_id: int = 0x0011):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.is_connected = False
        self.device_path = None
        self._connect()

    def _connect(self) -> bool:
        """Detect and connect to the controller."""
        try:
            devices = hid.enumerate(self.vendor_id, self.product_id)
            if not devices:
                print(
                    f"No USB Gamepad found (VID: {hex(self.vendor_id)}, PID: {hex(self.product_id)})"
                )
                return False

            self.device_path = devices[0]["path"]
            self.device = hid.device()
            self.device.open_path(self.device_path)
            self.device.set_nonblocking(True)
            self.is_connected = True
            print(
                f"Connected to USB Gamepad (VID: {hex(self.vendor_id)}, PID: {hex(self.product_id)})"
            )
            return True

        except Exception as e:
            print(f"Error connecting to controller: {e}")
            return False

    def read_input(self) -> Optional[bytes]:
        """Read one raw HID report, or None if nothing available."""
        if not self.is_connected or not self.device:
            return None
        try:
            data = self.device.read(64)
            return bytes(data) if data else None
        except Exception as e:
            print(f"Error reading input: {e}")
            return None

    def parse_report(self, data: bytes) -> Dict:
        """
        Parse a raw 8-byte HID report into a structured state dict.

        Returns:
            {
                "buttons": {"A": bool, "B": bool, ...},
                "dpad":    {"Up": bool, "Down": bool, "Left": bool, "Right": bool},
                "raw":     "01 7f 7f ..."   # hex string for debugging
            }
        """
        state: Dict = {
            "buttons": {name: False for name in _BUTTONS},
            "dpad": {"Up": False, "Down": False, "Left": False, "Right": False},
            "raw": " ".join(f"{b:02x}" for b in data) if data else "",
        }

        if not data or len(data) < 7:
            return state

        # --- buttons ---
        for name, (byte_idx, bit_idx) in _BUTTONS.items():
            state["buttons"][name] = bool(data[byte_idx] & (1 << bit_idx))

        # --- D-pad ---
        x = data[_DPAD_X_BYTE]
        y = data[_DPAD_Y_BYTE]
        state["dpad"]["Left"] = x < (_DPAD_CENTER - _DPAD_THRESHOLD)
        state["dpad"]["Right"] = x > (_DPAD_CENTER + _DPAD_THRESHOLD)
        state["dpad"]["Up"] = y < (_DPAD_CENTER - _DPAD_THRESHOLD)
        state["dpad"]["Down"] = y > (_DPAD_CENTER + _DPAD_THRESHOLD)

        return state

    def print_state(self, state: Dict) -> None:
        """Print only the active inputs (buttons + D-pad)."""
        pressed = [name for name, active in state["buttons"].items() if active]
        directions = [d for d, active in state["dpad"].items() if active]

        parts = []
        if pressed:
            parts.append("Buttons: " + ", ".join(pressed))
        if directions:
            parts.append("D-Pad: " + "+".join(directions))

        if parts:
            print("  ".join(parts))

    def run_polling_loop(self, update_frequency: int = 30) -> None:
        """Poll the controller and print state changes until Ctrl+C."""
        if not self.is_connected:
            print("Controller not connected")
            return

        print(f"Polling at {update_frequency} Hz — press Ctrl+C to exit\n")
        interval = 1.0 / update_frequency
        last_state = None

        try:
            while True:
                data = self.read_input()
                if data:
                    state = self.parse_report(data)
                    if state != last_state:
                        self.print_state(state)
                        last_state = state
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nExiting.")
        finally:
            if self.device:
                self.device.close()


def main():
    controller = SNESControllerHID()
    if controller.is_connected:
        controller.run_polling_loop(update_frequency=30)
    else:
        print("Failed to connect to controller")


if __name__ == "__main__":
    main()
