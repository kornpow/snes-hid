"""
SNES USB Controller Interface using inputs library
Lightweight cross-platform gamepad support
"""

import inputs
from typing import Dict, Optional
import sys


class SNESControllerInputs:
    """Handle SNES USB controller input via inputs library"""

    def __init__(self):
        """Initialize the controller interface"""
        self.controller = None
        self.is_connected = False

        self._detect_controller()

    def _detect_controller(self) -> bool:
        """Detect and initialize connected controller"""
        try:
            # Get all gamepads
            gamepads = inputs.get_gamepad()

            # Try to read from it to verify connection
            self.is_connected = True
            print("✓ Controller detected and ready!")
            return True

        except inputs.UnpluggedError:
            print("❌ No controller detected. Is it plugged in?")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def read_input(self) -> Optional[Dict]:
        """
        Read a single input event from the controller

        Returns:
            Dictionary with event information, or None on timeout
        """
        if not self.is_connected:
            return None

        try:
            event = inputs.get_key()

            return {
                "device": event.device,
                "event_type": event.ev_type,
                "state": event.state,
            }
        except inputs.UnpluggedError:
            print("❌ Controller unplugged!")
            self.is_connected = False
            return None
        except inputs.TimeoutError:
            return None
        except Exception as e:
            print(f"Error reading input: {e}")
            return None

    def print_event(self, event: Dict) -> None:
        """Pretty print an input event"""
        if not event:
            return

        device = event.get("device", "Unknown")
        event_type = event.get("event_type", "Unknown")
        state = event.get("state", "Unknown")

        print(f"{device}: {event_type} = {state}")

    def run_event_loop(self) -> None:
        """
        Run an event loop to continuously read controller input
        Press Ctrl+C to exit
        """
        if not self.is_connected:
            print("Controller not connected")
            return

        print("\nListening for controller events...")
        print("Press Ctrl+C to exit\n")

        try:
            while True:
                event = self.read_input()
                if event:
                    self.print_event(event)

        except KeyboardInterrupt:
            print("\n\nExiting...")
        except Exception as e:
            print(f"Error in event loop: {e}")


def main():
    """Example usage of SNESControllerInputs"""
    controller = SNESControllerInputs()

    if controller.is_connected:
        controller.run_event_loop()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
