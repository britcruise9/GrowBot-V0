"""Minimal driver for a WS2812 / NeoPixel LED ring via rpi_ws281x.

GrowBot's ring is 7 pixels on GPIO12 (PWM0). The WS2812 timing is generated
by the Pi's PWM + DMA, which requires **root** - run scripts that use this with
`sudo`. If rpi_ws281x is missing or you're not root, construction raises a clear
error so callers can skip lights gracefully.
"""
from __future__ import annotations

import time

try:
    from rpi_ws281x import Color, PixelStrip
except ImportError:  # pragma: no cover
    PixelStrip = None
    Color = None

from .pins import (
    LED_BRIGHTNESS,
    LED_CHANNEL,
    LED_COUNT,
    LED_DMA,
    LED_FREQ_HZ,
    LED_PIN,
)


class LedRing:
    def __init__(self, count: int = LED_COUNT, pin: int = LED_PIN, brightness: int = LED_BRIGHTNESS) -> None:
        if PixelStrip is None:
            raise RuntimeError("rpi_ws281x not installed - run: pip install rpi_ws281x")
        self.count = count
        self.strip = PixelStrip(count, pin, LED_FREQ_HZ, LED_DMA, False, brightness, LED_CHANNEL)
        try:
            self.strip.begin()
        except Exception as exc:  # typically a permissions error
            raise RuntimeError(f"LED init failed (WS2812 needs root - try sudo): {exc}") from exc

    def fill(self, rgb: tuple[int, int, int]) -> None:
        r, g, b = rgb
        for i in range(self.count):
            self.strip.setPixelColor(i, Color(r, g, b))
        self.strip.show()

    def off(self) -> None:
        self.fill((0, 0, 0))

    def spin(self, rgb: tuple[int, int, int], rounds: int = 2, delay: float = 0.05) -> None:
        """Chase a single lit pixel around the ring."""
        r, g, b = rgb
        for _ in range(rounds):
            for lit in range(self.count):
                for i in range(self.count):
                    self.strip.setPixelColor(i, Color(r, g, b) if i == lit else Color(0, 0, 0))
                self.strip.show()
                time.sleep(delay)
        self.off()
