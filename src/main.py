import obd
from dashboard import update_rpm_lights

# Parametry suzuki swift (odcina paliw0 przy 6500rpm)
RPM_MAX = 6500
RPM_START = 1000 # od ilu rpm ma pokazywac ledy


connection = obd.OBD() # auto connect to usb
get_rpm = obd.commands.RPM
get_speed = obd.commands.SPEED

while True:
    current_rpm = connection.query(get_rpm)
    if not current_rpm.is_null():
        update_rpm_lights(current_rpm.value.magnitude, RPM_START, RPM_MAX)