# AGENTS.md

## Project Overview

loam is a CircuitPython plant soil moisture monitor that runs on an Adafruit QT Py ESP32-S3 (8MB Flash / No PSRAM). It reads an I2C capacitive moisture sensor, sends push notifications, and deep sleeps between readings to conserve battery.

## Hardware Target

- **Board:** Adafruit QT Py ESP32-S3 — 8MB Flash / No PSRAM (product 5426)
- **Sensor:** Adafruit STEMMA Soil Sensor — I2C Capacitive Moisture Sensor (product 4026), connected via 4-pin JST PH to JST SH adapter cable (product 4424)
- **Firmware:** CircuitPython 10.x

## Project Structure

- `code.py` — Main application. Runs on every boot/wake cycle.
- `settings.toml` — Runtime configuration (WiFi credentials, Pushover keys, thresholds). Not checked in.
- `settings.toml.example` — Template for `settings.toml`.
- `.gitignore` — Ensures `settings.toml` isn’t committed.

The `lib/` directory on the CIRCUITPY drive (not in this repo) must contain:
- `adafruit_seesaw/`
- `adafruit_bus_device/`
- `adafruit_requests.mpy`

## Key Constraints

- **CircuitPython, not MicroPython or Arduino.** Use CircuitPython APIs and Adafruit libraries.
- **No PSRAM.** The board has 512KB SRAM only. Avoid large buffers.
- **Deep sleep restarts code.py from scratch.** There is no persistent state between wake cycles unless you use `alarm.sleep_memory` (raw bytes only).
- **NeoPixel power must be explicitly disabled.** CircuitPython auto-enables `board.NEOPIXEL_POWER` on boot. Set it to `False` via `digitalio` to save power.
- **USB connection fakes deep sleep.** Real power savings only occur on battery with no USB host connected.
- **Secrets go in `settings.toml`**, accessed via `os.getenv()`. Never hardcode credentials in `code.py`.
- **WiFi robustness.** Code connects with a timeout and proceeds offline; notifications are skipped if offline.
- **The soil sensor stays powered during deep sleep** since the QT Py lacks switchable STEMMA QT power.

## Sensor & Threshold Details

The STEMMA Soil Sensor uses the seesaw I2C protocol at address `0x36`. It provides:
- `moisture_read()` — Capacitive moisture reading. Range: ~200 (very dry) to ~2000 (very wet). Typical soil: 300–500.
- `get_temp()` — Chip temperature in Celsius (approximate, not precision).

Thresholds (configurable via `settings.toml`):
- `MOISTURE_THRESHOLD_LOW` — Below this value a DRY alert (priority=1) is sent.
- `MOISTURE_THRESHOLD_HIGH` — Above this value a WET notice (priority=0) is sent.
- Between the two, an OK notice (priority=-1) is sent.

Networking:
- `WIFI_CONNECT_TIMEOUT_S` — Seconds to wait for WiFi before proceeding offline.

## Coding Conventions

- Group imports: standard library, CircuitPython built-ins, third-party libraries (alphabetized within each group).
- Keep `code.py` as a single flat script — CircuitPython deep sleep re-runs the file from the top, so class hierarchies and module structures add complexity without benefit.
- Wrap network calls in try/except — WiFi and HTTP can fail, and the board should still sleep on failure rather than crash-looping.
