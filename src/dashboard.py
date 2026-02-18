import time

try:
    from rpi_ws281x import PixelStrip, Color
except ImportError:
    print("Uruchomiono w trybie symulacji (brak biblioteki rpi_ws281x)")
    from mocks import PixelStrip, Color

    