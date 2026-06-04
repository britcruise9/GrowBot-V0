#!/usr/bin/env python3
"""Capture one camera frame to /tmp and report it."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growbot import camera  # noqa: E402


def main() -> int:
    out = camera.DEFAULT_PATH
    print("=== camera test ===")
    ok, info = camera.capture(out)
    if ok:
        size = Path(out).stat().st_size if Path(out).exists() else 0
        print(f"  captured via {info} -> {out} ({size} bytes)")
        print("  (scp it to your laptop to look at the photo)")
        return 0
    print(f"  FAIL: {info}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
