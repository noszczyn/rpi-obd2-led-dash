# OBD2 LED Dashboard (Raspberry Pi, Python)

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Hardware-C51A4A?logo=Raspberry-Pi)
![License](https://img.shields.io/badge/license-MIT-green.svg)

WS2812B 8×8 LED matrix dashboard: RPM bar, gear prediction, over-rev blink. Uses **python-OBD** (ELM327) and **rpi_ws281x**.

---

## Full setup: autostart from scratch

Use this if you have a **fresh Raspberry Pi** and want the dashboard to start **automatically on every boot** (e.g. power from the car).  
Below, the project lives under **`/home/pi/rpi-obd2-led-dash`** — adjust the username if yours is not `pi`.

### 1) Raspberry Pi OS

- Install **Raspberry Pi OS Lite** (or Desktop) and boot the Pi.
- Connect network (Ethernet or Wi‑Fi).
- **Enable SSH** (optional but recommended for headless setup):

```bash
sudo raspi-config
```

→ `Interface Options` → `SSH` → `Enable`.

Update the system:

```bash
sudo apt update && sudo apt full-upgrade -y
```

### 2) Install system packages

```bash
sudo apt install -y git python3 python3-pip python3-venv
```

### 3) Clone the repository

```bash
cd /home/pi
git clone https://github.com/noszczyn/Digital-Dashboard.git rpi-obd2-led-dash
cd /home/pi/rpi-obd2-led-dash
```

(If you already copied the folder by other means, just ensure the path is `/home/pi/rpi-obd2-led-dash` and contains `src/main.py`.)

### 4) Install Python dependencies

Either **system-wide** (simplest for the provided systemd unit):

```bash
cd /home/pi/rpi-obd2-led-dash
python3 -m pip install --break-system-packages -r src/requirements.txt
```

On older images without `--break-system-packages`, use a venv and point the systemd unit to that Python (see notes at the end), or:

```bash
python3 -m pip install -r src/requirements.txt
```

### 5) Quick manual test (optional)

Plug in the **ELM327 USB** adapter. Then:

```bash
cd /home/pi/rpi-obd2-led-dash
bash src/run.sh
```

You should see the startup animation and live data when the car / adapter responds.  
Stop with `Ctrl+C`. GPIO needs **root** — `run.sh` uses `sudo`.

### 6) Install autostart (systemd)

This installs **`dash-dashboard.service`**, enables it on boot, and starts it now:

```bash
cd /home/pi/rpi-obd2-led-dash
sudo bash scripts/install_autostart.sh
```

### 7) Verify the service

```bash
systemctl status dash-dashboard.service --no-pager
journalctl -u dash-dashboard.service -f
```

### 8) Confirm after reboot

```bash
sudo reboot
```

After the Pi comes back:

```bash
systemctl status dash-dashboard.service --no-pager
```

You should see **`active (running)`** when OBD and LEDs are OK.

### Disable autostart

```bash
sudo systemctl disable --now dash-dashboard.service
```

---

## Features

- Symmetric RPM bar (configurable range and colors)
- Gear estimate from RPM / speed (no gear sensor)
- EMA-smoothed RPM for the bar; raw RPM for gear logic
- Over-rev: top row blinks red above `RPM_MAX + OVER_REV_ALERT_MARGIN_RPM`
- Optional performance monitor over SSH (`tools/main_perf.py`)

## Hardware

| Component | Notes |
|-----------|--------|
| Raspberry Pi | 3 / 4 / Zero 2 W |
| LED matrix | WS2812B 8×8 |
| Adapter | ELM327 USB |

## Project layout

```text
rpi-obd2-led-dash/
├── src/
│   ├── config.py
│   ├── display.py
│   ├── main.py
│   ├── obd_reader.py
│   ├── led_strip.py
│   ├── gear_predictor.py
│   ├── startup_check.py
│   ├── requirements.txt
│   └── run.sh
├── tools/
│   ├── main_perf.py
│   └── run_perf.sh
├── scripts/
│   └── install_autostart.sh
└── LICENSE
```

## Debug over SSH

From your PC:

```bash
ssh pi@<raspberry-pi-ip>
```

On the Pi:

```bash
cd /home/pi/rpi-obd2-led-dash
bash tools/run_perf.sh
```

## Configuration

Edit **`src/config.py`**: RPM range, colours, over-rev margin/blink, gear ratios, OBD options (`OBD_PROTOCOL`, etc.).

## Gear prediction

`RPM / speed` is compared to `GEARS_RATIOS` within `GEAR_TOLERANCE`; the displayed gear uses a majority vote over the last 5 samples.

## Requirements (Python packages)

- `rpi_ws281x`
- `obd`
- `psutil` (for `main_perf.py`)

## License

MIT — see `LICENSE`.
