#pragma once
#include "Config.hpp"

extern "C" {
    #include <ws2811.h>
}

class LedStrip{
    public:
        LedStrip();
        ~LedStrip();

        bool begin();

        void set_pixel(int index, uint8_t r, uint8_t g, uint8_t b);
        void show();
        void clear();
    private:
        ws2811_t m_led_string;
        bool m_initialized;
        ws2811_led_t pack_color(uint8_t r, uint8_t g, uint8_t b);
};