import obd
import time

connection = obd.OBD() # auto connect to usb
print(connection.status())

cmd = obd.commands.RPM

while True:
    response = connection.query(cmd)
    print(f"RPM: {response.value}")

    time.sleep(3)
