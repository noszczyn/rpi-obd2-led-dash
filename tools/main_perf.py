import os
import time
import threading
import psutil
from collections import deque, Counter

import config
import led_strip
import obd_reader
from display import clear_panel_led, update_rpm_lights, update_gear_lights
from gear_predictor import predict_gear
from startup_check import run_startup_animation, show_error_lights
from obd_reader import state, state_lock

# ------------------------------------------------------------------
# PERFORMANCE METRICS
# ------------------------------------------------------------------
metrics = {
    "obd_callbacks":    0,
    "led_frames":       0,
    "led_frame_time_ms":  0.0,
    "led_frame_time_avg": 0.0,
    "gear_history":     [],
    "last_gear_display": 0,
}
metrics_lock = threading.Lock()

# ------------------------------------------------------------------
# LED THREAD
# ------------------------------------------------------------------
gear_history = deque(maxlen=5)
gear_display = 0
running      = True
frame_times  = deque(maxlen=60)  # rolling average over last 60 frames (~2 seconds)

def led_loop() -> None:
    global gear_display

    while running:
        frame_start = time.perf_counter()

        with state_lock:
            rpm   = state["rpm"]
            speed = state["speed"]

        gear = predict_gear(rpm, speed)
        gear_history.append(gear)

        if len(gear_history) == gear_history.maxlen:
            gear_display = Counter(gear_history).most_common(1)[0][0]

        clear_panel_led()
        update_rpm_lights(rpm, config.RPM_START, config.RPM_MAX)

        if gear_display >= 0:
            update_gear_lights(gear_display)

        led_strip.show()

        frame_ms = (time.perf_counter() - frame_start) * 1000
        frame_times.append(frame_ms)

        with metrics_lock:
            metrics["led_frames"]          += 1
            metrics["led_frame_time_ms"]    = frame_ms
            metrics["led_frame_time_avg"]   = sum(frame_times) / len(frame_times)
            metrics["gear_history"]         = list(gear_history)
            metrics["last_gear_display"]    = gear_display

        time.sleep(0.03)

# ------------------------------------------------------------------
# OBD CALLBACKS WITH METRICS
# ------------------------------------------------------------------
_original_on_rpm   = obd_reader.on_rpm
_original_on_speed = obd_reader.on_speed

def on_rpm_tracked(response):
    _original_on_rpm(response)
    if not response.is_null():
        with metrics_lock:
            metrics["obd_callbacks"] += 1

def on_speed_tracked(response):
    _original_on_speed(response)
    if not response.is_null():
        with metrics_lock:
            metrics["obd_callbacks"] += 1

# Re-register watches with tracking callbacks
obd_reader.connection.unwatch_all()
obd_reader.connection.watch(obd_reader.obd.commands.RPM,   callback=on_rpm_tracked)
obd_reader.connection.watch(obd_reader.obd.commands.RPM,   callback=on_rpm_tracked)
obd_reader.connection.watch(obd_reader.obd.commands.SPEED, callback=on_speed_tracked)

# ------------------------------------------------------------------
# RASPBERRY PI SYSTEM INFO
# ------------------------------------------------------------------
def _get_cpu_temp() -> float | None:
    """Read CPU temperature from RPi system file."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read()) / 1000.0
    except FileNotFoundError:
        return None

def _get_cpu_freq() -> float | None:
    """Read current CPU frequency in MHz."""
    try:
        freq = psutil.cpu_freq()
        return freq.current if freq else None
    except Exception:
        return None

def _get_throttle_state() -> dict | None:
    """
    Check RPi throttling state via vcgencmd.
    Each bit flag indicates a different issue:
      bit 0  — now:  under-voltage
      bit 1  — now:  frequency capped
      bit 2  — now:  throttling active
      bit 16 — ever: under-voltage occurred
      bit 17 — ever: frequency was capped
      bit 18 — ever: throttling occurred
    """
    try:
        result  = os.popen("vcgencmd get_throttled").read().strip()
        hex_val = int(result.split("=")[1], 16)
        return {
            "under_voltage":      bool(hex_val & (1 << 0)),
            "freq_capped":        bool(hex_val & (1 << 1)),
            "throttled_now":      bool(hex_val & (1 << 2)),
            "under_voltage_ever": bool(hex_val & (1 << 16)),
            "freq_capped_ever":   bool(hex_val & (1 << 17)),
            "throttled_ever":     bool(hex_val & (1 << 18)),
            "raw": hex(hex_val),
        }
    except Exception:
        return None

def _format_throttle_state(ts: dict | None) -> str:
    if ts is None:
        return "  No data (vcgencmd unavailable)"

    lines = []
    if ts["under_voltage"]:      lines.append("  ⚠️  NOW: Under-voltage!")
    if ts["freq_capped"]:        lines.append("  ⚠️  NOW: Frequency capped!")
    if ts["throttled_now"]:      lines.append("  ⚠️  NOW: Throttling active!")
    if ts["under_voltage_ever"]: lines.append("  📌 PAST: Under-voltage occurred")
    if ts["freq_capped_ever"]:   lines.append("  📌 PAST: Frequency was capped")
    if ts["throttled_ever"]:     lines.append("  📌 PAST: Throttling occurred")
    if not lines:                lines.append("  ✅ No throttling")

    lines.append(f"  Raw: {ts['raw']}")
    return "\n".join(lines)

def _get_disk_usage() -> dict | None:
    try:
        usage = psutil.disk_usage("/")
        return {
            "total_gb": usage.total / (1024 ** 3),
            "used_gb":  usage.used  / (1024 ** 3),
            "percent":  usage.percent,
        }
    except Exception:
        return None

def _progress_bar(percent: float, width: int = 20) -> str:
    filled = int(width * percent / 100)
    return f"[{'█' * filled}{'░' * (width - filled)}] {percent:.1f}%"

# ------------------------------------------------------------------
# MONITOR THREAD
# ------------------------------------------------------------------
monitor_start = time.time()

def monitor_loop() -> None:
    last_callbacks = 0
    last_frames    = 0
    last_time      = time.time()

    while running:
        time.sleep(1.0)

        now     = time.time()
        elapsed = now - last_time
        uptime  = int(now - monitor_start)

        with metrics_lock:
            callbacks = metrics["obd_callbacks"]
            frames    = metrics["led_frames"]
            frame_ms  = metrics["led_frame_time_ms"]
            frame_avg = metrics["led_frame_time_avg"]
            g_history = metrics["gear_history"]
            g_display = metrics["last_gear_display"]

        with state_lock:
            rpm   = state["rpm"]
            speed = state["speed"]

        callbacks_per_sec = (callbacks - last_callbacks) / elapsed
        frames_per_sec    = (frames    - last_frames)    / elapsed

        last_callbacks = callbacks
        last_frames    = frames
        last_time      = now

        cpu_temp    = _get_cpu_temp()
        cpu_freq    = _get_cpu_freq()
        cpu_percent = psutil.cpu_percent(interval=None)
        ram         = psutil.virtual_memory()
        disk        = _get_disk_usage()
        throttle_st = _get_throttle_state()

        if cpu_temp is None:
            temp_str = "no data"
        elif cpu_temp >= 80:
            temp_str = f"{cpu_temp:.1f}°C  ⚠️  CRITICAL!"
        elif cpu_temp >= 70:
            temp_str = f"{cpu_temp:.1f}°C  ⚠️  High"
        else:
            temp_str = f"{cpu_temp:.1f}°C"

        print("\033[2J\033[H", end="")
        print("=" * 48)
        print(f"  DIGITAL DASHBOARD — performance monitor")
        print(f"  Uptime: {uptime}s")
        print("=" * 48)

        print("\n📡 OBD DATA")
        print(f"  RPM:    {rpm:>6.0f} rpm")
        print(f"  Speed:  {speed:>6.1f} km/h")

        print("\n⚙️  GEAR PREDICTION")
        print(f"  History:  {list(g_history)}")
        print(f"  Display:  {g_display}")

        print("\n⚡ DASHBOARD PERFORMANCE")
        print(f"  OBD callbacks/s:  {callbacks_per_sec:>5.1f}  (RPM x2 + SPEED)")
        print(f"  LED frames/s:     {frames_per_sec:>5.1f}  (target: 33)")
        print(f"  Frame time:       {frame_ms:>5.2f} ms")
        print(f"  Avg frame time:   {frame_avg:>5.2f} ms  (target: <30)")
        print(f"  Total frames:     {frames}")
        print(f"  Total callbacks:  {callbacks}")

        print("\n🔧 OBD OPTIMIZATIONS")
        print(f"  fast:          True   (return after 1 response)")
        print(f"  timeout:       0.05s  (serial port timeout)")
        print(f"  check_voltage: False  (skip voltage detection)")
        print(f"  delay_cmds:    0.05s  (async cycle delay)")
        print(f"  RPM watch:     x2     (double priority)")

        print("\n🍓 RASPBERRY PI")
        print(f"  CPU temp:   {temp_str}")
        print(f"  CPU freq:   {f'{cpu_freq:.0f} MHz' if cpu_freq else 'no data'}")
        print(f"  CPU:  {_progress_bar(cpu_percent)}")
        print(f"  RAM:  {_progress_bar(ram.percent)}  ({ram.used/1024**2:.0f} / {ram.total/1024**2:.0f} MB)")
        if disk:
            print(f"  SD:   {_progress_bar(disk['percent'])}  ({disk['used_gb']:.1f} / {disk['total_gb']:.1f} GB)")

        print("\n🔋 THROTTLING")
        print(_format_throttle_state(throttle_st))

        warnings = []
        if frame_avg > 30:
            warnings.append("Avg frame time exceeds 30ms")
        if callbacks_per_sec < 1 and uptime > 3:
            warnings.append("No OBD data — check connection")
        if frames_per_sec < 25:
            warnings.append("Low LED frame rate")
        if cpu_temp and cpu_temp >= 70:
            warnings.append("High CPU temperature")
        if ram.percent > 85:
            warnings.append(f"High RAM usage ({ram.percent:.0f}%)")
        if throttle_st and throttle_st["throttled_now"]:
            warnings.append("RPi is actively throttling!")
        if throttle_st and throttle_st["under_voltage"]:
            warnings.append("RPi detected under-voltage!")

        if warnings:
            print("\n⚠️  WARNINGS")
            for w in warnings:
                print(f"  • {w}")

        print("\n  Press Ctrl+C to stop")

# ------------------------------------------------------------------
# START
# ------------------------------------------------------------------
led_thread = None

try:
    obd_reader.connection.start()

    if obd_reader.connection.is_connected():
        print(f"Protocol: {obd_reader.connection.protocol_id()} — {obd_reader.connection.protocol_name()}")
        time.sleep(1)

        run_startup_animation()
        clear_panel_led()
        led_strip.show()

        led_thread     = threading.Thread(target=led_loop,    daemon=True)
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)

        led_thread.start()
        monitor_thread.start()

        while led_thread.is_alive():
            time.sleep(0.1)

    else:
        show_error_lights()

except KeyboardInterrupt:
    running = False
    if led_thread is not None:
        led_thread.join()
    obd_reader.connection.stop()
    clear_panel_led()
    led_strip.show()
    print("\nStopped.")