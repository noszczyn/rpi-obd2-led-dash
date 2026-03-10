# OBD2 LED Telemetry: RPM Shift Light & Smart Gear Indicator

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Hardware-C51A4A?logo=Raspberry-Pi)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A high-performance, multi-threaded OBD2 telemetry dashboard for Raspberry Pi and WS2812B LED matrices. Specifically built for the **Suzuki Swift (2008)**, but easily configurable for any OBD2-compatible vehicle.

>  *Photo / GIF of the matrix in action coming soon*

---

## Features

- **Real-time RPM indicator** — progressive LED bar that lights up from both sides
- **Smart gear prediction** — calculates the current gear mathematically from RPM/speed ratios, no gear sensor required
- **Asynchronous OBD2 polling** — event-driven callbacks with RPM prioritized over other metrics
- **Ultra-low latency** — multi-threaded architecture isolates LED rendering from OBD communication; frame render times **< 1ms** at a stable 33 FPS
- **Built-in performance monitor** — dedicated tool to inspect CPU, RAM, temperature, throttling state and OBD callback frequency in real time

---

## Hardware

| Component | Details |
|---|---|
| Raspberry Pi | Model 3, 4 or Zero 2 W |
| LED Matrix | WS2812B 8×8 |
| OBD2 Adapter | ELM327 USB (`/dev/ttyUSB0`) |

---

## Project Structure

```text
rpi-obd2-led-dash/
├── src/
│   ├── config.py           # All configuration — LED, RPM, gear ratios, OBD params
│   ├── display.py          # LED rendering logic (RPM bar, gear digits)
│   ├── gear_predictor.py   # Gear calculation from RPM/speed ratio
│   ├── led_strip.py        # WS2812B hardware interface
│   ├── obd_reader.py       # Async OBD2 connection and callbacks
│   ├── startup_check.py    # Boot animation and error display
│   ├── main.py             # Main application loop
│   └── run.sh              # Production startup script
│   └── requirements.txt    # Necessary libraries
├── tools/
│   ├── main_perf.py        # Performance and hardware monitor
│   └── run_perf.sh         # Startup script for the monitor
├── LICENSE
└── README.md
```

---

## Installation

```bash
git clone https://github.com/noszczyn/Digital-Dashboard
cd Digital-Dashboard
pip install -r src/requirements.txt
```

> **Note:** `rpi_ws281x` requires running as root. The startup scripts handle this automatically via `sudo`.

---

## Configuration

All parameters are in `src/config.py`. Key settings:

```python
# RPM indicator range
RPM_START = 3000    # RPM at which the bar starts lighting up
RPM_MAX   = 5000    # RPM at which the bar is fully lit

# Gear ratios — adjust for your vehicle
GEARS_RATIOS = {1: 133, 2: 73, 3: 49, 4: 37, 5: 29}

# OBD protocol — run tools/main_perf.py once to detect yours
OBD_PROTOCOL = "5"  # ISO 14230-4 KWP FAST
```

---

## Usage

**Production:**
```bash
bash src/run.sh
```

**Performance monitor (debug):**
```bash
bash tools/run_perf.sh
```

The monitor displays live OBD data, gear prediction history, LED frame rate and full Raspberry Pi system health including throttling state.

---

## How Gear Prediction Works

The algorithm divides **RPM by speed (km/h)** to get a ratio, then compares it against known gear ratios for the vehicle with a configurable tolerance (default ±20%). The result is stabilized using a majority vote over the last 5 readings to eliminate outliers.

```
current_ratio = RPM / speed
→ compare against GEARS_RATIOS
→ majority vote over last 5 predictions
→ display on LED matrix
```

---

## Requirements

```
obd
rpi-ws281x
psutil
```

Install via:
```bash
pip install -r src/requirements.txt
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
