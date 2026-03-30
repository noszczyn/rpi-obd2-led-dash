import time
import threading

import config
import led_strip
import obd_reader
from display import (
    apply_over_rev_alert,
    active_pairs_for_rpm,
    clear_panel_led,
    update_gear_lights,
    update_rpm_lights,
)
from gear_predictor import GearPipeline
from obd_reader import state, state_lock
from startup_check import run_startup_animation, show_error_lights

# ------------------------------------------------------------------
# LED THREAD
# ------------------------------------------------------------------
running = True


def led_loop() -> None:
    gear_pipeline = GearPipeline()
    smoothed_rpm = 0.0
    has_smoothed_rpm = False
    last_raw_rpm = 0.0
    has_last_raw_rpm = False
    last_displayed_gear = -1

    # Dirty flag: pomijamy strip.show() gdy wizualny wynik się nie zmieni.
    # Uwzględnia też fazę migania over-rev, bo wtedy top row zmienia kolor niezależnie od RPM.
    over_rev_threshold = config.RPM_MAX + config.OVER_REV_ALERT_MARGIN_RPM
    over_rev_period_ms = max(1, int(config.OVER_REV_BLINK_PERIOD_SEC * 1000))
    last_active_pairs: int | None = None
    last_gear_display: int | None = None
    last_blink_key: tuple[bool, bool] | None = None

    while running:
        frame_start = time.perf_counter()

        with state_lock:
            raw_rpm = state["rpm"]
            speed = state["speed"]

        if not has_smoothed_rpm:
            # Gdy OBD jeszcze nie zwróciło danych, raw_rpm bywa 0 i wtedy EMA łapie fałszywy transient.
            # Start EMA dopiero gdy pojawi się sensowny sygnał (raw_rpm>0 lub speed>0).
            if raw_rpm > 0.0 or speed > 0.0:
                smoothed_rpm = raw_rpm
                has_smoothed_rpm = True
        else:
            smoothed_rpm = (config.RPM_EMA_ALPHA * raw_rpm) + (
                (1.0 - config.RPM_EMA_ALPHA) * smoothed_rpm
            )

        # Precompute "what will be shown" to decide whether to call strip.show().
        active_pairs = active_pairs_for_rpm(raw_rpm, config.RPM_START, config.RPM_MAX)

        blink_active = smoothed_rpm > over_rev_threshold
        if blink_active:
            now_ms = int(time.monotonic() * 1000)
            blink_on = (now_ms // over_rev_period_ms) % 2 == 0
        else:
            blink_on = False
        blink_key = (blink_active, blink_on)

        gear_display = gear_pipeline.step(
            raw_rpm,
            speed,
            last_displayed_gear,
            has_last_raw_rpm,
            last_raw_rpm,
        )
        if gear_display >= 0:
            last_displayed_gear = gear_display

        last_raw_rpm = raw_rpm
        has_last_raw_rpm = True

        clear_panel_led()
        update_rpm_lights(raw_rpm, config.RPM_START, config.RPM_MAX)

        if gear_display >= 0:
            update_gear_lights(gear_display)

        apply_over_rev_alert(
            smoothed_rpm,
            blink_on_override=blink_on if blink_active else None,
        )

        dirty = (
            active_pairs != last_active_pairs
            or gear_display != last_gear_display
            or blink_key != last_blink_key
        )
        if dirty:
            led_strip.show()
            last_active_pairs = active_pairs
            last_gear_display = gear_display
            last_blink_key = blink_key
        elapsed = time.perf_counter() - frame_start
        time.sleep(max(0.0, config.TARGET_FRAME_TIME_SEC - elapsed))


# ------------------------------------------------------------------
# START
# ------------------------------------------------------------------
led_thread = None
_obd_started = False

try:
    obd_reader.connection.start()
    _obd_started = True

    if obd_reader.connection.is_connected():
        run_startup_animation()
        clear_panel_led()
        led_strip.show()

        led_thread = threading.Thread(target=led_loop, daemon=True)
        led_thread.start()

        while led_thread.is_alive():
            time.sleep(0.1)
        if running:
            raise RuntimeError("led_loop exited unexpectedly")
    else:
        print(
            "OBD: no adapter or no link (see journalctl). "
            "Red pattern = error. Set OBD_PORT in config.py if needed. "
            "Plug ELM327 USB and: sudo systemctl restart dash-dashboard.service",
            flush=True,
        )
        show_error_lights()
        while True:
            time.sleep(3600)

except KeyboardInterrupt:
    running = False
finally:
    if led_thread is not None:
        led_thread.join(timeout=3.0)
    if _obd_started:
        try:
            obd_reader.connection.stop()
        except Exception:
            pass
    try:
        clear_panel_led()
        led_strip.show()
    except Exception:
        pass
