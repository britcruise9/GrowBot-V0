#!/usr/bin/env python3
"""GrowBot's first hello - lights, voice, and legs together, gently.

Wakes its LED ring, says hello, and waves its legs. Every subsystem is optional:
if the LED ring, speaker, or servos aren't present, that part is skipped and the
rest still runs - so even a half-built robot says hi.

LEDs need root, so for the full effect run:

    sudo -E python3 scripts/hello_growbot.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growbot import pins  # noqa: E402


def open_leds():
    try:
        from growbot.leds import LedRing

        return LedRing()
    except Exception as exc:
        print(f"  (lights skipped: {exc})")
        return None


def say_hello() -> bool:
    try:
        from growbot import audio

        print(f"  speaking: {pins.HELLO_PHRASE!r}")
        ok, info = audio.speak(pins.HELLO_PHRASE)
        if not ok:
            print(f"  (voice issue: {info})")
        return ok
    except Exception as exc:
        print(f"  (voice skipped: {exc})")
        return False


def wave_legs() -> bool:
    try:
        from growbot.servos import ServoBus
    except Exception as exc:
        print(f"  (legs skipped: {exc})")
        return False
    try:
        with ServoBus() as bus:
            joints = [s for s in pins.SERVO_IDS if bus.ping(s)]
            starts = {s: bus.present_position(s) for s in joints}
            movable = [s for s in joints if starts[s] is not None]
            if not movable:
                print("  (legs skipped: no servos answering)")
                return False
            print(f"  waving {len(movable)} leg(s): {movable}")
            try:
                for sid in movable:
                    bus.set_torque(sid, True)
                for _ in range(2):
                    for sid in movable:
                        base = starts[sid]
                        for delta in (pins.SAFE_NUDGE, -pins.SAFE_NUDGE, 0):
                            bus.move(sid, base + delta)
                            time.sleep(0.22)
                for sid in movable:
                    bus.move(sid, starts[sid])
                time.sleep(0.3)
            finally:
                for sid in movable:
                    bus.set_torque(sid, False)
            return True
    except Exception as exc:
        print(f"  (legs skipped: {exc})")
        return False


def main() -> int:
    print("hi, i'm growbot. waking up...\n")

    ring = open_leds()
    if ring:
        ring.fill((0, 120, 255))  # awake blue

    spoke = say_hello()
    waved = wave_legs()

    if ring:
        ring.spin((0, 255, 120), rounds=1, delay=0.04)  # happy green
        ring.off()

    did = [name for name, ok in (("lights", bool(ring)), ("voice", spoke), ("legs", waved)) if ok]
    print(f"\nthat's me - {', '.join(did) if did else 'quietly here'}. nice to meet you.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
