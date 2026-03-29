import threading

import obd

import config

state = {"rpm": 0.0, "speed": 0.0}
state_lock = threading.Lock()

_obd_port = config.OBD_PORT if config.OBD_PORT else None


def on_rpm(response):
    if not response.is_null():
        with state_lock:
            state["rpm"] = float(response.value.magnitude)


def on_speed(response):
    if not response.is_null():
        with state_lock:
            state["speed"] = float(response.value.magnitude)


connection = obd.Async(
    _obd_port,
    fast=config.OBD_FAST,
    timeout=config.OBD_TIMEOUT,
    check_voltage=config.OBD_CHECK_VOLTAGE,
    delay_cmds=config.OBD_DELAY_CMDS,
    protocol=config.OBD_PROTOCOL,
)

connection.watch(obd.commands.RPM, callback=on_rpm)
connection.watch(obd.commands.RPM, callback=on_rpm)
connection.watch(obd.commands.SPEED, callback=on_speed)
