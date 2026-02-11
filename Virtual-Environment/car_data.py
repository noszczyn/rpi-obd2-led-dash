import random
from pynput import keyboard


class VirtualCarInterface:
    def __init__(self):
        self.model_running = True

        self.engine_on = False

        self.rpm = 0
        self.idle_rpm = 800
        self.max_rpm = 7800

        self.throttle_level = 0 # Zakres 0-1(0-100%) wciskając klawisz "w"
        self.throttle_press = False

    def start_engine(self):
        self.engine_on = True
        self.throttle_level = 0.1
        print("Engine ON")

    def stop_engine(self):
        self.engine_on = False
        self.rpm = 0
        self.throttle_level = 0
        print("Engine OFF")
    
    def decrease_throttle(self):
        if self.throttle_level > 0.1: 
            self.throttle_level -= 0.1

            if self.throttle_level < 0.1: 
                self.throttle_level = 0.1
        
    def update(self):
        if self.engine_on:
            if self.throttle_press:
                if self.throttle_level < 0.9: self.throttle_level += 0.1
            else:
                if self.throttle_level > 0.1: 
                    self.throttle_level -= 0.1

                    if self.throttle_level < 0.1: 
                        self.throttle_level = 0.1
        else:
            self.throttle_level = 0
            
        if self.engine_on:
            swing = random.uniform(-0.001, 0.001) # "szum" w obrotach
            self.rpm = (self.throttle_level + swing) * self.max_rpm
        else:
            self.rpm = 0

        return int(self.rpm)