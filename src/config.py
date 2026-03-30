from rpi_ws281x import Color

# ------------------------------------------------------------------
# MATRIX LED WS2812B PARAMETERS
# ------------------------------------------------------------------
LED_X, LED_Y = 8, 8
LED_COUNT = LED_X * LED_Y
LED_PIN = 18
LED_FREQ_HZ = 800_000
LED_DMA = 10
LED_INVERT = False
LED_BRIGHTNESS = 255
LED_CHANNEL = 0

# ------------------------------------------------------------------
# RPM PARAMETERS (ported from C++ Config.hpp)
# ------------------------------------------------------------------
RPM_MAX = 5300.0
RPM_START = 4000.0
RPM_BASE_PAIRS = 3

RPM_EMA_ALPHA = 0.70
# Gdy kandydat na bieg jest większy niż stabilny, a surowe RPM rośnie o > tego progu,
# traktujemy to jako fałszywy "upshift" (w prawdziwym upshifcie RPM zwykle spada).
RPM_RISE_DOWNSHIFT_GUARD = 120.0

OVER_REV_ALERT_MARGIN_RPM = 300.0
OVER_REV_BLINK_PERIOD_SEC = 0.16

# LED / main loop timing
TARGET_FRAME_TIME_SEC = 0.016

# ------------------------------------------------------------------
# GEAR PREDICTOR PARAMETERS
# ------------------------------------------------------------------
# OBD Vehicle Speed is typically km/h (python-OBD); GEARS_RATIOS must match that unit.
# Histereza luzu: z biegu → 0 przy speed <= ON; z 0 → dopiero gdy speed >= OFF (brak skoków 0↔1).
NEUTRAL_SPEED_ON = 3.0
NEUTRAL_SPEED_OFF = 6.0
MIN_SPEED_FOR_RATIO = 1.0  # poniżej tego predict_gear_raw zwraca -1 (unikaj rpm/speed)

GEAR_TOLERANCE = 0.2
GEAR_FILTER_LEN = 3
GEAR_HYSTERESIS_K = 2
# Nowy bieg musi być bliżej idealnego stosunku o ten margines (jednostki jak GEARS_RATIOS).
GEAR_HYSTERESIS_DEV_MARGIN = 8.0
GEAR_UNKNOWN_HOLD_SEC = 0.2

GEARS_RATIOS = {
    0: 0,
    1: 133,
    2: 73,
    3: 49,
    4: 37,
    5: 29,
}

# ------------------------------------------------------------------
# GEAR DISPLAY INDICES — LED MATRIX
# ------------------------------------------------------------------
GEARS_INDEX = {
    -1: [],
    0: [24, 25, 26, 27, 28, 29, 30, 34, 35, 43, 53, 54, 56, 57, 58, 59, 60, 61, 62],
    1: [24, 28, 34, 39, 40, 41, 42, 43, 44, 45, 46, 55, 56],
    2: [24, 25, 29, 33, 37, 39, 40, 43, 46, 49, 51, 55, 56, 61],
    3: [25, 29, 33, 39, 40, 43, 46, 49, 52, 55, 57, 58, 60, 61],
    4: [27, 28, 34, 36, 43, 46, 49, 50, 51, 52, 53, 54, 55, 59],
    5: [25, 27, 28, 29, 30, 33, 36, 39, 40, 43, 46, 49, 52, 55, 57, 58, 59, 62],
}

# ------------------------------------------------------------------
# LED COLORS — gear: purple; RPM: green → purple; over-rev blink: red
# ------------------------------------------------------------------
COLORS = {
    "gear": Color(109, 40, 217),
    "rpm_base": Color(74, 222, 128),
    "rpm_shift": Color(109, 40, 217),
    "over_rev": Color(255, 0, 0),
    "black": Color(0, 0, 0),
}

# ------------------------------------------------------------------
# OBD CONNECTION PARAMETERS (python-OBD Async)
# ------------------------------------------------------------------
# None = auto-detect USB serial. If that fails, set e.g. "/dev/ttyUSB0" or "/dev/ttyACM0".
OBD_PORT = None

OBD_FAST = True
OBD_TIMEOUT = 0.05
OBD_CHECK_VOLTAGE = False
OBD_DELAY_CMDS = 0.01
OBD_PROTOCOL = "5"