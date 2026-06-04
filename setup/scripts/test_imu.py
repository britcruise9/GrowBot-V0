#!/usr/bin/env python3
"""Read the IMU: WHO_AM_I, then a few accel/gyro samples. Tilt to see them move."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growbot.imu import Imu  # noqa: E402


def main() -> int:
    print("=== IMU test ===")
    try:
        imu = Imu()
    except Exception as exc:
        print(f"!! {exc}")
        return 1
    who = imu.who_am_i()
    print(f"  WHO_AM_I=0x{who:02x} (MPU-6050 family often reports 0x68/0x70/0x71/0x98)")
    print("  samples (tilt the robot to watch acc shift, rotate to see gyro spike):")
    for _ in range(6):
        d = imu.read()
        print(
            f"    acc=({d['ax']:+.2f},{d['ay']:+.2f},{d['az']:+.2f})g  "
            f"gyro=({d['gx']:+.1f},{d['gy']:+.1f},{d['gz']:+.1f})deg/s"
        )
        time.sleep(0.2)
    imu.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
