# loam

A battery-friendly plant soil moisture monitor built with CircuitPython. Wakes once per day, reads soil moisture from a capacitive sensor, sends a [Pushover](https://pushover.net) notification, and goes back to deep sleep.

## Hardware

- [Adafruit QT Py ESP32-S3 — 8MB Flash / No PSRAM](https://www.adafruit.com/product/5426)
- [Adafruit STEMMA Soil Sensor — I2C Capacitive Moisture Sensor](https://www.adafruit.com/product/4026)
- [4-pin JST PH to JST SH Cable — STEMMA to QT / Qwiic](https://www.adafruit.com/product/4424) (200mm)
- Battery pack (raw LiPo recommended — USB power banks will auto-shutoff at deep sleep current levels)

Connect the soil sensor (JST PH connector) to the QT Py's STEMMA QT port (JST SH connector) using the adapter cable. No soldering required.

## Firmware

Install [CircuitPython](https://circuitpython.org/board/adafruit_qtpy_esp32s3_nopsram/) on the QT Py. This project was developed against CircuitPython 10.x.

## CircuitPython Libraries

Copy the following from the [Adafruit CircuitPython Library Bundle](https://circuitpython.org/libraries) into the `lib/` folder on your CIRCUITPY drive:

- `adafruit_seesaw/` (folder)
- `adafruit_bus_device/` (folder)
- `adafruit_requests.mpy`

Or install via [circup](https://github.com/adafruit/circup):

```sh
pip install circup
circup install adafruit_seesaw adafruit_requests
```

> Tip: Do not commit the `lib/` contents to this repo; they live on the CIRCUITPY drive.

## Setup

1. Copy `code.py` to the root of your CIRCUITPY drive.
2. Copy `settings.toml.example` to `settings.toml` on the CIRCUITPY drive and fill in your credentials and thresholds:

```toml
WIFI_SSID = "your_network"
WIFI_PASSWORD = "your_password"
PUSHOVER_API_KEY = "your_pushover_app_token"
PUSHOVER_USER_KEY = "your_pushover_user_key"

# Optional tuning
MOISTURE_THRESHOLD_LOW = 400   # below this -> DRY alert
MOISTURE_THRESHOLD_HIGH = 600  # above this -> WET notice
SLEEP_DURATION = 86400         # seconds between readings (24h)
WIFI_CONNECT_TIMEOUT_S = 20    # seconds to wait for WiFi before going offline
```

> Security: `settings.toml` contains secrets. It is ignored by `.gitignore` and should not be committed.

## Configuration

Environment variables in `settings.toml` control behavior:

- `MOISTURE_THRESHOLD_LOW` — Below this value, a DRY alert is sent. Default: `400`.
- `MOISTURE_THRESHOLD_HIGH` — Above this value, a WET notice is sent. Default: `600`.
- `SLEEP_DURATION` — Seconds between readings. Default: `86400` (24 hours).
- `WIFI_CONNECT_TIMEOUT_S` — How long to try connecting to WiFi before proceeding offline. Default: `20` seconds.

## How It Works

On each wake cycle, the board:

1. Disables the onboard NeoPixel to save power
2. Tries to connect to WiFi with a timeout; continues offline if unavailable
3. Reads moisture and temperature from the soil sensor via I2C
4. Sends a Pushover notification (DRY alert, OK notice, or WET notice)
5. Releases the I2C bus and enters deep sleep

Deep sleep restarts `code.py` from scratch on each wake, so no state is preserved between cycles.

## Power Estimates

With a 10,000 mAh battery (raw LiPo, not a USB power bank):

- Deep sleep draw: ~1–3mA (dominated by the always-on soil sensor)
- Active phase: ~200mA for ~10 seconds, once per day
- **Estimated runtime: ~6–9 months**

The soil sensor stays powered during deep sleep since the QT Py ESP32-S3 does not have switchable STEMMA QT power. Adding a MOSFET to gate power to the sensor would significantly extend battery life.

## Calibration

- Put the sensor in dry air/soil to note a baseline (often ~200–300).
- Water the pot thoroughly, then read again after 10–15 minutes (often ~600–900 depending on soil).
- Choose `MOISTURE_THRESHOLD_LOW` a bit above the “needs water soon” level and `MOISTURE_THRESHOLD_HIGH` above your typical just-watered level if you care to be notified when it’s very wet.
- You can print readings over several days to refine thresholds.

## Troubleshooting

- If using a USB power bank, it may shut off at low current in deep sleep. Prefer a raw LiPo connected to the QT Py’s BAT/GND pads or a bank with an “always-on” mode.
- If WiFi is flaky, the script will wait up to `WIFI_CONNECT_TIMEOUT_S` seconds, then proceed offline and still deep sleep to preserve battery.

## License

MIT
