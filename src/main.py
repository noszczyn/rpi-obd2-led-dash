import time
import threading

import config
import led_strip
import obd_reader
from collections import Counter, deque
from display import (
    apply_over_rev_alert,
    clear_panel_led,
    update_gear_lights,
    update_rpm_lights,
)
from gear_predictor import predict_gear
from obd_reader import state, state_lock
from startup_check import run_startup_animation, show_error_lights

# ------------------------------------------------------------------
# LED THREAD
# ------------------------------------------------------------------
gear_history = deque(maxlen=5)
gear_display = 0
running = True


def led_loop() -> None:
    global gear_display

    smoothed_rpm = 0.0
    has_smoothed_rpm = False
    last_raw_rpm = 0.0
    has_last_raw_rpm = False
    last_displayed_gear = -1

    while running:
        frame_start = time.perf_counter()

        with state_lock:
            raw_rpm = state["rpm"]
            speed = state["speed"]

        if not has_smoothed_rpm:
            smoothed_rpm = raw_rpm
            has_smoothed_rpm = True
        else:
            smoothed_rpm = (config.RPM_EMA_ALPHA * raw_rpm) + (
                (1.0 - config.RPM_EMA_ALPHA) * smoothed_rpm
            )

        predicted_gear = predict_gear(raw_rpm, speed)
        if (
            last_displayed_gear > 0
            and predicted_gear > last_displayed_gear
            and has_last_raw_rpm
            and (raw_rpm - last_raw_rpm) > config.RPM_RISE_DOWNSHIFT_GUARD
        ):
            predicted_gear = last_displayed_gear

        gear_history.append(predicted_gear)
        if len(gear_history) == gear_history.maxlen:
            gear_display = Counter(gear_history).most_common(1)[0][0]

        last_raw_rpm = raw_rpm
        has_last_raw_rpm = True

        clear_panel_led()
        update_rpm_lights(smoothed_rpm, config.RPM_START, config.RPM_MAX)

        if gear_display >= 0:
            update_gear_lights(gear_display)
            last_displayed_gear = gear_display

        apply_over_rev_alert(raw_rpm)

        led_strip.show()
        elapsed = time.perf_counter() - frame_start
        time.sleep(max(0.0, config.TARGET_FRAME_TIME_SEC - elapsed))


# ------------------------------------------------------------------
# START
# ------------------------------------------------------------------
led_thread = None

try:
    obd_reader.connection.start()

    if obd_reader.connection.is_connected():
        run_startup_animation()
        clear_panel_led()
        led_strip.show()

        led_thread = threading.Thread(target=led_loop, daemon=True)
        led_thread.start()

        while led_thread.is_alive():
            time.sleep(0.1)
    else:
        show_error_lights()

except KeyboardInterrupt:
    running = False
    if led_thread is not None:
        led_thread.join()
    obd_reader.connection.stop()
    clear_panel_led()
    led_strip.show()
