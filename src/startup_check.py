import time

import config
import led_strip


def run_startup_animation() -> None:
    for i in range(config.LED_COUNT):
        led_strip.set_pixel(i, config.COLORS["gear"])
        led_strip.show()
        time.sleep(0.05)


def show_error_lights() -> None:
    message = [24, 25, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38, 39]
    for i in message:
        led_strip.set_pixel(i, config.COLORS["over_rev"])
    led_strip.show()
