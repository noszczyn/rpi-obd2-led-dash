import sys, termios, tty, select, time
from controls import key_press
from car_data import VirtualCarInterface
from dashboard import update_rpm_lights, clear_panel_led

virtual_car = VirtualCarInterface()

fd = sys.stdin.fileno() # numer id (pod jakim adresem termios/select ma szukac danych)
old_settings = termios.tcgetattr(fd) # stare ustawienia terminala

try:
    tty.setcbreak(fd) # zmiana trybu terminala na cbreak(brak echo, nie czeka na klawisz "enter")
    while virtual_car.model_running:
        readable = select.select([sys.stdin], [], [], 0) # w kazdym momencie sprawdza czy klawisz został nacisniety
        if readable[0]:
            key = sys.stdin.read(1) # czyta jaki klawisz zostal wcisniety
            key_press(virtual_car, key)

        current_rpm = virtual_car.update()
        update_rpm_lights(current_rpm, virtual_car.idle_rpm, virtual_car.max_rpm, virtual_car.engine_on)
        print(f"RPM: {current_rpm} | Throttle: {virtual_car.throttle_level:.1f}")
        time.sleep(0.05)
except KeyboardInterrupt:
    print("ctrl + c")
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings) # powrót startych ustawien terminala
    clear_panel_led()

print("End simulation")