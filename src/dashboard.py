import math

try:
    from rpi_ws281x import PixelStrip, Color
except ImportError:
    print("Uruchomiono w trybie symulacji (brak biblioteki rpi_ws281x)")
    from mocks import PixelStrip, Color

# Konfiguracja panelu led
led_x, led_y = 8, 32
LED_COUNT = led_x * led_y # liczba dio
LED_PIN = 18 # GPIO
LED_FREQ_HZ = 800000
LED_DMA = 10 # kanał dma
LED_INVERT = False # odwrocenie sygnału
LED_BRIGHTNESS = 20 # jasnosc
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

rpm_colors = (Color(0, 255, 0), Color(255, 0, 0), Color(0, 0, 255)) # zielony, czerowny, niebieski

def update_rpm_lights(rpm, rpm_idle, rpm_max, is_engine_on):
    led_factor = max((rpm - rpm_idle) / (rpm_max - rpm_idle), 0) # wspolczynnik (zakres 0-1)
    led_active = int(min(led_factor, 1) * LED_COUNT) # ilosc aktywnych diod(sa to indeksy)
    column_active = int(led_factor * led_y) # zakres 0-32 kolumny

    if is_engine_on:
        for i in range(LED_COUNT):
            current_column = i // 8 # ile ma byc aktualnie zaswieconych kolumn
            color_index = math.floor(current_column * len(rpm_colors) / led_y)
            
            if current_column <= column_active:
                strip.setPixelColor(i, rpm_colors[color_index])
            else:
                strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

def clear_panel_led():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()