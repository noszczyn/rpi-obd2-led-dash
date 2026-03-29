#include <csignal>
#include <chrono>
#include <iostream>
#include <string>
#include <thread>

#include "Config.hpp"
#include "LedStrip.hpp"
#include "Display.hpp"
#include "GearPredictor.hpp"
#include "ObdReader.hpp"

volatile std::sig_atomic_t g_running = 1;

void handle_sigint(int sig) {
    (void)sig;
    std::cout << "\n[SIGNAL] Interrupt received. Shutting down safely...\n";
    g_running = 0;
}

int main(int argc, char** argv) {
    using clock = std::chrono::steady_clock;

    std::signal(SIGINT, handle_sigint);

    std::string device_path = "/dev/ttyUSB0";
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--device" && i + 1 < argc) {
            device_path = argv[++i];
        } else if (arg == "--help") {
            std::cout
                << "Usage:\n"
                << "  ./dashboard_app [--device /dev/ttyUSB0]\n";
            return 0;
        }
    }

    std::cout << "--- SUZUKI SWIFT TELEMETRY START ---\n";
    std::cout << "Mode: obd-pid, device: " << device_path << "\n";

    LedStrip led_strip;
    if (!led_strip.begin()) {
        std::cerr << "CRITICAL ERROR: failed to initialize LED matrix.\n";
        std::cerr << "Make sure you run this program with 'sudo'.\n";
        return 1;
    }

    Display display(led_strip);
    GearPredictor predictor;

    ObdReader obd(device_path);
    if (!obd.connect()) {
        std::cerr << "Cannot connect to telemetry adapter. Exiting.\n";
        return 1; // LedStrip destructor turns LEDs off on exit.
    }

    if (!obd.initialize()) {
        std::cerr << "Telemetry source initialization failed. Exiting.\n";
        return 1;
    }

    std::cout << "Connection established. Starting real-time loop...\n";

    int consecutive_frame_misses = 0;
    bool failsafe_active = false;
    bool has_smoothed_rpm = false;
    float smoothed_rpm = 0.0f;
    bool has_last_raw_rpm = false;
    float last_raw_rpm = 0.0f;
    int last_displayed_gear = -1;

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
                smoothed_rpm = (Config::RPM_EMA_ALPHA * (*opt_rpm)) + ((1.0f - Config::RPM_EMA_ALPHA) * smoothed_rpm);
            }
        }

        const bool frame_valid = opt_rpm.has_value() && opt_speed.has_value();

        if (frame_valid) {
            consecutive_frame_misses = 0;
            if (failsafe_active) {
                std::cout << "OBD data stream recovered.\n";
            }
            failsafe_active = false;

            // Use raw RPM for gear prediction to avoid EMA lag during quick shifts.
            const float rpm_for_gear = *opt_rpm;
            predicted_gear = predictor.gear_predict(rpm_for_gear, *opt_speed);

            // Anti-glitch guard:
            // when RPM rises quickly (typical downshift behavior), suppress one-frame
            // upshift spikes such as 4 -> 5 -> 3 caused by transient OBD timing skew.
            if (last_displayed_gear > 0 &&
                predicted_gear > last_displayed_gear &&
                has_last_raw_rpm &&
                ((*opt_rpm - last_raw_rpm) > Config::RPM_RISE_DOWNSHIFT_GUARD)) {
                predicted_gear = last_displayed_gear;
            }
        } else {
            consecutive_frame_misses++;
        }

        if (opt_rpm.has_value()) {
            last_raw_rpm = *opt_rpm;
            has_last_raw_rpm = true;
        }

        if (consecutive_frame_misses >= Config::MAX_CONSECUTIVE_FRAME_MISSES) {
            if (!failsafe_active) {
                std::cerr << "Failsafe: no valid telemetry frames, turning LEDs off.\n";
                failsafe_active = true;
            }

            display.clear_panel_led();
            led_strip.show();

            const auto elapsed = clock::now() - loop_start;
            if (elapsed < Config::LOOP_TIME_NO_DATA) {
                std::this_thread::sleep_for(Config::LOOP_TIME_NO_DATA - elapsed);
            }
            continue;
        }

        display.clear_panel_led();

        const bool over_rev_alert = opt_rpm.has_value() && (*opt_rpm > (Config::MAX_RPM + Config::OVER_REV_ALERT_MARGIN_RPM));
        const long long now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(loop_start.time_since_epoch()).count();
        const bool over_rev_blink_on = ((now_ms / Config::OVER_REV_BLINK_PERIOD.count()) % 2) == 0;

        if (has_smoothed_rpm) {
            display.update_rpm_lights(smoothed_rpm);
        }
        if (predicted_gear >= 0) {
            display.update_gear_lights(predicted_gear);
            last_displayed_gear = predicted_gear;
        }
        if (over_rev_alert) {
            display.set_top_row_alert(over_rev_blink_on);
        }

        led_strip.show();

        const auto target_loop_time = frame_valid
            ? Config::LOOP_TIME_WITH_VALID_DATA
            : (opt_rpm.has_value() || opt_speed.has_value() ? Config::LOOP_TIME_PARTIAL_DATA : Config::LOOP_TIME_NO_DATA);

        const auto elapsed = clock::now() - loop_start;
        if (elapsed < target_loop_time) {
            std::this_thread::sleep_for(target_loop_time - elapsed);
        }
    }

    std::cout << "System off\n";

    return 0;
}