from rpi_ws281x import PixelStrip, Color
import time

# Konfiguracja panelu led
led_x, led_y = 8, 32
LED_COUNT = led_x * led_y # liczba diod
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

gears = {
    -1: [],
    0: [24,25,26,27,28,29,30,34,35,43,53,54,56,57,58,59,60,61,62], # neutral
    1: [24,28,34,39,40,41,42,43,44,45,46,55,56],
    2: [24,25,29,33,37,39,40,43,46,49,51,55,56,61],
    3: [25,29,33,39,40,43,46,49,52,55,57,58,60,61],
    4: [27,28,34,36,43,46,49,50,51,52,53,54,55,59],
    5: [25,27,28,29,30,33,36,39,40,43,46,49,52,55,57,58,59,62],
}
# GEARS_INDEX = {
#     -1: [116, 123, 132, 139, 148],
#     0: [113, 114, 115, 116, 117, 118, 119, 124, 125, 132, 138, 137, 145, 146, 147, 148, 149, 150, 151], # neutral
#     1: [115, 119, 120,125,129,130,131,132,133,134,135,136, 151],
#     2: [114,118,119,120,122,126,129,132,135,136,140,142,146,151],
#     3: [114,118,120,126,129,135,136,139,142,146,147,149,150, 132],
#     4: [115,116,123,125,129,132,136,137,138,139,140,141,142,148],
#     5: [113,114,115,118,120,124,126,129,131,135,136,140,142, 145, 148,149,150],
#     6: [113, 114,115,116,117,118, 119, 123, 126, 129, 132, 139, 142, 146, 147, 149,150, 151] # reverse
# }


def gear_update(gear):
    for i in gears[gear]:
        strip.setPixelColor(i, Color(255, 40, 0))
    strip.show()

def clear_led():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

clear_led()

loop = False

while loop:
    for i in range(-1, 6):
        gear_update(i)
        time.sleep(1)
        clear_led()

clear_led()
#gear_update(5)
