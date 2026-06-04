#!/usr/bin/env python3
"""Speak a phrase on the voiceHAT speaker, then sample the mic level."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growbot import audio, pins  # noqa: E402


def main() -> int:
    print("=== audio test ===")
    print(f"  speaking: {pins.HELLO_PHRASE!r}")
    ok, info = audio.speak(pins.HELLO_PHRASE)
    print(f"  speaker: {'OK' if ok else 'FAIL'} ({info})")

    print("  recording 1s from mic (tap it or talk)...")
    mic_ok, level = audio.record_level(1.0)
    if not mic_ok:
        print(f"  mic: FAIL ({level})")
    elif isinstance(level, (int, float)) and level < 5:
        print(f"  mic: recorded but SILENT (RMS={level}) - capture gain/mixer off, or no mic fitted")
    else:
        print(f"  mic: OK (RMS={level} - higher = louder)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
