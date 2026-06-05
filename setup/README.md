# GrowBot V0 Setup and Calibration Software

This is the basic software to bring the GrowBot hardware to life. It is a small driver package plus one quick test per subsystem (servos, LED ring, speaker, mic, IMU, camera), and a `hello_growbot.py` that runs lights, voice, and legs together. Its job is to prove the body works. It does not include the learning agent, the LLM brain, or the training code. Those are V1, still in development.

> [!IMPORTANT]
> The SCS0009 / SC09 servos store 2-byte values big-endian, for reads and writes. If you get nonsense positions or a servo that will not move past some point, check the byte order first. Little-endian code (Dynamixel style) looks like it works, then silently writes garbage. That one fact cost me a full day, so the driver here gets it right.

## What's in it

Drivers in `growbot/` (you import these):

| Module | What it does |
|--------|--------------|
| `pins.py` | every wiring constant in one place (port, servo IDs, GPIO pins, encoder range). **Edit this to match your build.** |
| `servos.py` | SCS0009 servos, big-endian correct: scan, read position, move, sync-move |
| `leds.py` | WS2812 ring on GPIO12: fill, spin, off |
| `audio.py` | `speak(text)` through espeak-ng/flite and aplay; sample the mic level |
| `imu.py` | MPU-6050 over I2C: WHO_AM_I, accel, gyro |
| `camera.py` | capture one still from the Pi camera |

Scripts in `scripts/` (you run these):

| Command | What it does |
|---------|--------------|
| `python3 scripts/scan_servos.py` | read-only: finds servos, prints positions, no motion |
| `python3 scripts/test_servos_safe.py` | nudges each leg a few degrees and back, then goes limp |
| `sudo python3 scripts/test_leds.py` | ring through red, green, blue, white, then a spin |
| `python3 scripts/test_audio.py` | says "hello, I'm GrowBot", then samples the mic |
| `python3 scripts/test_imu.py` | prints WHO_AM_I and live accel/gyro, tilt it to watch |
| `python3 scripts/test_camera.py` | captures one photo to /tmp |
| `sudo -E python3 scripts/hello_growbot.py` | the full hello: lights, voice, legs. Skips whatever is not present. |

## Setup

```bash
pip install -r requirements.txt
sudo apt install espeak-ng   # text-to-speech (flite also works)
# picamera2 and alsa-utils (aplay/arecord) ship with Raspberry Pi OS
```

The LED ring uses the Pi's PWM/DMA for WS2812 timing, which needs root, so run the LED test and the full hello with `sudo`.

## Quickstart

```bash
python3 scripts/scan_servos.py            # confirm the servo bus (read-only)
python3 scripts/test_servos_safe.py       # gentle leg nudge (hold the robot or use a stand)
sudo python3 scripts/test_leds.py         # ring colors and a spin
python3 scripts/test_audio.py             # speaker says hello, mic level
python3 scripts/test_imu.py               # tilt to watch accel/gyro
python3 scripts/test_camera.py            # one photo to /tmp
sudo -E python3 scripts/hello_growbot.py  # lights, voice, legs together
```

If `scan_servos.py` can't open the port: on a Pi Zero 2W the servo bus is `/dev/serial0` (the real PL011 UART), not `/dev/ttyS0` (which throws an Input/output error). Enable it with `raspi-config` > Interface Options > Serial Port: login shell off, serial hardware on, then reboot.

## SCS0009 register cheat sheet

All 2-byte values are big-endian.

| Reg | Name | Bytes | Notes |
|-----|------|-------|-------|
| 0x03 | ID | 1 | 1 to 253 |
| 0x28 | torque enable | 1 | 0 = limp, 1 = holding |
| 0x2A | goal position | 2 BE | 0 to 1023 |
| 0x30 | EEPROM lock | 1 | write 0 to unlock before changing 0x00 to 0x2F, 1 to lock |
| 0x38 | present position | 2 BE | read-only |

Packet: `FF FF <id> <len> <inst> <params...> <checksum>`, where `len = len(params) + 2` and `checksum = ~(id + len + inst + sum(params)) & 0xFF`. The bus is half-duplex, so every send is echoed back before the reply; strip the echo before parsing. The driver does this and checks the checksum so a stray echo byte can't be read as a position.

The SCS0009 reports 0 to 1023 across about 300 degrees. On my units the usable floor is 255, so the driver clamps motion to 255 to 1023.

## Tested on

A Raspberry Pi Zero 2W (Raspberry Pi OS Bookworm, 64-bit) with two SCS0009 servos on the PL011 UART at 1 Mbaud, an MPU-6050 IMU at I2C 0x68, a 7-pixel WS2812 ring on GPIO12, a MAX98357A amp into a speaker, an INMP441 mic, and a Pi camera. Your build will differ, so `growbot/pins.py` is where you reconcile it.

Audio note: the MAX98357A is usually set up with the googlevoicehat-soundcard overlay, so its ALSA card shows up as `sndrpigooglevoi` (that is the default in `pins.py`; change it if yours differs). If a play returns cleanly but you hear nothing, it is almost always speaker wiring, not software.

## Safety

These scripts move a real robot. `test_servos_safe.py` and `hello_growbot.py` move each joint a few degrees around where it currently is, so keep GrowBot on a stand or hold it, and keep fingers clear. Motion is clamped in software to the usable encoder range, and torque is released on exit, even on Ctrl-C. The scripts talk to servos by ID and make no left/right assumption, so you can bring up the bus before you have settled your own leg mapping.

## License

[CC BY-NC 4.0](../LICENSE), the same as the rest of the repo. Build it, change it, and share it for non-commercial use, with credit to Art of the Problem.
