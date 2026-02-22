from rpi_ws281x import PixelStrip, Color
import time

# Konfiguracja panelu led
led_x, led_y = 8, 32
LED_COUNT = led_x * led_y # liczba diod
LED_PIN = 18 # GPIO
LED_FREQ_HZ = 800000
LED_DMA = 10 # kanał dma
LED_INVERT = False # odwrocenie sygnału
LED_BRIGHTNESS = 50 # jasnosc (0-255)
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
    0: [113, 114, 115, 116, 117, 118, 119, 124, 125, 132, 138, 137, 145, 146, 147, 148, 149, 150, 151], # neutral
    1: [115, 119, 120,125,129,130,131,132,133,134,135,136, 151],
    2: [114,118,119,120,122,126,129,132,135,136,140,142,146,151],
    3: [114,118,120,126,129,135,136,139,142,146,147,149,150, 132],
    4: [115,116,123,125,129,132,136,137,138,139,140,141,142,148],
    5: [113,114,115,118,120,124,126,129,131,135,136,140,142, 145, 148,149,150],
}


def gear_update(gear):
    for i in gears[gear]:
        strip.setPixelColor(i, Color(255, 255, 255))
    strip.show()

def clear_led():
    for i in range(256):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

clear_led()

loop = False

while loop:
    for i in range(-1, 7):
        gear_update(i)
        time.sleep(1)
        clear_led()
