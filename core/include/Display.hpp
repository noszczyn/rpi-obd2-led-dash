#pragma once
#include "Config.hpp"
#include "LedStrip.hpp"
#include <array>

class Display {
    public:
        Display(LedStrip& led_strip);

        void clear_panel_led();

        void update_rpm_lights(float current_rpm);
        void update_gear_lights(int current_gear);
        void set_top_row_alert(bool enabled);
    private:
        LedStrip& m_led_strip;

        std::array<int, Config::LED_X> m_rpm_led_indices{};

        void build_rpm_index();
        void clear_rpm_lights();
        void clear_gear_lights();
};
