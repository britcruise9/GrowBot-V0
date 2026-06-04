"""Dead-simple speaker + mic helpers for GrowBot's MAX98357A speaker and INMP441 mic.

- speak(text): text-to-speech via espeak-ng (falls back to flite), played on the
  speaker through aplay.
- record_level(seconds): record from the mic and return a rough RMS loudness, so
  you can confirm the microphone is alive (tap it / talk and watch the number).

These shell out to standard tools (espeak-ng/flite/aplay/arecord) rather than
pulling in heavy Python audio deps. Bringup should be boring and reliable.
"""
from __future__ import annotations

import array
import os
import subprocess
import tempfile
import wave

from .pins import AUDIO_DEVICE, HELLO_PHRASE


def _tts_to_wav(text: str, wav_path: str) -> bool:
    for cmd in (["espeak-ng", "-w", wav_path, text], ["flite", "-t", text, "-o", wav_path]):
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=15)
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                return True
        except Exception:
            continue
    return False


def speak(text: str = HELLO_PHRASE, device: str | None = AUDIO_DEVICE) -> tuple[bool, str]:
    """Speak `text` aloud. Returns (ok, info)."""
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        if not _tts_to_wav(text, wav):
            return False, "no TTS available (install espeak-ng or flite)"
        attempts = ([["aplay", "-q", "-D", device, wav]] if device else []) + [["aplay", "-q", wav]]
        last = ""
        for cmd in attempts:
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=20)
                return True, f"played via {' '.join(cmd[:-1]) or 'aplay'}"
            except Exception as exc:
                last = str(exc)
        return False, f"aplay failed: {last}"
    finally:
        try:
            os.remove(wav)
        except OSError:
            pass


def record_level(seconds: float = 1.0, device: str | None = AUDIO_DEVICE) -> tuple[bool, object]:
    """Record briefly and return (ok, rms_level). Best-effort mic check."""
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        cmd = ["arecord", "-q"]
        if device:
            cmd += ["-D", device]
        cmd += ["-d", str(max(1, int(seconds))), "-f", "S16_LE", "-r", "16000", "-c", "1", wav]
        subprocess.run(cmd, check=True, capture_output=True, timeout=int(seconds) + 10)
        with wave.open(wav, "rb") as w:
            frames = w.readframes(w.getnframes())
        samples = array.array("h")
        samples.frombytes(frames)
        if not samples:
            return True, 0.0
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        return True, round(rms, 1)
    except Exception as exc:
        return False, str(exc)
    finally:
        try:
            os.remove(wav)
        except OSError:
            pass
