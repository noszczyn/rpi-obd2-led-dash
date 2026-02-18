class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

class PixelStrip:
    def __init__(self, num, pin, freq_hz=800000, dma=10, invert=False, brightness=255, channel=0):
        self.num = num
        print(f"[MOCK] Inicjalizacja paska LED: {num} diod na pinie {pin}")

    def begin(self):
        print("[MOCK] Pasek wystartował")

    def show(self):
        # Na Macu tylko wypisujemy, że coś się dzieje
        pass 

    def setPixelColor(self, n, color):
        # Tutaj nic nie robimy, żeby nie spamować konsoli
        pass

    def numPixels(self):
        return self.num