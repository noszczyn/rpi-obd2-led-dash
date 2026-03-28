import time
import threading
import led_strip
import obd_reader
import config
from collections import deque, Counter
from display import clear_panel_led, update_rpm_lights, update_gear_lights
from gear_predictor import predict_gear
from startup_check import run_startup_animation, show_error_lights
from obd_reader import state, state_lock


# ------------------------------------------------------------------
# LED THREAD
# ------------------------------------------------------------------
gear_history = deque(maxlen=5)
gear_display = 0
running      = True
TARGET_FRAME_TIME = 0.03

def led_loop() -> None:
    global gear_display

    while running:
        frame_start = time.perf_counter()

        with state_lock:
            rpm   = state["rpm"]
            speed = state["speed"]

        gear = predict_gear(rpm, speed)
        gear_history.append(gear)

        if len(gear_history) == gear_history.maxlen:
            gear_display = Counter(gear_history).most_common(1)[0][0]

        clear_panel_led()
        update_rpm_lights(rpm, config.RPM_START, config.RPM_MAX)

        if gear_display >= 0:
            update_gear_lights(gear_display)

        led_strip.show()
        elapsed = time.perf_counter() - frame_start
        time.sleep(max(0.0, TARGET_FRAME_TIME - elapsed))


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