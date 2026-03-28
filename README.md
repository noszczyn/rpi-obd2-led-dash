# OBD2 LED Telemetry: RPM Shift Light & Smart Gear Indicator

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
=======
![C++](https://img.shields.io/badge/C%2B%2B-17-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Hardware-C51A4A?logo=Raspberry-Pi)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A high-performance, multi-threaded OBD2 telemetry dashboard for Raspberry Pi and WS2812B LED matrices. The main implementation is in **C++** (folder `core/`), with an additional Python prototype kept for experiments and profiling.

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
<<<<<<< HEAD
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
=======
Digital-Dashboard/
├── core/                       # Main C++ application
│   ├── include/                # Headers
│   ├── src/                    # Core implementation
│   ├── tools/                  # Debug binary entrypoint
│   ├── rpi_ws281x/             # External ws281x library source
│   └── Makefile                # Native build
├── python_prototype/           # Optional add-on (prototype/monitoring)
│   ├── src/
│   └── tools/
├── Makefile                    # Root wrapper for core/Makefile
>>>>>>> 6ee0430 (swap program from python to c++)
├── LICENSE
└── README.md
```

---

## Installation

```bash
git clone https://github.com/noszczyn/Digital-Dashboard
cd Digital-Dashboard
<<<<<<< HEAD
pip install -r src/requirements.txt
=======
make
>>>>>>> 6ee0430 (swap program from python to c++)
```

> **Note:** `rpi_ws281x` requires running as root on Raspberry Pi runtime. Build commands themselves do not use `sudo`.

---

<<<<<<< HEAD
## Configuration
=======
## ⚙️ Build & Run (C++)
>>>>>>> 6ee0430 (swap program from python to c++)

Build main binary:

<<<<<<< HEAD
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
=======
>>>>>>> 6ee0430 (swap program from python to c++)
```bash
make
```

Build debug binary:
```bash
make debug
```

<<<<<<< HEAD
The monitor displays live OBD data, gear prediction history, LED frame rate and full Raspberry Pi system health including throttling state.

---

## How Gear Prediction Works

The algorithm divides **RPM by speed (km/h)** to get a ratio, then compares it against known gear ratios for the vehicle with a configurable tolerance (default ±20%). The result is stabilized using a majority vote over the last 5 readings to eliminate outliers.

=======
Clean binaries:
```bash
make clean
>>>>>>> 6ee0430 (swap program from python to c++)
```

Run from `core/`:
```bash
cd core
./dashboard_app
```

---

<<<<<<< HEAD
## Requirements
=======
## 🧪 Python Prototype (Optional)
>>>>>>> 6ee0430 (swap program from python to c++)

Python code in `python_prototype/` is an optional companion for rapid iteration and performance monitoring.

Install dependencies:
```bash
<<<<<<< HEAD
pip install -r src/requirements.txt
=======
pip install -r python_prototype/src/requirements.txt
```

Run prototype:
```bash
bash python_prototype/src/run.sh
```

Run monitor:
```bash
bash python_prototype/tools/run_perf.sh
>>>>>>> 6ee0430 (swap program from python to c++)
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
