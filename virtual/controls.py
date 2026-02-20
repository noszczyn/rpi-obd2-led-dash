def key_press(car, key):
    if key == "q":
        car.model_running = False
    elif key == "w": # Throttle on
        car.throttle_level = min(1.0, car.throttle_level + 0.12)
    elif key == "e": # Engine start
        car.start_engine()
    elif key == "r": # Engine off
        car.stop_engine()