from rpi_ws281x import PixelStrip, Color
from car_data import gears_ratios
import math

# Konfiguracja panelu led
LED_X, LED_Y = 8, 32
LED_COUNT = LED_X * LED_Y # liczba diod
LED_PIN = 18 # GPIO
LED_FREQ_HZ = 800000
LED_DMA = 10 # kanał dma
LED_INVERT = False # odwrocenie sygnału
LED_BRIGHTNESS = 20 # jasnosc (0-255)
LED_CHANNEL = 0 # kanał PWM

strip = PixelStrip(
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
    LED_CHANNEL, 
)
# inicjalizacja
strip.begin()

# Indeksy gotowych biegow do wyswietlenia
GEARS_INDEX = {
    -1: [116, 123, 132, 139, 148],
    0: [113, 114, 115, 116, 117, 118, 119, 124, 125, 132, 138, 137, 145, 146, 147, 148, 149, 150, 151], # neutral
    1: [115, 119, 120,125,129,130,131,132,133,134,135,136, 151],
    2: [114,118,119,120,122,126,129,132,135,136,140,142,146,151],
    3: [114,118,120,126,129,135,136,139,142,146,147,149,150, 132],
    4: [115,116,123,125,129,132,136,137,138,139,140,141,142,148],
    5: [113,114,115,118,120,124,126,129,131,135,136,140,142, 145, 148,149,150],
    6: [113, 114,115,116,117,118, 119, 123, 126, 129, 132, 139, 142, 146, 147, 149,150, 151] # reverse
}
# Indeksy zerowego wiersza do rpm indicator
RPM_INDEX = []
for i in range(LED_COUNT):
    column = i // 8 
    row = i % 8
    if column % 2 == 1: # diody polaczone w "wezyk"
        row = 7 - row

    if row == 0:
        RPM_INDEX.append(i)

def clear_panel_led():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

def update_rpm_lights(rpm, rpm_start, rpm_max):
    led_factor = max((rpm - rpm_start) / (rpm_max - rpm_start), 0) # wspolczynnik (zakres 0-1)
    column_active = int(led_factor * LED_Y) # zakres 0-32 kolumny

    for i in range(column_active)
        rpm_i = RPM_INDEX[i]
        #color_index = min(math.floor(col * len(rpm_colors) / led_y), 2) # podzial rpm na 3 czesci, wybor indexu do koloru
        strip.setPixelColor(rpm_i, Color(255, 0, 0))

def update_gear_lights(gear):
    for i in GEARS_INDEX[gear]:
        strip.setPixelColor(i, Color(255, 0, 0))

def predict_current_gear(rpm, speed):
    neutral_speed_limiter = 5 # aby uniknac dzielenia przez 0, dodaje ogranicznik kiedy ma byc neutral
    gear_tolerance = 15 # maksymalne dozwolone odchylenie 

    if speed < neutral_speed_limiter:
        predicted_gear = 0
    else:
        current_ratio = rpm / speed
        ratio_delta = float("inf")

        predicted_gear = -1

        for gear, gear_ratio in gears_ratios.items():
            devation = abs(current_ratio - gear_ratio)

            if devation < gear_tolerance and devation < ratio_delta:
                ratio_delta = devation
                predicted_gear = gear

    update_gear_lights(predicted_gear)