import obd
import time
from dashboard import update_rpm_lights, predict_current_gear, strip, clear_panel_led, update_gear_lights, update_throttle_position
from car_data import RPM_MAX, RPM_START
from startup_check import led_system_check, error_system

connection = obd.Async() # auto connect to usb
connection.watch(obd.commands.RPM)
connection.watch(obd.commands.SPEED)
connection.watch(obd.commands.THROTTLE_POS)
get_rpm = obd.commands.RPM
get_speed = obd.commands.SPEED
get_throttle = obd.commands.THROTTLE_POS

connection.start()

try:
    gear_history = []
    gear_display = 0
    last_rpm = 0

    if connection.is_connected():
        led_system_check()
        clear_panel_led()
        strip.show()

        while True:
            current_rpm_obj = connection.query(get_rpm)
            current_speed_obj = connection.query(get_speed)
            current_throttle_obj = connection.query(get_throttle)

            if not current_rpm_obj.is_null():
                current_rpm = current_rpm_obj.value.magnitude
                current_speed = current_speed_obj.value.magnitude if not current_speed_obj.is_null() else 0
                current_throttle = current_throttle_obj.value.magnitude if not current_throttle_obj.is_null() else 0

                if abs(current_rpm - last_rpm) > 10:
                    gear = predict_current_gear(rpm=current_rpm, speed=current_speed)

                    if len(gear_history) > 2:
                        if len(set(gear_history)) == 1:
                            gear_display = gear_history[0]
                        gear_history.pop(0)

                    gear_history.append(gear)
                    last_rpm = current_rpm

                clear_panel_led()

                update_rpm_lights(current_rpm, RPM_START, RPM_MAX)

                if gear_display >= 0:
                    update_gear_lights(gear_display)

                update_throttle_position(current_throttle)

                strip.show()
            time.sleep(0.03)
    else:
        error_system()
        
except KeyboardInterrupt:
    connection.stop()
    clear_panel_led()
    strip.show()
