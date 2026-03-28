#include <csignal>
#include <chrono>
#include <iostream>
#include <thread>

#include "Config.hpp"
#include "LedStrip.hpp"
#include "Display.hpp"
#include "ObdReader.hpp"
#include "GearPredictor.hpp"

volatile std::sig_atomic_t g_running = 1;

void handle_sigint(int sig) {
    (void)sig;
    std::cout << "\n[SIGNAL] Interrupt received. Shutting down safely...\n";
    g_running = 0;
}

int main() {
    using clock = std::chrono::steady_clock;
    using namespace std::chrono_literals;

    constexpr float kRpmEmaAlpha = 0.20f;
    constexpr int kMaxConsecutiveFrameMisses = 20;
    constexpr auto kLoopTimeWithValidData = 40ms;
    constexpr auto kLoopTimePartialData = 60ms;
    constexpr auto kLoopTimeNoData = 100ms;

    std::signal(SIGINT, handle_sigint);

    std::cout << "--- SUZUKI SWIFT TELEMETRY START ---\n";

    LedStrip led_strip;
    if (!led_strip.begin()) {
        std::cerr << "CRITICAL ERROR: failed to initialize LED matrix.\n";
        std::cerr << "Make sure you run this program with 'sudo'.\n";
        return 1;
    }

    Display display(led_strip);
    GearPredictor predictor;

    ObdReader obd("/dev/ttyUSB0");

    if (!obd.connect()) {
        std::cerr << "Cannot connect to OBD adapter. Exiting.\n";
        return 1; // LedStrip destructor turns LEDs off on exit.
    }

    if (!obd.initialize()) {
        std::cerr << "OBD adapter initialization failed. Exiting.\n";
        return 1;
    }

    std::cout << "Connection established. Starting real-time loop...\n";

    int consecutive_frame_misses = 0;
    bool failsafe_active = false;
    bool has_smoothed_rpm = false;
    float smoothed_rpm = 0.0f;

    while (g_running) {
        const auto loop_start = clock::now();

        auto opt_rpm = obd.get_rpm();
        auto opt_speed = obd.get_speed();

        int predicted_gear = -1;

        if (opt_rpm.has_value()) {
            if (!has_smoothed_rpm) {
                smoothed_rpm = *opt_rpm;
                has_smoothed_rpm = true;
            } else {
                smoothed_rpm = (kRpmEmaAlpha * (*opt_rpm)) + ((1.0f - kRpmEmaAlpha) * smoothed_rpm);
            }
        }

        const bool frame_valid = opt_rpm.has_value() && opt_speed.has_value();

        if (frame_valid) {
            consecutive_frame_misses = 0;
            if (failsafe_active) {
                std::cout << "OBD data stream recovered.\n";
            }
            failsafe_active = false;
            predicted_gear = predictor.gear_predict(smoothed_rpm, *opt_speed);
        } else {
            consecutive_frame_misses++;
        }

        if (consecutive_frame_misses >= kMaxConsecutiveFrameMisses) {
            if (!failsafe_active) {
                std::cerr << "Failsafe: no valid OBD frames, turning LEDs off.\n";
                failsafe_active = true;
            }

            display.clear_panel_led();
            led_strip.show();

            const auto elapsed = clock::now() - loop_start;
            if (elapsed < kLoopTimeNoData) {
                std::this_thread::sleep_for(kLoopTimeNoData - elapsed);
            }
            continue;
        }

        display.clear_panel_led();

        if (has_smoothed_rpm) {
            display.update_rpm_lights(smoothed_rpm);
        }
        if (predicted_gear > 0) {
            display.update_gear_lights(predicted_gear);
        }

        led_strip.show();

        const auto target_loop_time = frame_valid
            ? kLoopTimeWithValidData
            : (opt_rpm.has_value() || opt_speed.has_value() ? kLoopTimePartialData : kLoopTimeNoData);

        const auto elapsed = clock::now() - loop_start;
        if (elapsed < target_loop_time) {
            std::this_thread::sleep_for(target_loop_time - elapsed);
        }
    }

    std::cout << "System off\n";

    return 0;
}