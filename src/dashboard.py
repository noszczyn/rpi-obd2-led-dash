from rpi_ws281x import PixelStrip, Color
from car_data import gears_ratios
import math

# Konfiguracja panelu led
LED_X, LED_Y = 8, 8
LED_COUNT = LED_X * LED_Y # liczba diod
LED_PIN = 18 # GPIO
LED_FREQ_HZ = 800000
LED_DMA = 10 # kanał dma
LED_INVERT = False # odwrocenie sygnału
LED_BRIGHTNESS = 10 # jasnosc (0-255)
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

colors = {
    "gear": Color(255, 80, 0),         # bursztyn
    "throttle": Color(80, 0, 0),       # ciemny czerowny
    "rpm_base": Color(255, 80, 0),     # bursztyn
    "rpm_shift": Color(255, 0, 0),     # czerowny
    "black": Color(0, 0, 0)
}

# Indeksy gotowych biegow do wyswietlenia
GEARS_INDEX = {
    -1: [],
    0: [24,25,26,27,28,29,30,34,35,43,53,54,56,57,58,59,60,61,62], # neutral
    1: [24,28,34,39,40,41,42,43,44,45,46,55,56],
    2: [24,25,29,33,37,39,40,43,46,49,51,55,56,61],
    3: [25,29,33,39,40,43,46,49,52,55,57,58,60,61],
    4: [27,28,34,36,43,46,49,50,51,52,53,54,55,59],
    5: [25,27,28,29,30,33,36,39,40,43,46,49,52,55,57,58,59,62],
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
        strip.setPixelColor(i, colors["black"])

def update_rpm_lights(rpm, rpm_start, rpm_max):
    led_factor = min(max((rpm - rpm_start) / (rpm_max - rpm_start), 0), 1) # wspolczynnik (zakres 0-1)
    column_active = int(led_factor * LED_Y) # zakres 0-8 kolumny

    for i in range(column_active // 2):
        rpm_i_start = RPM_INDEX[i]
        rpm_i_end = RPM_INDEX[-1 - i]
        
        if i < 3:
            color = colors["rpm_base"]
        else:
            color = colors["rpm_shift"]    

        strip.setPixelColor(rpm_i_start, color)
        strip.setPixelColor(rpm_i_end, color)

def update_gear_lights(gear):
    for i in GEARS_INDEX[gear]:
        strip.setPixelColor(i, colors["gear"])

def predict_current_gear(rpm, speed):
    neutral_speed_limiter = 3 # aby uniknac dzielenia przez 0, dodaje ogranicznik kiedy ma byc neutral

    if speed < neutral_speed_limiter:
        predicted_gear = 0
    else:
        current_ratio = rpm / speed
        ratio_delta = float("inf")
        
        predicted_gear = -1

        for gear, gear_ratio in gears_ratios.items():
            deviation = abs(current_ratio - gear_ratio)
            gear_tolerance =  gear_ratio * 0.2 # maksymalne dozwolone odchylenie 

            if deviation < gear_tolerance and deviation < ratio_delta:
                ratio_delta = deviation
                predicted_gear = gear

    return predicted_gear

def update_throttle_position(throttle):
    bar_length = 7
    bar_progress = int(min(throttle // 14, bar_length)) # ograniczenie gdyby mialo byc jakims cudem 8
    bottom_led_index = LED_Y - 1 # progres od dolu do gory

    for i in range(bar_progress):
        current_led = bottom_led_index - i
        strip.setPixelColor(current_led, colors["throttle"])