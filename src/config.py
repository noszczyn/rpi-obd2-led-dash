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

# Guard na fałszywy downshift podczas hamowania: jeśli kandydat na bieg spada (np. 4→3),
# ale surowe RPM nie rośnie co najmniej o ten próg, to blokujemy zmianę.
RPM_DOWN_SHIFT_CONFIRM_RISE = 200.0

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
GEAR_HYSTERESIS_DEV_MARGIN = 2.0
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
    0: [3, 7, 8, 13, 17, 18, 19, 20, 21, 22, 23, 24, 39],
    1: [24, 28, 34, 39, 40, 41, 42, 43, 44, 45, 46, 55, 56],
    2: [2, 6, 7, 8, 10, 14, 17, 20, 23, 24, 28, 30, 34, 39],
    3: [2, 6, 8, 14, 17, 20, 23, 24, 27, 30, 34, 35, 37, 38],
    4: [3, 4, 11, 13, 17, 20, 24, 25, 26, 27, 28, 29, 30, 36],
    5: [1, 2, 3, 6, 8, 11, 14, 17, 20, 23, 24, 27, 30, 33, 36, 37, 38],
}

# ------------------------------------------------------------------
# LED COLORS — gear: purple; RPM: green → purple; over-rev blink: red
# ------------------------------------------------------------------
COLORS = {
    "gear": Color(109, 40, 217),
    "rpm_base": Color(0, 200, 30),
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