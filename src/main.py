import obd
import time
from dashboard import update_rpm_lights, predict_current_gear, strip, clear_panel_led
from car_data import RPM_MAX, RPM_START

connection = obd.OBD() # auto connect to usb
get_rpm = obd.commands.RPM
get_speed = obd.commands.SPEED

while True:
    current_rpm = connection.query(get_rpm)
    current_speed = connection.query(get_speed)
    if not current_rpm.is_null():
        clear_panel_led()
        update_rpm_lights(current_rpm.value.magnitude, RPM_START, RPM_MAX)
        if not current_speed.is_null():
            predict_current_gear(rpm=current_rpm.value.magnitude, speed=current_speed.value.magnitude)
        strip.show()
    sleep.time(0.1)
