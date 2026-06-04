#!/usr/bin/env python3
"""Light the WS2812 ring through a few colors, then a spin.

WS2812 needs root, so run this with sudo:

    sudo python3 scripts/test_leds.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growbot.leds import LedRing  # noqa: E402


def main() -> int:
    print("=== LED ring test (needs root) ===")
    try:
        ring = LedRing()
    except Exception as exc:
        print(f"!! {exc}")
        return 1
    for name, rgb in [("red", (255, 0, 0)), ("green", (0, 255, 0)), ("blue", (0, 0, 255)), ("white", (255, 255, 255))]:
        print(f"  {name}")
        ring.fill(rgb)
        time.sleep(0.5)
    print("  spin")
    ring.spin((0, 180, 255), rounds=2, delay=0.05)
    ring.off()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
