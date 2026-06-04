#!/usr/bin/env python3
"""Move each detected servo a small, safe amount around its CURRENT position.

Gentle and bounded: each joint is nudged +/- pins.SAFE_NUDGE encoder units in
small steps, returned to where it started, and then released (torque off).
Nothing assumes left vs. right - servos are exercised by ID.

Put GrowBot on a stand or hold it, and keep fingers clear of the joints.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growbot import pins  # noqa: E402
from growbot.servos import ServoBus  # noqa: E402


def nudge(bus: ServoBus, sid: int, delta: int, step: int = 5, dwell: float = 0.02) -> None:
    start = bus.present_position(sid)
    if start is None:
        print(f"  id {sid}: no position read - skipping")
        return
    target = max(pins.ENCODER_MIN, min(pins.ENCODER_MAX, start + delta))
    print(f"  id {sid}: {start} -> {target} -> {start}")
    bus.set_torque(sid, True)
    stepping = step if target >= start else -step
    pos = start
    while abs(target - pos) > abs(stepping):
        pos += stepping
        bus.move(sid, pos)
        time.sleep(dwell)
    bus.move(sid, target)
    time.sleep(0.2)
    while abs(start - pos) > abs(stepping):
        pos -= stepping
        bus.move(sid, pos)
        time.sleep(dwell)
    bus.move(sid, start)
    time.sleep(0.2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", default=",".join(str(i) for i in pins.SERVO_IDS))
    ap.add_argument("--nudge", type=int, default=pins.SAFE_NUDGE)
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip()]

    print("=== safe servo motion test ===")
    print("GrowBot will move a few degrees per joint. Hold it or use a stand.\n")

    with ServoBus() as bus:
        present = [sid for sid in ids if bus.ping(sid)]
        if not present:
            print("no servos detected - run scan_servos.py first")
            return 1
        try:
            for sid in present:
                nudge(bus, sid, +args.nudge)
                nudge(bus, sid, -args.nudge)
        except KeyboardInterrupt:
            print("\ninterrupted - releasing torque")
        finally:
            # Always go limp on exit, even on error or Ctrl-C mid-motion.
            for sid in present:
                bus.set_torque(sid, False)
        print("\ndone - torque released (joints are limp)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
