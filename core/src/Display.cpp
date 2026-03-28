#include "Display.hpp"
#include <algorithm>
#include <cmath>

Display::Display(LedStrip& led_strip) : m_led_strip(led_strip) {
    build_rpm_index();
}

void Display::clear_panel_led(){
    m_led_strip.clear();
}

void Display::build_rpm_index(){
    int index_counter = 0;
    for (int i = 0; i < Config::LED_COUNT; i++) {
        int column = i / Config::LED_Y;
        int row = i % Config::LED_Y;
        if (column % 2 == 1) {
            row = (Config::LED_Y - 1) - row;
        }
        if (row == 0 && index_counter < static_cast<int>(m_rpm_led_indices.size())) {
            m_rpm_led_indices[index_counter] = i;
            index_counter++;
        }
    }
}

void Display::clear_rpm_lights() {
    for (int led_index : m_rpm_led_indices) {
        m_led_strip.set_pixel(led_index, Config::OFF.r, Config::OFF.g, Config::OFF.b);
    }
}

void Display::clear_gear_lights() {
    for (const auto& [gear, led_indices] : Config::GEARS_INDEX) {
        if (gear < 0) {
            continue;
        }
        for (int led_index : led_indices) {
            m_led_strip.set_pixel(led_index, Config::OFF.r, Config::OFF.g, Config::OFF.b);
        }
    }
}

void Display::update_rpm_lights(float current_rpm){
    clear_rpm_lights();

    const float rpm_span = Config::MAX_RPM - Config::START_RPM;
    if (rpm_span <= 0.0f) {
        return;
    }

    const float led_factor = std::clamp((current_rpm - Config::START_RPM) / rpm_span, 0.0f, 1.0f);
    const int total_pairs = Config::LED_X / 2;
    const int active_pairs = static_cast<int>(std::ceil(led_factor * total_pairs));

    for (int i = 0; i < active_pairs; i++) {
        const int rpm_i_start = m_rpm_led_indices[i];
        const int rpm_i_end = m_rpm_led_indices[Config::LED_X - 1 - i];
        const Color& color = (i < Config::RPM_BASE_PAIRS) ? Config::AMBER : Config::RED;

        m_led_strip.set_pixel(rpm_i_start, color.r, color.g, color.b);
        m_led_strip.set_pixel(rpm_i_end, color.r, color.g, color.b);
    }
}

void Display::update_gear_lights(int gear) {
    clear_gear_lights();

    const auto gear_it = Config::GEARS_INDEX.find(gear);
    if (gear_it == Config::GEARS_INDEX.end()) {
        return;
    }

    for (int led_index : gear_it->second) {
        m_led_strip.set_pixel(led_index, Config::AMBER.r, Config::AMBER.g, Config::AMBER.b);
    }
}