"""
Quick test to verify controller connection without blocking
"""

import hid
import sys


def test_connection():
    """Test if we can connect to the controller"""
    try:
        vendor_id = 0x0079
        product_id = 0x0011

        devices = hid.enumerate(vendor_id, product_id)

        if not devices:
            print("No device found")
            return False

        print(f"Found device: {devices[0]}")

        device = hid.device()
        device.open_path(devices[0]["path"])
        device.set_nonblocking(True)

        # Try one read
        data = device.read(64)

        if data:
            print(f"Successfully read {len(data)} bytes: {bytes(data).hex()}")
        else:
            print("Device connected but no data available (this is normal)")

        device.close()
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
