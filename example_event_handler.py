"""
Example event-based controller handler
Processes controller input events as they happen
"""

import pygame
from controller import SNESController


class SNESControllerEventHandler:
    """Handle controller input events"""

    def __init__(self):
        self.controller = SNESController(deadzone=0.3)
        self.previous_state = {}

    def handle_events(self):
        """Process pygame events from the controller"""
        if not self.controller.is_connected:
            return

        current_state = self.controller.get_state()

        # Detect button press (state changed from False to True)
        if current_state.get("buttons"):
            for button, pressed in current_state["buttons"].items():
                prev_pressed = self.previous_state.get("buttons", {}).get(button, False)

                if pressed and not prev_pressed:
                    self.on_button_press(button)
                elif not pressed and prev_pressed:
                    self.on_button_release(button)

        # Detect axis movement
        if current_state.get("axes"):
            for axis, value in current_state["axes"].items():
                prev_value = self.previous_state.get("axes", {}).get(axis, 0.0)

                # Significant change detected
                if abs(value - prev_value) > 0.1:
                    self.on_axis_motion(axis, value)

        # Detect D-Pad changes
        if current_state.get("hat"):
            prev_hat = self.previous_state.get("hat")
            if current_state["hat"] != prev_hat:
                self.on_hat_motion(current_state["hat"])

        self.previous_state = current_state

    def on_button_press(self, button: str):
        """Called when a button is pressed"""
        print(f"🔘 Button pressed: {button}")

    def on_button_release(self, button: str):
        """Called when a button is released"""
        print(f"🔘 Button released: {button}")

    def on_axis_motion(self, axis: str, value: float):
        """Called when an axis value changes significantly"""
        print(f"📊 {axis}: {value:.2f}")

    def on_hat_motion(self, direction: str):
        """Called when D-Pad direction changes"""
        if direction != "Neutral":
            print(f"⬆️  D-Pad: {direction}")

    def run(self):
        """Run the event handler"""
        if not self.controller.is_connected:
            print("Controller not connected")
            return

        print("\nListening for controller events...")
        print("Press Ctrl+C to exit\n")

        clock = pygame.time.Clock()

        try:
            while True:
                pygame.event.pump()
                self.handle_events()
                clock.tick(30)  # 30 Hz polling

        except KeyboardInterrupt:
            print("\n\nExiting...")
        finally:
            pygame.quit()


if __name__ == "__main__":
    handler = SNESControllerEventHandler()
    handler.run()
