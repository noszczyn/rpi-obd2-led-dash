import time
from dashboard import *

def led_system_check():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(255, 80, 0))
        strip.show()
        time.sleep(0.05)

def error_system():
    message = [24,25,27,28,29,30,31,32,33,34,35,36,38,39]
    for i in message:
        strip.setPixelColor(i, Color(255, 0, 0))

    strip.show()
