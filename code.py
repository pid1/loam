# Standard library imports
import os
import ssl
import time

# CircuitPython built-in imports
import alarm
import board
import digitalio
import socketpool
import wifi

# Third-party library imports
import adafruit_requests
from adafruit_seesaw.seesaw import Seesaw

# --- Configuration (env-overridable) ---
SLEEP_DURATION = int(os.getenv("SLEEP_DURATION", "86400"))
WIFI_CONNECT_TIMEOUT_S = int(os.getenv("WIFI_CONNECT_TIMEOUT_S", "20"))
# Moisture thresholds
MOISTURE_THRESHOLD_LOW = int(os.getenv("MOISTURE_THRESHOLD_LOW", "400"))
MOISTURE_THRESHOLD_HIGH = int(os.getenv("MOISTURE_THRESHOLD_HIGH", "600"))

# Pushover credentials from environment
PUSHOVER_TOKEN = os.getenv("PUSHOVER_API_KEY")
PUSHOVER_USER = os.getenv("PUSHOVER_USER_KEY")

# Disable NeoPixel on start to save power
neopixel_power = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
neopixel_power.direction = digitalio.Direction.OUTPUT
neopixel_power.value = False


def connect_wifi(timeout_s: int) -> bool:
    """Connect to WiFi with a timeout; return True if connected, else False."""
    ssid = os.getenv("WIFI_SSID")
    password = os.getenv("WIFI_PASSWORD")
    if not ssid or not password:
        print("WiFi SSID/PASSWORD not set; running offline")
        return False
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            wifi.radio.connect(ssid, password)
            print(f"Connected to {ssid}")
            return True
        except Exception as e:
            print(f"WiFi connect error: {e}; retrying...")
            time.sleep(1)
    print("WiFi connect timeout; proceeding offline")
    return False


# Main execution; always deep-sleep even on failures
i2c = None
try:
    connected = connect_wifi(WIFI_CONNECT_TIMEOUT_S)
    requests = None
    if connected:
        pool = socketpool.SocketPool(wifi.radio)
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

    i2c = board.STEMMA_I2C()
    soil = Seesaw(i2c, addr=0x36)

    moisture = soil.moisture_read()
    temp = soil.get_temp()

    print(
        f"Moisture: {moisture}  Temp: {temp:.1f}C  "
        f"(low<{MOISTURE_THRESHOLD_LOW} / high>{MOISTURE_THRESHOLD_HIGH})"
    )

    # Decide state and message
    if moisture < MOISTURE_THRESHOLD_LOW:
        message = (
            f"🌱 Soil is DRY. Moisture={moisture} (<{MOISTURE_THRESHOLD_LOW})"
        )
        priority = 1
    elif moisture > MOISTURE_THRESHOLD_HIGH:
        message = (
            f"💧 Soil is WET. Moisture={moisture} (>{MOISTURE_THRESHOLD_HIGH})"
        )
        priority = 0  # informational
    else:
        message = (
            f"✓ Soil moisture OK: {moisture} (between "
            f"{MOISTURE_THRESHOLD_LOW}-{MOISTURE_THRESHOLD_HIGH})"
        )
        priority = -1
    print(message)

    # Send Pushover if configured and online
    if PUSHOVER_TOKEN and PUSHOVER_USER and requests:
        data = {
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message,
            "title": "Plant Monitor",
            "priority": priority,
        }
        try:
            resp = requests.post(
                "https://api.pushover.net/1/messages.json", data=data
            )
            print(f"Pushover: {resp.status_code}")
            resp.close()
        except Exception as e:
            print(f"Pushover error: {e}")
    else:
        if not (PUSHOVER_TOKEN and PUSHOVER_USER):
            print("Pushover credentials not configured")
        if not connected:
            print("Skipping notification (offline)")

finally:
    try:
        if i2c:
            i2c.deinit()
    except Exception:
        pass
    time.sleep(1)
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + SLEEP_DURATION)
    print(f"Sleeping for {SLEEP_DURATION}s...")
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)

