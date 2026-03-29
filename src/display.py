import time

import config
import led_strip
from math import ceil


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
        led_strip.set_pixel(i, config.COLORS["black"])


def update_rpm_lights(rpm: float, rpm_start: float, rpm_max: float) -> None:
    span = rpm_max - rpm_start
    if span <= 0:
        return
    led_factor = min(max((rpm - rpm_start) / span, 0.0), 1.0)
    total_pairs = config.LED_X // 2
    active_pairs = int(ceil(led_factor * total_pairs))

    for i in range(active_pairs):
        rpm_i_start = RPM_INDEX[i]
        rpm_i_end = RPM_INDEX[config.LED_X - 1 - i]
        color = config.COLORS["rpm_base"] if i < config.RPM_BASE_PAIRS else config.COLORS["rpm_shift"]
        led_strip.set_pixel(rpm_i_start, color)
        led_strip.set_pixel(rpm_i_end, color)


def apply_over_rev_alert(rpm: float) -> None:
    """Blink entire top RPM row red when rpm > RPM_MAX + OVER_REV_ALERT_MARGIN_RPM."""
    threshold = config.RPM_MAX + config.OVER_REV_ALERT_MARGIN_RPM
    if rpm <= threshold:
        return
    period_ms = max(1, int(config.OVER_REV_BLINK_PERIOD_SEC * 1000))
    now_ms = int(time.monotonic() * 1000)
    blink_on = (now_ms // period_ms) % 2 == 0
    c = config.COLORS["rpm_shift"] if blink_on else config.COLORS["black"]
    for idx in RPM_INDEX:
        led_strip.set_pixel(idx, c)


def update_gear_lights(gear: int) -> None:
    for i in config.GEARS_INDEX[gear]:
        led_strip.set_pixel(i, config.COLORS["gear"])
