#!/usr/bin/env python3
"""Read-only scan for GrowBot's SCS0009 servos. Commands NO motion.

Use this for first contact: it confirms the bus, baud, and which IDs answer,
without sending a single move command. If this works, your wiring and power
are good and you can move on to the motion tests.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growbot import pins  # noqa: E402
from growbot.servos import ServoBus  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", default=pins.SERVO_PORT)
    ap.add_argument("--baud", type=int, default=pins.SERVO_BAUD)
    ap.add_argument(
        "--ids",
        default=",".join(str(i) for i in (*pins.SERVO_IDS, 3, 4, 5, 6)),
        help="comma-separated servo IDs to probe",
    )
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip()]

    print("=== GrowBot servo scan (read-only, no motion) ===")
    print(f"port={args.port} baud={args.baud} ids={ids}\n")

    try:
        bus = ServoBus(args.port, args.baud)
    except Exception as exc:
        print(f"!! could not open {args.port}: {exc}")
        print("   On a Pi Zero 2W the servo bus is /dev/serial0, not /dev/ttyS0.")
        return 1

    found = []
    with bus:
        for sid in ids:
            if bus.ping(sid):
                pos = bus.present_position(sid)
                print(f"  id {sid:<3} PRESENT   present_pos={pos}")
                found.append(sid)
            else:
                print(f"  id {sid:<3} -")

    if found:
        print(f"\nfound {len(found)} servo(s): {found}")
        return 0
    print("\nno servos found - check power, wiring, and that you're on /dev/serial0")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
