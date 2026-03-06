import config
from rpi_ws281x import PixelStrip, Color

strip = PixelStrip(
    config.LED_COUNT,
    config.LED_PIN,
    config.LED_FREQ_HZ,
    config.LED_DMA,
    config.LED_INVERT,
    config.LED_BRIGHTNESS,
    config.LED_CHANNEL, 
)

def show() -> None:
    strip.show()

def set_pixel(index: int, color) -> None:
    strip.setPixelColor(index, color)

strip.begin()