def key_press(car, key):
    try:
        if key.char == "q":
            car.model_running = False
        elif key.char == "w": # Throttle on
            car.throttle_press = True
        elif key.char == "e": # Engine start
            car.start_engine()
        elif key.char == "r": # Engine off
            car.stop_engine()
    except AttributeError:
        pass

def key_release(car, key):
    try:
        if key.char == "w": # Throttle off
            car.throttle_press = False
    except AttributeError:
        pass