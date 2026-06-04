"""Minimal MPU-6050 (IMU) reader over I2C via smbus2.

Reads acceleration in g and angular rate in deg/s. Used for the IMU bringup
test - tilt the robot and watch the numbers move.
"""
from __future__ import annotations

import time

try:
    import smbus2
except ImportError:  # pragma: no cover
    smbus2 = None

from .pins import IMU_I2C_ADDR

REG_PWR_MGMT_1 = 0x6B
REG_WHO_AM_I = 0x75
REG_ACCEL_XOUT_H = 0x3B
REG_GYRO_XOUT_H = 0x43

ACCEL_SCALE = 16384.0  # LSB/g  at +/-2g
GYRO_SCALE = 131.0     # LSB/(deg/s) at +/-250 deg/s


class Imu:
    def __init__(self, addr: int = IMU_I2C_ADDR, bus_num: int = 1) -> None:
        if smbus2 is None:
            raise RuntimeError("smbus2 not installed - run: pip install smbus2")
        self.addr = addr
        self.bus = smbus2.SMBus(bus_num)
        self.bus.write_byte_data(addr, REG_PWR_MGMT_1, 0x00)  # wake from sleep
        time.sleep(0.05)

    def _word(self, reg: int) -> int:
        high = self.bus.read_byte_data(self.addr, reg)
        low = self.bus.read_byte_data(self.addr, reg + 1)
        val = (high << 8) | low
        return val - 65536 if val >= 0x8000 else val  # signed 16-bit

    def who_am_i(self) -> int:
        return self.bus.read_byte_data(self.addr, REG_WHO_AM_I)

    def read(self) -> dict[str, float]:
        return {
            "ax": self._word(REG_ACCEL_XOUT_H) / ACCEL_SCALE,
            "ay": self._word(REG_ACCEL_XOUT_H + 2) / ACCEL_SCALE,
            "az": self._word(REG_ACCEL_XOUT_H + 4) / ACCEL_SCALE,
            "gx": self._word(REG_GYRO_XOUT_H) / GYRO_SCALE,
            "gy": self._word(REG_GYRO_XOUT_H + 2) / GYRO_SCALE,
            "gz": self._word(REG_GYRO_XOUT_H + 4) / GYRO_SCALE,
        }

    def close(self) -> None:
        try:
            self.bus.close()
        except Exception:
            pass
