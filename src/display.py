import time

import config
import led_strip
from math import ceil

# Mikro-optymalizacja: cache kolorów (mniej dostępu do słownika w pętli).
_C_BLACK = config.COLORS["black"]
_C_RPM_BASE = config.COLORS["rpm_base"]
_C_RPM_SHIFT = config.COLORS["rpm_shift"]
_C_OVER_REV = config.COLORS["over_rev"]
_C_GEAR = config.COLORS["gear"]


def _build_rpm_index(led_count: int, led_y: int) -> list[int]:
    rpm_index: list[int] = []
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
        led_strip.set_pixel(i, _C_BLACK)


def active_pairs_for_rpm(rpm: float, rpm_start: float, rpm_max: float) -> int:
    """Zwraca ile 'par' kolumn ma świecić pasek RPM dla zadanego rpm."""
    span = rpm_max - rpm_start
    if span <= 0:
        return 0
    led_factor = min(max((rpm - rpm_start) / span, 0.0), 1.0)
    total_pairs = config.LED_X // 2
    return int(ceil(led_factor * total_pairs))


def update_rpm_lights(rpm: float, rpm_start: float, rpm_max: float) -> None:
    active_pairs = active_pairs_for_rpm(rpm, rpm_start, rpm_max)

    for i in range(active_pairs):
        rpm_i_start = RPM_INDEX[i]
        rpm_i_end = RPM_INDEX[config.LED_X - 1 - i]
        color = _C_RPM_BASE if i < config.RPM_BASE_PAIRS else _C_RPM_SHIFT
        led_strip.set_pixel(rpm_i_start, color)
        led_strip.set_pixel(rpm_i_end, color)


def apply_over_rev_alert(rpm: float, blink_on_override: bool | None = None) -> None:
    """Blinkuj górny rząd RPM kolorem `over_rev`, ale na blink_off nie nadpisuj paska."""
    threshold = config.RPM_MAX + config.OVER_REV_ALERT_MARGIN_RPM
    if rpm <= threshold:
        return
    period_ms = max(1, int(config.OVER_REV_BLINK_PERIOD_SEC * 1000))
    if blink_on_override is None:
        now_ms = int(time.monotonic() * 1000)
        blink_on = (now_ms // period_ms) % 2 == 0
    else:
        blink_on = blink_on_override
    # Na fazie blink_off nie nadpisujemy koloru paska (zostaje to co ustawiło update_rpm_lights()).
    if not blink_on:
        return
    for idx in RPM_INDEX:
        led_strip.set_pixel(idx, _C_OVER_REV)


def update_gear_lights(gear: int) -> None:
    for i in config.GEARS_INDEX[gear]:
        led_strip.set_pixel(i, _C_GEAR)
