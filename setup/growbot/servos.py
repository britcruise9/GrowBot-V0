"""Minimal big-endian-correct driver for SCS0009 / SC09 serial-bus servos.

The one fact that costs everyone a day: the SCS0009 stores 2-byte values
BIG-ENDIAN, for BOTH reads and writes. Dynamixel-style little-endian code
appears to work but silently writes garbage that the servo clips to its max
angle - which looks like a servo that refuses to move past some point.

Tested against SCS0009 servos on a Raspberry Pi Zero 2W over the raw UART
(no vendor SDK). Run scripts/scan_servos.py first to confirm the bus before
commanding any motion.
"""
from __future__ import annotations

import time

try:
    import serial  # pyserial
except ImportError:  # pragma: no cover - dependency hint
    serial = None

from .pins import (
    ENCODER_MAX,
    ENCODER_MIN,
    REG_GOAL_POS,
    REG_PRESENT_POS,
    REG_TORQUE_ENABLE,
    SERVO_BAUD,
    SERVO_PORT,
)

# Instruction codes
PING = 0x01
READ = 0x02
WRITE = 0x03
SYNC_WRITE = 0x83
BROADCAST_ID = 0xFE


def _checksum(sid: int, length: int, inst: int, params: list[int]) -> int:
    return (~(sid + length + inst + sum(params))) & 0xFF


def _packet(sid: int, inst: int, params: list[int]) -> bytes:
    length = len(params) + 2
    return bytes([0xFF, 0xFF, sid, length, inst] + list(params) + [_checksum(sid, length, inst, params)])


def _find_response(buf: bytes, sid: int) -> bytes | None:
    """Locate a checksum-valid response packet for ``sid`` inside ``buf``.

    Robust to the half-duplex echo and UART timing jitter: it scans for a
    well-formed ``FF FF <sid> ...`` frame whose checksum validates, rather than
    trusting byte offsets.
    """
    i = 0
    while i < len(buf) - 5:
        if buf[i] == 0xFF and buf[i + 1] == 0xFF and buf[i + 2] == sid:
            ln = buf[i + 3]
            end = i + 4 + ln
            if end <= len(buf):
                body = buf[i + 2 : end]
                if body[-1] == ((~sum(body[:-1])) & 0xFF):
                    return buf[i:end]
        i += 1
    return None


class ServoBus:
    """A thin, big-endian-correct interface to the SCS0009 servo bus."""

    def __init__(self, port: str = SERVO_PORT, baud: int = SERVO_BAUD, timeout: float = 0.05) -> None:
        if serial is None:
            raise RuntimeError("pyserial is not installed - run: pip install pyserial")
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def close(self) -> None:
        try:
            self.ser.close()
        except Exception:
            pass

    def __enter__(self) -> "ServoBus":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- low level -------------------------------------------------------
    def _txrx(self, sid: int, inst: int, params: list[int], read_extra: int = 16) -> bytes | None:
        pkt = _packet(sid, inst, params)
        self.ser.reset_input_buffer()
        self.ser.write(pkt)
        self.ser.flush()
        time.sleep(0.004)
        buf = self.ser.read(len(pkt) + read_extra)
        # Search after the TX echo so the echoed packet isn't read as a reply.
        idx = buf.find(pkt)
        start = idx + len(pkt) if idx >= 0 else 0
        return _find_response(buf[start:], sid)

    def ping(self, sid: int) -> bool:
        return self._txrx(sid, PING, [], read_extra=6) is not None

    def read_bytes(self, sid: int, reg: int, size: int) -> list[int] | None:
        resp = self._txrx(sid, READ, [reg, size], read_extra=size + 6)
        if not resp or len(resp) < 5 + size:
            return None
        return list(resp[5 : 5 + size])

    def read_word(self, sid: int, reg: int) -> int | None:
        data = self.read_bytes(sid, reg, 2)
        if not data:
            return None
        return (data[0] << 8) | data[1]  # BIG-ENDIAN

    def read_byte(self, sid: int, reg: int) -> int | None:
        data = self.read_bytes(sid, reg, 1)
        return data[0] if data else None

    def write_bytes(self, sid: int, reg: int, data: list[int]) -> None:
        self._txrx(sid, WRITE, [reg] + list(data), read_extra=6)

    def write_word(self, sid: int, reg: int, val: int) -> None:
        val = int(val) & 0xFFFF
        self.write_bytes(sid, reg, [(val >> 8) & 0xFF, val & 0xFF])  # BIG-ENDIAN

    def write_byte(self, sid: int, reg: int, val: int) -> None:
        self.write_bytes(sid, reg, [int(val) & 0xFF])

    # --- semantic helpers ------------------------------------------------
    def present_position(self, sid: int) -> int | None:
        """Read the servo's current encoder position (0-1023), or None."""
        return self.read_word(sid, REG_PRESENT_POS)

    def set_torque(self, sid: int, on: bool) -> None:
        """Enable (hold) or disable (go limp) the servo's torque."""
        self.write_byte(sid, REG_TORQUE_ENABLE, 1 if on else 0)

    def move(self, sid: int, pos: int) -> int:
        """Command a single servo to an encoder position, clamped to the safe range."""
        pos = max(ENCODER_MIN, min(ENCODER_MAX, int(pos)))
        self.write_word(sid, REG_GOAL_POS, pos)
        return pos

    def move_sync(self, targets: dict[int, int]) -> None:
        """Command several servos at once (true simultaneous motion).

        Sequential single-servo writes let one joint finish before the next
        starts; sync-write (instruction 0x83, broadcast ID) moves them together.
        """
        params: list[int] = [REG_GOAL_POS, 2]
        for sid, pos in targets.items():
            pos = max(ENCODER_MIN, min(ENCODER_MAX, int(pos)))
            params += [sid, (pos >> 8) & 0xFF, pos & 0xFF]
        length = len(params) + 2
        csum = (~(BROADCAST_ID + length + SYNC_WRITE + sum(params))) & 0xFF
        self.ser.write(bytes([0xFF, 0xFF, BROADCAST_ID, length, SYNC_WRITE] + params + [csum]))
        self.ser.flush()
        self.ser.reset_input_buffer()
