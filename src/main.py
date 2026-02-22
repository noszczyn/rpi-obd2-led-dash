import obd
import time
from dashboard import update_rpm_lights, predict_current_gear, strip, clear_panel_led, update_gear_lights
from car_data import RPM_MAX, RPM_START

connection = obd.Async() # auto connect to usb
connection.watch(obd.commands.RPM)
connection.watch(obd.commands.SPEED)
get_rpm = obd.commands.RPM
get_speed = obd.commands.SPEED

connection.start()

# saving rpm to optimalization
last_rpm = -1

try:
    print("script on")

    gear_history = []

    while True:
        current_rpm_obj = connection.query(get_rpm)
        current_speed_obj = connection.query(get_speed)

        if not current_rpm_obj.is_null():
            current_rpm = current_rpm_obj.value.magnitude
            current_speed = current_speed_obj.value.magnitude if not current_speed_obj.is_null() else 0

            if abs(current_rpm - last_rpm) > 10:
                clear_panel_led()

                update_rpm_lights(current_rpm, RPM_START, RPM_MAX)
                gear = predict_current_gear(rpm=current_rpm, speed=current_speed)

                if len(gear_history) > 2:
                    if len(set(gear_history)) == 1:
                        update_gear_lights(gear_history[0])
                    gear_history.pop(0)

                gear_history.append(gear)
                
                strip.show()
                last_rpm = current_rpm
        
        time.sleep(0.03)

except KeyboardInterrupt:
    print("script off")
    connection.stop()
    clear_panel_led()
    strip.show()
