#include "LedStrip.hpp"
#include <cstring>
#include <iostream>

LedStrip::LedStrip() : m_initialized(false) {
    std::memset(&m_led_string, 0, sizeof(ws2811_t));

    m_led_string.freq = Config::LED_FREQ_HZ;
    m_led_string.dmanum = Config::LED_DMA;

    m_led_string.channel[0].gpionum = Config::LED_PIN; 
    m_led_string.channel[0].count = Config::LED_COUNT;
    m_led_string.channel[0].invert = Config::LED_INVERT ? 1 : 0;
    m_led_string.channel[0].brightness = Config::LED_BRIGHTNESS;
    m_led_string.channel[0].strip_type = WS2811_STRIP_GRB;

    m_led_string.channel[1].gpionum = 0;
    m_led_string.channel[1].count = 0;
    m_led_string.channel[1].brightness = 0;
}

LedStrip::~LedStrip(){
    if (m_initialized) {
        clear();
        show();
        ws2811_fini(&m_led_string);
    }
}

bool LedStrip::begin(){
    ws2811_return_t ret = ws2811_init(&m_led_string);

    if (ret != WS2811_SUCCESS) {
        std::cerr << "LED matrix initialization failed: " << ws2811_get_return_t_str(ret) << "\n";
        return false;
    }
    m_initialized = true;
    return true;
}

ws2811_led_t LedStrip::pack_color(uint8_t r, uint8_t g, uint8_t b) {
    return (r << 16) | (g << 8) | b;
}

void LedStrip::set_pixel(int index, uint8_t r, uint8_t g, uint8_t b){
    if (m_led_string.channel[0].leds != nullptr && index >= 0 && index < Config::LED_COUNT) {
        m_led_string.channel[0].leds[index] = pack_color(r, g, b);
    }
}

void LedStrip::show() {
    if (!m_initialized) {
        return;
    }

    ws2811_return_t ret = ws2811_render(&m_led_string);
    if (ret != WS2811_SUCCESS) {
        std::cerr << "LED render failed: " << ws2811_get_return_t_str(ret) << "\n";
    }
}

void LedStrip::clear() {
    if (m_led_string.channel[0].leds != nullptr) {
        std::memset(m_led_string.channel[0].leds, 0, Config::LED_COUNT * sizeof(ws2811_led_t));
    }
}