import obd
import time

data = open("ratio_data.csv", 'a')

connection = obd.OBD() # auto connect to usb
get_rpm = obd.commands.RPM
get_speed = obd.commands.SPEED

while True:
    rpm = connection.query(get_rpm)
    speed = connection.query(get_speed)
    if not rpm.is_null() and not speed.is_null():
        rpm_raw = rpm.value.magnitude
        speed_raw = speed.value.magnitude
        if speed_raw <= 5:
            ratio = 0
        else:
            ratio = rpm_raw / speed_raw

        data.write(f"RPM: {rpm_raw}, SPEED: {speed_raw}, RATIO: {ratio}\n")
        data.flush()
    time.sleep(1)
    