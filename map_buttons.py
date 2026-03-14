"""
Interactive button mapping tool for SNES USB Gamepad.

Walks you through each input one at a time, diffs the HID report
against an idle baseline, and saves the discovered mapping.

Usage:
    uv run map_buttons.py
"""

import hid
import json
import time
import sys
from pathlib import Path

VID = 0x0079
PID = 0x0011
READ_SIZE = 64
REPORT_BYTES = 8
SAMPLE_COUNT = 10  # reads to take when sampling a held input
SAMPLE_DELAY = 0.02  # seconds between reads

# SNES has no analog sticks — only these digital inputs
BUTTONS_TO_MAP = ["B", "A", "X", "Y", "L", "R", "Select", "Start"]
DPAD_DIRECTIONS = ["Up", "Down", "Left", "Right"]


# ── helpers ───────────────────────────────────────────────────────────────────


def open_device() -> hid.device:
    devices = hid.enumerate(VID, PID)
    if not devices:
        sys.exit(
            "No USB Gamepad found (VID=0x0079, PID=0x0011). Plug it in and try again."
        )
    dev = hid.device()
    dev.open_path(devices[0]["path"])
    dev.set_nonblocking(True)
    return dev


def flush(dev: hid.device, count: int = 5) -> None:
    """Discard stale buffered reports."""
    for _ in range(count):
        dev.read(READ_SIZE)
        time.sleep(0.01)


def sample_reports(dev: hid.device, count: int = SAMPLE_COUNT) -> list[list[int]]:
    """Collect up to `count` non-empty reports within a 3-second window."""
    reports = []
    deadline = time.time() + 3.0
    while len(reports) < count and time.time() < deadline:
        data = dev.read(READ_SIZE)
        if data:
            reports.append(list(data[:REPORT_BYTES]))
        time.sleep(SAMPLE_DELAY)
    return reports


def most_common_report(reports: list[list[int]]) -> list[int]:
    """Majority-vote each byte position across all samples."""
    if not reports:
        return [0] * REPORT_BYTES
    result = []
    for col in range(REPORT_BYTES):
        vals = [r[col] for r in reports]
        result.append(max(set(vals), key=vals.count))
    return result


def diff_bytes(baseline: list[int], active: list[int]) -> dict[int, tuple[int, int]]:
    """Return {byte_index: (baseline_val, active_val)} for every changed byte."""
    return {
        i: (baseline[i], active[i])
        for i in range(min(len(baseline), len(active)))
        if baseline[i] != active[i]
    }


def changed_bits(b_base: int, b_active: int) -> list[int]:
    """Bit positions that differ between two byte values."""
    diff = b_base ^ b_active
    return [i for i in range(8) if diff & (1 << i)]


def fmt_byte(val: int) -> str:
    return f"0x{val:02x}  ({val:3d})  0b{val:08b}"


def section(title: str) -> None:
    width = 60
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def prompt(msg: str) -> None:
    input(f"  → {msg}  [press Enter when ready] ")


# ── mapping routines ──────────────────────────────────────────────────────────


def capture_idle(dev: hid.device) -> list[int]:
    section("Step 1 of 3 — Idle Baseline")
    print("  Release every button and the D-pad completely.")
    prompt("Ready?")
    flush(dev)
    reports = sample_reports(dev, 20)
    baseline = most_common_report(reports)
    print(f"\n  Baseline: {' '.join(f'{b:02x}' for b in baseline)}\n")
    return baseline


def map_buttons(dev: hid.device, baseline: list[int]) -> dict:
    section("Step 2 of 3 — Face & Shoulder Buttons")
    print("  For each button below, press and HOLD it, then hit Enter.")
    print("  Keep holding until you see the result, then release.\n")

    mapping = {}
    total = len(BUTTONS_TO_MAP)

    for idx, button in enumerate(BUTTONS_TO_MAP, start=1):
        print(f"  [{idx}/{total}]  Button: {button}")
        prompt(f"Hold {button}")
        flush(dev)
        reports = sample_reports(dev, SAMPLE_COUNT)
        active = most_common_report(reports)

        diffs = diff_bytes(baseline, active)

        if not diffs:
            print(f"  [!] No change detected — skipping {button}.\n")
            continue

        print(f"       Raw: {' '.join(f'{b:02x}' for b in active)}")

        # Choose the byte where the most bits changed
        best_byte = max(diffs, key=lambda i: bin(diffs[i][0] ^ diffs[i][1]).count("1"))
        b_base, b_active = diffs[best_byte]
        bits = changed_bits(b_base, b_active)

        print(f"     Byte {best_byte}: {fmt_byte(b_base)}")
        print(f"          → {fmt_byte(b_active)}")
        print(f"       Bits changed: {bits}")

        if len(bits) == 1:
            mapping[button] = {"byte": best_byte, "bit": bits[0]}
            print(f"  [✓] {button} = byte[{best_byte}] bit {bits[0]}\n")
        else:
            mask = b_base ^ b_active
            mapping[button] = {"byte": best_byte, "mask": mask}
            print(
                f"  [✓] {button} = byte[{best_byte}] mask 0x{mask:02x}  (multiple bits)\n"
            )

    return mapping


def map_dpad(dev: hid.device, baseline: list[int]) -> dict:
    section("Step 3 of 3 — D-Pad")
    print("  For each direction below, press and HOLD the D-pad, then hit Enter.")
    print("  Keep holding until you see the result, then release.\n")

    mapping = {}
    total = len(DPAD_DIRECTIONS)

    for idx, direction in enumerate(DPAD_DIRECTIONS, start=1):
        print(f"  [{idx}/{total}]  D-Pad: {direction}")
        prompt(f"Hold D-pad {direction}")
        flush(dev)
        reports = sample_reports(dev, SAMPLE_COUNT)
        active = most_common_report(reports)

        diffs = diff_bytes(baseline, active)

        if not diffs:
            print(f"  [!] No change detected — skipping {direction}.\n")
            continue

        print(f"       Raw: {' '.join(f'{b:02x}' for b in active)}")

        # D-pad is typically an 8-way hat encoded as a single value in one byte
        best_byte = max(diffs, key=lambda i: abs(diffs[i][1] - diffs[i][0]))
        b_base, b_active = diffs[best_byte]

        mapping[direction] = {"byte": best_byte, "value": b_active, "baseline": b_base}
        print(
            f"  [✓] D-pad {direction} = byte[{best_byte}] value {b_active}  (baseline {b_base})\n"
        )

    return mapping


# ── summary & save ────────────────────────────────────────────────────────────


def print_summary(buttons: dict, dpad: dict) -> None:
    section("Mapping Summary")

    print("\n  Buttons")
    print(f"  {'Name':<10} {'Byte':>5}  {'Bit / Mask'}")
    print(f"  {'─' * 10}  {'─' * 4}  {'─' * 12}")
    for name, info in buttons.items():
        if "bit" in info:
            detail = f"bit {info['bit']}"
        else:
            detail = f"mask 0x{info['mask']:02x}"
        print(f"  {name:<10} byte[{info['byte']}]  {detail}")

    print("\n  D-Pad")
    print(f"  {'Direction':<10} {'Byte':>5}  {'Value'}")
    print(f"  {'─' * 10}  {'─' * 4}  {'─' * 5}")
    for direction, info in dpad.items():
        print(f"  {direction:<10} byte[{info['byte']}]  {info['value']}")


def save_mapping(buttons: dict, dpad: dict, path: Path) -> None:
    data = {"buttons": buttons, "dpad": dpad}
    path.write_text(json.dumps(data, indent=2))
    print(f"\n  Saved to {path}")


# ── main ──────────────────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("  SNES USB Controller — Button Mapping Tool")
    print("=" * 60)
    print("\n  Inputs on a SNES controller:")
    print("    Face buttons : B  A  X  Y")
    print("    Shoulders    : L  R")
    print("    Meta         : Select  Start")
    print("    D-Pad        : Up  Down  Left  Right")
    print("\n  This tool will walk you through each one.\n")

    dev = open_device()
    print(f"  Connected — USB Gamepad (VID=0x{VID:04x}, PID=0x{PID:04x})\n")

    try:
        baseline = capture_idle(dev)
        buttons = map_buttons(dev, baseline)
        dpad = map_dpad(dev, baseline)
    finally:
        dev.close()

    print_summary(buttons, dpad)

    out_path = Path("button_mapping.json")
    answer = input(f"\n  Save mapping to {out_path}? [Y/n] ").strip().lower()
    if answer != "n":
        save_mapping(buttons, dpad, out_path)
        print("  Done! Run the script again if any buttons were missed.")
    else:
        print("  Mapping not saved.")


if __name__ == "__main__":
    main()
