import argparse
import hid
import time
import sys

# Button definitions: name -> (byte_index, bit_index)
_BUTTONS = {
    "B": (5, 6),
    "A": (5, 5),
    "X": (5, 4),
    "Y": (5, 7),
    "L": (6, 0),
    "R": (6, 1),
    "Select": (6, 4),
    "Start": (6, 5),
}

_DPAD_X_BYTE = 3
_DPAD_Y_BYTE = 4
_DPAD_CENTER = 127
_DPAD_THRESHOLD = 64


def parse_report(data):
    if len(data) < 7:
        return None

    buttons = [
        name for name, (byte, bit) in _BUTTONS.items() if data[byte] & (1 << bit)
    ]

    x, y = data[_DPAD_X_BYTE], data[_DPAD_Y_BYTE]
    dpad = []
    if x < _DPAD_CENTER - _DPAD_THRESHOLD:
        dpad.append("Left")
    if x > _DPAD_CENTER + _DPAD_THRESHOLD:
        dpad.append("Right")
    if y < _DPAD_CENTER - _DPAD_THRESHOLD:
        dpad.append("Up")
    if y > _DPAD_CENTER + _DPAD_THRESHOLD:
        dpad.append("Down")

    return {"buttons": buttons, "dpad": dpad}


def poll_controller(num_reads=50, delay=0.1, continuous=False):
    try:
        devices = hid.enumerate(0x0079, 0x0011)
        if not devices:
            print("No device found")
            return False

        device = hid.device()
        device.open_path(devices[0]["path"])
        device.set_nonblocking(True)

        if continuous:
            print("Polling continuously — press Ctrl+C to stop.\n")
        else:
            print(f"Polling {num_reads} times — press buttons and the D-pad!\n")

        last_state = None
        i = 0
        try:
            while continuous or i < num_reads:
                data = device.read(64)

                if data:
                    state = parse_report(data)
                    if state and state != last_state:
                        parts = []
                        if state["buttons"]:
                            parts.append("Buttons: " + ", ".join(state["buttons"]))
                        if state["dpad"]:
                            parts.append("D-Pad: " + "+".join(state["dpad"]))
                        if parts:
                            print(f"[{i:4d}] " + "  ".join(parts))
                        last_state = state

                time.sleep(delay)
                i += 1
        except KeyboardInterrupt:
            print("\nStopped.")

        device.close()
        if not continuous:
            print("\nDone!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Poll a SNES USB controller and print button/D-pad events.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-c",
        "--continuous",
        action="store_true",
        help="Run until Ctrl+C (default: 50 reads)",
    )
    mode.add_argument(
        "-n",
        "--num-reads",
        type=int,
        default=50,
        metavar="N",
        help="Number of reads before exiting (default: 50)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.1,
        metavar="SECS",
        help="Delay between reads in seconds (default: 0.1)",
    )
    args = parser.parse_args()

    success = poll_controller(
        num_reads=args.num_reads,
        delay=args.delay,
        continuous=args.continuous,
    )
    sys.exit(0 if success else 1)
