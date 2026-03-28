#pragma once
#include <array>
#include <vector>
#include <map>
#include <cstdint>

struct Color {
    uint8_t r;
    uint8_t g;
    uint8_t b;
};

namespace Config {
    // RPM PARAMETERS — SUZUKI SWIFT 2008
    constexpr float MAX_RPM = 5000.0; // RPM at which LED indicator ends
    constexpr float START_RPM = 3000.0; // RPM at which LED indicator starts
    constexpr int RPM_BASE_PAIRS = 3; // LED pairs shown in base color before shift color

    // GEAR PREDICTOR PARAMETERS
    constexpr int NEUTRAL_SPEED_LIMIT = 3;
    constexpr float GEAR_TOLERANCE = 0.2;

    inline constexpr std::array<float, 6> GEARS_RATIOS = {0.0, 133.0, 73.0, 49.0, 37.0, 29.0};

    // MATRIX LED WS2812B PARAMETERS
    constexpr int LED_X = 8;
    constexpr int LED_Y = 8;
    constexpr int LED_COUNT = LED_X * LED_Y;
    constexpr int LED_PIN = 18; // GPIO pin
    constexpr int LED_FREQ_HZ = 800000; // LED signal frequency (Hz)
    constexpr int LED_DMA = 10; // DMA channel
    constexpr int LED_BRIGHTNESS = 30; // brightness (0-255)
    constexpr int LED_CHANNEL = 0; // PWM channel
    constexpr bool LED_INVERT = false; // invert signal (for NPN transistor)

    // COLORS
    constexpr Color AMBER = {255, 80, 0};
    constexpr Color RED = {255, 40, 0}; 
    constexpr Color OFF = {0, 0, 0};

    // GEAR DISPLAY INDICES — LED MATRIX
    inline const std::map<int, std::vector<int>> GEARS_INDEX = {
        {-1, {}},
        {0,  {24,25,26,27,28,29,30,34,35,43,53,54,56,57,58,59,60,61,62}},
        {1,  {24,28,34,39,40,41,42,43,44,45,46,55,56}},
        {2,  {24,25,29,33,37,39,40,43,46,49,51,55,56,61}},
        {3,  {25,29,33,39,40,43,46,49,52,55,57,58,60,61}},
        {4,  {27,28,34,36,43,46,49,50,51,52,53,54,55,59}},
        {5,  {25,27,28,29,30,33,36,39,40,43,46,49,52,55,57,58,59,62}},
    };
}
