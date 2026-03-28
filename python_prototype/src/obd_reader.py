import obd
import threading
import config

state = {"rpm": 0, "speed": 0}
state_lock = threading.Lock()

# ------------------------------------------------------------------
# OBD CALLBACK
# ------------------------------------------------------------------
def on_rpm(response):
    if not response.is_null():
        with state_lock:
            state["rpm"] = response.value.magnitude

def on_speed(response):
    if not response.is_null():
        with state_lock:
            state["speed"] = response.value.magnitude

# ------------------------------------------------------------------
# OBD CONNECTION
# ------------------------------------------------------------------
connection = obd.Async(
    fast=config.OBD_FAST,
    timeout=config.OBD_TIMEOUT,
    check_voltage=config.OBD_CHECK_VOLTAGE,
    delay_cmds=config.OBD_DELAY_CMDS,
    protocol=config.OBD_PROTOCOL,
)

connection.watch(obd.commands.RPM,   callback=on_rpm)
connection.watch(obd.commands.RPM,   callback=on_rpm)
connection.watch(obd.commands.SPEED, callback=on_speed)