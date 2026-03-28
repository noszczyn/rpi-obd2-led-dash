from rpi_ws281x import Color

# ------------------------------------------------------------------
# MATRIX LED WS2812B PARAMETERS
# ------------------------------------------------------------------
LED_X, LED_Y     = 8, 8
LED_COUNT        = LED_X * LED_Y
LED_PIN          = 18       # GPIO pin
LED_FREQ_HZ      = 800000   # LED signal frequency (Hz)
LED_DMA          = 10       # DMA channel
LED_INVERT       = False    # invert signal (for NPN transistor)
LED_BRIGHTNESS   = 30       # brightness (0-255)
LED_CHANNEL      = 0        # PWM channel

# ------------------------------------------------------------------
# RPM PARAMETERS — SUZUKI SWIFT 2008
# ------------------------------------------------------------------
RPM_MAX          = 5000     # RPM at which LED indicator ends
RPM_START        = 3000     # RPM at which LED indicator starts
RPM_BASE_PAIRS   = 3        # LED pairs shown in base color before shift color

# ------------------------------------------------------------------
# GEAR PREDICTOR PARAMETERS
# ------------------------------------------------------------------
NEUTRAL_SPEED_LIMIT = 3     # below this speed (km/h) gear is always neutral
GEAR_TOLERANCE      = 0.2   # max allowed deviation from gear ratio (20%)

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
    0:  [24,25,26,27,28,29,30,34,35,43,53,54,56,57,58,59,60,61,62],  # neutral
    1:  [24,28,34,39,40,41,42,43,44,45,46,55,56],
    2:  [24,25,29,33,37,39,40,43,46,49,51,55,56,61],
    3:  [25,29,33,39,40,43,46,49,52,55,57,58,60,61],
    4:  [27,28,34,36,43,46,49,50,51,52,53,54,55,59],
    5:  [25,27,28,29,30,33,36,39,40,43,46,49,52,55,57,58,59,62],
}

# ------------------------------------------------------------------
# LED COLORS
# ------------------------------------------------------------------
COLORS = {
    "gear":      Color(255, 80, 0),   # amber
    "rpm_base":  Color(255, 40, 0),   # amber
    "rpm_shift": Color(255, 0,  0),   # red
    "black":     Color(0,   0,  0),   # off
}

# ------------------------------------------------------------------
# OBD CONNECTION PARAMETERS
# ------------------------------------------------------------------
OBD_FAST          = True    # return data after 1 response instead of timeout
OBD_TIMEOUT       = 0.05    # serial port timeout (seconds)
OBD_CHECK_VOLTAGE = False   # skip voltage detection on startup
OBD_DELAY_CMDS    = 0.05    # delay between command cycles (default: 0.25s)
OBD_PROTOCOL      = "5"     # ISO 14230-4 KWP FAST — skip auto-detection