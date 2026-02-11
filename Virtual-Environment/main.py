from pynput import keyboard
from car_data import VirtualCarInterface
from time import sleep
import controls

virtual_car = VirtualCarInterface()


listener = keyboard.Listener(
    on_press=lambda key: controls.key_press(virtual_car, key), 
    on_release=lambda key: controls.key_release(virtual_car, key), 
    suppress=True
)
listener.start()

while virtual_car.model_running:
    current_rpm = virtual_car.update()
    print(f"RPM: {current_rpm} | Throttle: {virtual_car.throttle_level:.1f}")
    sleep(0.07)

print("End simulation")
listener.stop()