import config
import led_strip
from math import ceil

def _build_rpm_index(led_count: int, led_y: int) -> list[int]:
    rpm_index = []
    for i in range(led_count):
        column = i // led_y
        row = i % led_y
        if column % 2 == 1:
            row = led_y - 1 - row
        if row == 0:
            rpm_index.append(i)
    
    return rpm_index

RPM_INDEX = _build_rpm_index(config.LED_COUNT, config.LED_Y)

def clear_panel_led() -> None:
    for i in range(config.LED_COUNT):
        led_strip.set_pixel(i, config.COLORS["black"])

def update_rpm_lights(rpm: float, rpm_start: int, rpm_max: int) -> None:
    led_factor = min(max((rpm - rpm_start) / (rpm_max - rpm_start), 0), 1) # FACTOR (RANGE 0-1)
    active_pairs = int(ceil(led_factor * (config.LED_Y / 2)))

    for i in range(active_pairs):
        rpm_i_start = RPM_INDEX[i]
        rpm_i_end = RPM_INDEX[-1 - i]
        
        if i < config.RPM_BASE_PAIRS:
            color = config.COLORS["rpm_base"]
        else:
            color = config.COLORS["rpm_shift"]    

        led_strip.set_pixel(rpm_i_start, color)
        led_strip.set_pixel(rpm_i_end, color)

def update_gear_lights(gear: int) -> None:
    for i in config.GEARS_INDEX[gear]:
        led_strip.set_pixel(i, config.COLORS["gear"])