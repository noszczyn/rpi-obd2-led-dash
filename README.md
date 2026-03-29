# OBD2 LED Dashboard (Raspberry Pi)

![C++](https://img.shields.io/badge/C%2B%2B-17-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Hardware-C51A4A?logo=Raspberry-Pi)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Real-time OBD2 dashboard for Raspberry Pi and an 8x8 WS2812B LED matrix.

Primary runtime mode is **automatic startup on boot** (car ignition -> Raspberry Pi power -> dashboard starts automatically).

## What It Does

- Displays RPM on the top LED row (symmetric bar).
- Predicts current gear from RPM/speed ratio.
- Shows an over-rev alert: top row blinks red above threshold.
- Includes an optional debug binary for SSH-based diagnostics.

## Hardware Requirements

- Raspberry Pi (3/4/Zero 2 W recommended)
- WS2812B 8x8 LED matrix
- ELM327 USB OBD2 adapter (typically `/dev/ttyUSB0`)
- Stable 5V power supply for automotive use

## Fresh Raspberry Pi Setup (Step by Step)

This section is intended for a clean Raspberry Pi OS installation.

### 1) Prepare Raspberry Pi OS

- Flash Raspberry Pi OS Lite (recommended).
- Boot the Pi and connect it to network.
- Enable SSH:

```bash
sudo raspi-config
```

Then go to `Interface Options` -> `SSH` -> `Enable`.

### 2) Install build dependencies

```bash
sudo apt update
sudo apt install -y git make g++ pkg-config cmake
```

### 3) Clone this repository

```bash
cd /home/pi
git clone https://github.com/noszczyn/Digital-Dashboard.git dash
cd /home/pi/dash
```

### 4) Install `libws2811`

The dashboard requires `libws2811` and `ws2811.h`.

Use the bundled source:

```bash
cd /home/pi/dash/core/rpi_ws281x
mkdir -p build
cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

Quick check:

```bash
pkg-config --cflags --libs libws2811
```

### 5) Install dashboard autostart service (recommended/default)

From repository root:

```bash
cd /home/pi/dash
sudo bash scripts/install_autostart.sh /dev/ttyUSB0
```

This script:
- builds the project,
- creates `dash-dashboard.service`,
- enables and starts it automatically on boot.

### 6) Verify service state

```bash
systemctl status dash-dashboard.service --no-pager
journalctl -u dash-dashboard.service -f
```

### 7) Validate boot behavior

```bash
sudo reboot
```

After reboot, dashboard should start without manual commands.

## Daily Usage (Production)

No manual start required after setup.  
The service starts on boot automatically.

Useful commands:

```bash
# Service status
systemctl status dash-dashboard.service --no-pager

# Live logs
journalctl -u dash-dashboard.service -f

# Restart service
sudo systemctl restart dash-dashboard.service

# Disable autostart
sudo systemctl disable --now dash-dashboard.service
```

## Debug Workflow (Optional, via SSH)

Debug mode is secondary and intended for remote troubleshooting.

1) SSH into Raspberry Pi from your laptop:

```bash
ssh pi@<raspberry_pi_ip>
```

2) Build debug binary:

```bash
cd /home/pi/dash
make debug
```

3) Run debug monitor:

```bash
cd /home/pi/dash/core
sudo ./dashboard_debug --device /dev/ttyUSB0
```

## Configuration

Main tuning values are in:

- `core/include/Config.hpp`

Key parameters include:
- `MAX_RPM`
- `START_RPM`
- `OVER_REV_ALERT_MARGIN_RPM`
- LED timing and loop timing constants

## Read-Only SD Card (Recommended for Car Use)

To reduce corruption risk on sudden power loss, follow:

- `docs/raspberry-readonly-guide.md`

## Project Structure

```text
Digital-Dashboard/
├── core/
│   ├── include/
│   ├── src/
│   ├── tools/
│   ├── rpi_ws281x/
│   └── Makefile
├── scripts/
├── docs/
├── Makefile
└── README.md
```

## License

MIT - see `LICENSE` for details.
