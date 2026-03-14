"""
SNES USB Controller Interface
Reads input from a connected SNES-style USB controller using pygame
"""

import pygame
import sys
from typing import Dict, List, Tuple


class SNESController:
    """Handle SNES USB controller input"""

    # Button mapping for standard SNES layout
    BUTTON_NAMES = {
        0: "A",
        1: "B",
        2: "X",
        3: "Y",
        4: "LB",  # Left Bumper
        5: "RB",  # Right Bumper
        6: "Back",
        7: "Start",
        8: "Left Stick Press",
        9: "Right Stick Press",
    }

    # Axis mapping
    AXIS_NAMES = {
        0: "Left Stick X",
        1: "Left Stick Y",
        2: "Right Stick X",
        3: "Right Stick Y",
        4: "Left Trigger",
        5: "Right Trigger",
    }

    # D-Pad hat mapping
    HAT_DIRECTIONS = {
        (0, 0): "Neutral",
        (0, 1): "Up",
        (0, -1): "Down",
        (1, 0): "Right",
        (-1, 0): "Left",
        (1, 1): "Up-Right",
        (1, -1): "Down-Right",
        (-1, 1): "Up-Left",
        (-1, -1): "Down-Left",
    }

    def __init__(self, deadzone: float = 0.5):
        """
        Initialize the controller interface

        Args:
            deadzone: Analog stick deadzone (0.0-1.0), default 0.5
        """
        pygame.init()
        pygame.display.set_mode((1, 1))  # Minimal window for event handling
        pygame.joystick.init()

        self.deadzone = deadzone
        self.joystick = None
        self.is_connected = False

        self._detect_controller()

    def _detect_controller(self) -> bool:
        """Detect and initialize connected controller"""
        joystick_count = pygame.joystick.get_count()

        if joystick_count == 0:
            print("❌ No controllers detected")
            return False

        print(f"✓ Found {joystick_count} controller(s)")

        # Use the first controller found
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.is_connected = True
        print(f"✓ Connected to: {self.joystick.get_name()}")
        print(f"  - Buttons: {self.joystick.get_numbuttons()}")
        print(f"  - Axes: {self.joystick.get_numaxes()}")
        print(f"  - Hats: {self.joystick.get_numhats()}")

        return True

    def _apply_deadzone(self, value: float) -> float:
        """Apply deadzone to analog stick value"""
        if abs(value) < self.deadzone:
            return 0.0

        # Normalize value after deadzone
        if value > 0:
            return (value - self.deadzone) / (1.0 - self.deadzone)
        else:
            return (value + self.deadzone) / (1.0 - self.deadzone)

    def get_state(self) -> Dict:
        """
        Get current controller state

        Returns:
            Dictionary containing button states, axis values, and hat position
        """
        if not self.is_connected or not self.joystick:
            return {}

        state = {
            "buttons": {},
            "axes": {},
            "hat": None,
        }

        # Button states
        for i in range(self.joystick.get_numbuttons()):
            button_name = self.BUTTON_NAMES.get(i, f"Button {i}")
            state["buttons"][button_name] = self.joystick.get_button(i)

        # Axis values (analog sticks and triggers)
        for i in range(self.joystick.get_numaxes()):
            axis_name = self.AXIS_NAMES.get(i, f"Axis {i}")
            raw_value = self.joystick.get_axis(i)
            state["axes"][axis_name] = self._apply_deadzone(raw_value)

        # Hat (D-Pad)
        if self.joystick.get_numhats() > 0:
            hat_value = self.joystick.get_hat(0)
            state["hat"] = self.HAT_DIRECTIONS.get(hat_value, "Unknown")

        return state

    def print_state(self, state: Dict) -> None:
        """Pretty print the controller state"""
        if not state:
            print("No controller state available")
            return

        print("\n" + "=" * 50)

        # Buttons
        pressed_buttons = [btn for btn, pressed in state["buttons"].items() if pressed]
        if pressed_buttons:
            print(f"Buttons: {', '.join(pressed_buttons)}")

        # Analog sticks and triggers
        meaningful_axes = {k: v for k, v in state["axes"].items() if abs(v) > 0.01}
        if meaningful_axes:
            print("Axes:")
            for axis_name, value in meaningful_axes.items():
                print(f"  {axis_name}: {value:.2f}")

        # D-Pad
        if state["hat"] and state["hat"] != "Neutral":
            print(f"D-Pad: {state['hat']}")

        print("=" * 50)

    def run_polling_loop(self, update_frequency: int = 30) -> None:
        """
        Run a polling loop to continuously read controller input

        Args:
            update_frequency: Updates per second (Hz)
        """
        if not self.is_connected:
            print("Controller not connected")
            return

        print(f"\nPolling controller at {update_frequency} Hz")
        print("Press Ctrl+C to exit\n")

        clock = pygame.time.Clock()

        try:
            while True:
                pygame.event.pump()  # Update pygame events without blocking

                state = self.get_state()
                self.print_state(state)

                clock.tick(update_frequency)

        except KeyboardInterrupt:
            print("\n\nExiting...")
        finally:
            pygame.quit()


def main():
    """Example usage of SNESController"""
    controller = SNESController(deadzone=0.3)

    if controller.is_connected:
        controller.run_polling_loop(update_frequency=10)
    else:
        print("Failed to connect to controller")
        sys.exit(1)


if __name__ == "__main__":
    main()
