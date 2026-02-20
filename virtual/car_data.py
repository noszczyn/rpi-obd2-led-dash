import random


class VirtualCarInterface:
    def __init__(self):
        self.model_running = True

        self.engine_on = False

        self.rpm = 0
        self.idle_rpm = 750
        self.max_rpm = 7500

        self.throttle_level = 0 # Zakres 0-1(0-100%) wciskając klawisz "w"
        self.throttle_press = False

    def start_engine(self):
        self.engine_on = True
        self.throttle_level = 0.1
        print("Engine ON")

    def stop_engine(self):
        self.engine_on = False
        self.throttle_level = 0
        self.rpm = self.idle_rpm * self.throttle_level
        print("Engine OFF")
        
    def update(self):
        if self.engine_on:

            if self.throttle_level > 0.1: 
                self.throttle_level -= 0.02

                if self.throttle_level < 0.1: 
                    self.throttle_level = 0.1
        else:
            self.throttle_level = 0
            
        if self.engine_on:
            self.rpm = self.throttle_level * self.max_rpm

        return int(self.rpm)