#include <algorithm>
#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdio>
#include <deque>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <numeric>
#include <optional>
#include <sstream>
#include <string>
#include <sys/statvfs.h>
#include <thread>
#include <unordered_map>
#include <vector>

#include "Display.hpp"
#include "GearPredictor.hpp"
#include "LedStrip.hpp"
#include "ObdReader.hpp"

namespace {
using Clock = std::chrono::steady_clock;

struct TelemetryState {
    float rpm = 0.0f;
    int speed = 0;
    bool rpm_valid = false;
    bool speed_valid = false;
};

struct Metrics {
    uint64_t obd_callbacks = 0;
    uint64_t led_frames = 0;
    double led_frame_time_ms = 0.0;
    double led_frame_time_avg = 0.0;
    std::vector<int> gear_history;
    int last_gear_display = -1;
};

std::atomic<bool> g_running{true};
std::atomic<long long> g_last_obd_data_ms{0};
std::atomic<long long> g_last_rpm_data_ms{0};
std::mutex g_state_mutex;
std::mutex g_metrics_mutex;
TelemetryState g_state;
Metrics g_metrics;
std::string g_mode_label = "obd-pid";

void handle_sigint(int sig) {
    (void)sig;
    g_running.store(false);
}

long long monotonic_ms_now() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        Clock::now().time_since_epoch()
    ).count();
}

std::optional<double> read_double_file(const std::string& path, double scale = 1.0) {
    std::ifstream file(path);
    if (!file.is_open()) {
        return std::nullopt;
    }

    double value = 0.0;
    file >> value;
    if (file.fail()) {
        return std::nullopt;
    }
    return value * scale;
}

std::optional<double> get_cpu_temp_c() {
    return read_double_file("/sys/class/thermal/thermal_zone0/temp", 0.001);
}

std::optional<double> get_cpu_freq_mhz() {
    auto khz = read_double_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq");
    if (!khz.has_value()) {
        return std::nullopt;
    }
    return *khz / 1000.0;
}

struct MemoryInfo {
    double used_percent = 0.0;
    double used_mb = 0.0;
    double total_mb = 0.0;
};

std::optional<MemoryInfo> get_memory_info() {
    std::ifstream meminfo("/proc/meminfo");
    if (!meminfo.is_open()) {
        return std::nullopt;
    }

    long total_kb = 0;
    long avail_kb = 0;
    std::string key;
    long value = 0;
    std::string unit;
    while (meminfo >> key >> value >> unit) {
        if (key == "MemTotal:") {
            total_kb = value;
        } else if (key == "MemAvailable:") {
            avail_kb = value;
        }
        if (total_kb > 0 && avail_kb > 0) {
            break;
        }
    }
    if (total_kb <= 0 || avail_kb <= 0) {
        return std::nullopt;
    }

    const double used_kb = static_cast<double>(total_kb - avail_kb);
    MemoryInfo info;
    info.used_percent = (used_kb * 100.0) / static_cast<double>(total_kb);
    info.used_mb = used_kb / 1024.0;
    info.total_mb = static_cast<double>(total_kb) / 1024.0;
    return info;
}

struct DiskInfo {
    double used_percent = 0.0;
    double used_gb = 0.0;
    double total_gb = 0.0;
};

std::optional<DiskInfo> get_disk_info() {
    struct statvfs fs {};
    if (statvfs("/", &fs) != 0) {
        return std::nullopt;
    }

    const double total = static_cast<double>(fs.f_blocks) * static_cast<double>(fs.f_frsize);
    const double available = static_cast<double>(fs.f_bavail) * static_cast<double>(fs.f_frsize);
    if (total <= 0.0) {
        return std::nullopt;
    }

    DiskInfo info;
    const double used = std::max(0.0, total - available);
    info.used_percent = (used * 100.0) / total;
    info.used_gb = used / (1024.0 * 1024.0 * 1024.0);
    info.total_gb = total / (1024.0 * 1024.0 * 1024.0);
    return info;
}

class CpuUsageSampler {
public:
    std::optional<double> sample() {
        std::ifstream stat("/proc/stat");
        if (!stat.is_open()) {
            return std::nullopt;
        }

        std::string label;
        unsigned long long user = 0, nice = 0, system = 0, idle = 0;
        unsigned long long iowait = 0, irq = 0, softirq = 0, steal = 0;
        stat >> label >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;
        if (label != "cpu") {
            return std::nullopt;
        }

        const unsigned long long idle_all = idle + iowait;
        const unsigned long long non_idle = user + nice + system + irq + softirq + steal;
        const unsigned long long total = idle_all + non_idle;

        if (!has_prev_) {
            has_prev_ = true;
            prev_total_ = total;
            prev_idle_ = idle_all;
            return std::nullopt;
        }

        const auto total_delta = total - prev_total_;
        const auto idle_delta = idle_all - prev_idle_;
        prev_total_ = total;
        prev_idle_ = idle_all;

        if (total_delta == 0) {
            return std::nullopt;
        }
        return std::clamp((1.0 - (static_cast<double>(idle_delta) / static_cast<double>(total_delta))) * 100.0, 0.0, 100.0);
    }

private:
    bool has_prev_ = false;
    unsigned long long prev_total_ = 0;
    unsigned long long prev_idle_ = 0;
};

std::string to_fixed(double value, int precision) {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(precision) << value;
    return oss.str();
}

std::string progress_bar(double percent, int width = 20) {
    const int filled = std::clamp(static_cast<int>(width * percent / 100.0), 0, width);
    return "[" + std::string(static_cast<size_t>(filled), '#') +
           std::string(static_cast<size_t>(width - filled), '-') +
           "] " + to_fixed(percent, 1) + "%";
}

int most_common_gear(const std::deque<int>& history) {
    std::unordered_map<int, int> counts;
    for (int gear : history) {
        counts[gear]++;
    }

    int best_gear = history.front();
    int best_count = 0;
    for (const auto& [gear, count] : counts) {
        if (count > best_count || (count == best_count && gear > best_gear)) {
            best_count = count;
            best_gear = gear;
        }
    }
    return best_gear;
}
} // namespace

int main(int argc, char** argv) {
    std::signal(SIGINT, handle_sigint);
    g_last_obd_data_ms.store(monotonic_ms_now(), std::memory_order_relaxed);
    g_last_rpm_data_ms.store(monotonic_ms_now(), std::memory_order_relaxed);

    std::string device_path = "/dev/ttyUSB0";
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--device" && i + 1 < argc) {
            device_path = argv[++i];
        } else if (arg == "--help") {
            std::cout
                << "Usage:\n"
                << "  ./dashboard_debug [--device /dev/ttyUSB0]\n";
            return 0;
        }
    }

    g_mode_label = "obd-pid";
    std::cout << "--- SUZUKI SWIFT DEBUG MONITOR START ---\n";
    std::cout << "Mode: " << g_mode_label << ", device: " << device_path << "\n";

    LedStrip led_strip;
    if (!led_strip.begin()) {
        std::cerr << "CRITICAL ERROR: failed to initialize LED matrix.\n";
        std::cerr << "Make sure you run this program with 'sudo'.\n";
        return 1;
    }

    Display display(led_strip);
    GearPredictor predictor;

    ObdReader obd(device_path);
    if (!obd.connect() || !obd.initialize()) {
        std::cerr << "Telemetry adapter is not available.\n";
        return 1;
    }

    std::thread obd_thread([&obd]() {
        while (g_running.load()) {
            const auto loop_start = Clock::now();
            const auto rpm = obd.get_rpm();
            const auto speed = obd.get_speed();
            bool got_any_valid_frame = false;

            {
                std::scoped_lock lock(g_state_mutex);
                if (rpm.has_value()) {
                    g_state.rpm = *rpm;
                    g_state.rpm_valid = true;
                    got_any_valid_frame = true;
                    g_last_rpm_data_ms.store(monotonic_ms_now(), std::memory_order_relaxed);
                }
                if (speed.has_value()) {
                    g_state.speed = *speed;
                    g_state.speed_valid = true;
                    got_any_valid_frame = true;
                }
            }

            if (got_any_valid_frame) {
                g_last_obd_data_ms.store(monotonic_ms_now(), std::memory_order_relaxed);
            }

            {
                std::scoped_lock lock(g_metrics_mutex);
                if (rpm.has_value()) {
                    g_metrics.obd_callbacks++;
                }
                if (speed.has_value()) {
                    g_metrics.obd_callbacks++;
                }
            }

            const auto elapsed = Clock::now() - loop_start;
            if (elapsed < Config::OBD_TICK) {
                std::this_thread::sleep_for(Config::OBD_TICK - elapsed);
            }
        }
    });

    std::thread led_thread([&display, &led_strip, &predictor]() {
        std::deque<int> gear_history;
        std::deque<double> frame_times_ms;
        float smoothed_rpm = 0.0f;
        bool has_smoothed_rpm = false;
        bool has_last_raw_rpm = false;
        float last_raw_rpm = 0.0f;
        int gear_display = -1;

        while (g_running.load()) {
            const auto frame_start = Clock::now();

            TelemetryState snapshot;
            {
                std::scoped_lock lock(g_state_mutex);
                snapshot = g_state;
            }

            if (snapshot.rpm_valid) {
                if (!has_smoothed_rpm) {
                    smoothed_rpm = snapshot.rpm;
                    has_smoothed_rpm = true;
                } else {
                    smoothed_rpm = (Config::RPM_EMA_ALPHA * snapshot.rpm) + ((1.0f - Config::RPM_EMA_ALPHA) * smoothed_rpm);
                }
            }

            int predicted_gear = -1;
            if (snapshot.rpm_valid && snapshot.speed_valid) {
                // Use raw RPM for gear prediction to avoid EMA lag during quick shifts.
                predicted_gear = predictor.gear_predict(snapshot.rpm, snapshot.speed);

                if (gear_display > 0 &&
                    predicted_gear > gear_display &&
                    has_last_raw_rpm &&
                    ((snapshot.rpm - last_raw_rpm) > Config::RPM_RISE_DOWNSHIFT_GUARD)) {
                    predicted_gear = gear_display;
                }

                gear_history.push_back(predicted_gear);
                if (gear_history.size() > 5) {
                    gear_history.pop_front();
                }
                if (gear_history.size() == 5) {
                    gear_display = most_common_gear(gear_history);
                }
            }
            if (snapshot.rpm_valid) {
                last_raw_rpm = snapshot.rpm;
                has_last_raw_rpm = true;
            }

            display.clear_panel_led();
            const long long now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(frame_start.time_since_epoch()).count();
            const long long last_rpm_ms = g_last_rpm_data_ms.load(std::memory_order_relaxed);
            const bool rpm_fresh = (now_ms - last_rpm_ms) <= Config::RPM_FRESH_TIMEOUT.count();
            const bool over_rev_alert = snapshot.rpm_valid &&
                                        rpm_fresh &&
                                        (snapshot.rpm > (Config::MAX_RPM + Config::OVER_REV_ALERT_MARGIN_RPM));
            const bool over_rev_blink_on = ((now_ms / Config::OVER_REV_BLINK_PERIOD.count()) % 2) == 0;
            if (has_smoothed_rpm) {
                display.update_rpm_lights(smoothed_rpm);
            }
            if (gear_display >= 0) {
                display.update_gear_lights(gear_display);
            }
            if (over_rev_alert) {
                display.set_top_row_alert(over_rev_blink_on);
            }
            led_strip.show();

            const auto elapsed = Clock::now() - frame_start;
            const double frame_ms = std::chrono::duration<double, std::milli>(elapsed).count();
            frame_times_ms.push_back(frame_ms);
            if (frame_times_ms.size() > 60) {
                frame_times_ms.pop_front();
            }

            const double avg = std::accumulate(frame_times_ms.begin(), frame_times_ms.end(), 0.0) /
                               static_cast<double>(frame_times_ms.size());

            {
                std::scoped_lock lock(g_metrics_mutex);
                g_metrics.led_frames++;
                g_metrics.led_frame_time_ms = frame_ms;
                g_metrics.led_frame_time_avg = avg;
                g_metrics.last_gear_display = gear_display;
                g_metrics.gear_history.assign(gear_history.begin(), gear_history.end());
            }

            if (elapsed < Config::LED_TARGET_FRAME) {
                std::this_thread::sleep_for(Config::LED_TARGET_FRAME - elapsed);
            }
        }
    });

    std::thread monitor_thread([]() {
        CpuUsageSampler cpu_sampler;
        const auto monitor_start = Clock::now();
        auto prev_time = Clock::now();
        uint64_t prev_callbacks = 0;
        uint64_t prev_frames = 0;

        while (g_running.load()) {
            std::this_thread::sleep_for(std::chrono::seconds(1));

            const auto now = Clock::now();
            const double elapsed = std::chrono::duration<double>(now - prev_time).count();
            const int uptime = static_cast<int>(std::chrono::duration_cast<std::chrono::seconds>(now - monitor_start).count());

            Metrics metrics_snapshot;
            TelemetryState state_snapshot;
            {
                std::scoped_lock lock(g_metrics_mutex);
                metrics_snapshot = g_metrics;
            }
            {
                std::scoped_lock lock(g_state_mutex);
                state_snapshot = g_state;
            }

            const double callbacks_per_sec = elapsed > 0.0
                ? static_cast<double>(metrics_snapshot.obd_callbacks - prev_callbacks) / elapsed
                : 0.0;
            const double frames_per_sec = elapsed > 0.0
                ? static_cast<double>(metrics_snapshot.led_frames - prev_frames) / elapsed
                : 0.0;

            prev_callbacks = metrics_snapshot.obd_callbacks;
            prev_frames = metrics_snapshot.led_frames;
            prev_time = now;

            const auto cpu_temp = get_cpu_temp_c();
            const auto cpu_freq = get_cpu_freq_mhz();
            const auto cpu_percent = cpu_sampler.sample();
            const auto memory = get_memory_info();
            const auto disk = get_disk_info();
            const auto stale_timeout_ms = std::chrono::duration_cast<std::chrono::milliseconds>(Config::OBD_STALE_TIMEOUT).count();
            const long long now_ms = monotonic_ms_now();
            const long long last_obd_ms = g_last_obd_data_ms.load(std::memory_order_relaxed);
            const long long obd_stale_ms = std::max<long long>(0, now_ms - last_obd_ms);
            const bool obd_stale = obd_stale_ms > stale_timeout_ms;

            std::cout << "\033[2J\033[H";
            std::cout << "================================================\n";
            std::cout << "  DIGITAL DASHBOARD - debug monitor\n";
            std::cout << "  Uptime: " << uptime << "s\n";
            std::cout << "  Mode: " << g_mode_label << "\n";
            std::cout << "================================================\n\n";

            std::cout << "TELEMETRY DATA\n";
            std::cout << "  RPM:   " << std::setw(6) << static_cast<int>(state_snapshot.rpm) << " rpm\n";
            std::cout << "  Speed: " << std::setw(6) << state_snapshot.speed << " km/h\n\n";
            std::cout << "  Stream: " << (obd_stale ? "STALE" : "OK")
                      << " (" << to_fixed(static_cast<double>(obd_stale_ms) / 1000.0, 1)
                      << "s since last valid frame)\n\n";

            std::cout << "GEAR PREDICTION\n";
            std::cout << "  History: [";
            for (size_t i = 0; i < metrics_snapshot.gear_history.size(); ++i) {
                std::cout << metrics_snapshot.gear_history[i]
                          << (i + 1 < metrics_snapshot.gear_history.size() ? ", " : "");
            }
            std::cout << "]\n";
            std::cout << "  Display: " << metrics_snapshot.last_gear_display << "\n\n";

            std::cout << "PERFORMANCE\n";
            std::cout << "  Telemetry callbacks/s: " << to_fixed(callbacks_per_sec, 1) << "\n";
            std::cout << "  LED frames/s:     " << to_fixed(frames_per_sec, 1) << " (target ~33)\n";
            std::cout << "  Frame time:       " << to_fixed(metrics_snapshot.led_frame_time_ms, 2) << " ms\n";
            std::cout << "  Avg frame time:   " << to_fixed(metrics_snapshot.led_frame_time_avg, 2) << " ms\n";
            std::cout << "  Total frames:     " << metrics_snapshot.led_frames << "\n";
            std::cout << "  Total callbacks:  " << metrics_snapshot.obd_callbacks << "\n\n";

            std::cout << "RASPBERRY PI\n";
            std::cout << "  CPU temp: " << (cpu_temp.has_value() ? to_fixed(*cpu_temp, 1) + " C" : "no data") << "\n";
            std::cout << "  CPU freq: " << (cpu_freq.has_value() ? to_fixed(*cpu_freq, 0) + " MHz" : "no data") << "\n";
            std::cout << "  CPU:      " << (cpu_percent.has_value() ? progress_bar(*cpu_percent) : "no data") << "\n";
            if (memory.has_value()) {
                std::cout << "  RAM:      " << progress_bar(memory->used_percent)
                          << "  (" << to_fixed(memory->used_mb, 0) << " / " << to_fixed(memory->total_mb, 0) << " MB)\n";
            } else {
                std::cout << "  RAM:      no data\n";
            }
            if (disk.has_value()) {
                std::cout << "  SD:       " << progress_bar(disk->used_percent)
                          << "  (" << to_fixed(disk->used_gb, 1) << " / " << to_fixed(disk->total_gb, 1) << " GB)\n";
            } else {
                std::cout << "  SD:       no data\n";
            }

            std::cout << "\nPress Ctrl+C to stop\n";
            if (obd_stale) {
                std::cout << "\nWARNING: telemetry stream is stale (>2s without valid frame)\n";
            }
        }
    });

    while (g_running.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    if (obd_thread.joinable()) {
        obd_thread.join();
    }
    if (led_thread.joinable()) {
        led_thread.join();
    }
    if (monitor_thread.joinable()) {
        monitor_thread.join();
    }

    display.clear_panel_led();
    led_strip.show();
    std::cout << "\nStopped.\n";
    return 0;
}