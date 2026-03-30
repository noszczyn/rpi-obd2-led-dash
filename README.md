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

**How this matches the code:** the unit runs **`python3 /…/src/main.py`** with **`WorkingDirectory`** set to **`src/`** (same layout as manual `cd src && sudo python3 main.py`). Imports resolve via the script directory. **`User=root`** matches **`src/run.sh`** (GPIO / WS2812 needs root on a typical Pi). Dependencies are installed with the same **`python3`** as **`ExecStart`** (paths are written at install time). **`Restart=always`** brings the service back after crashes; OBD port is only **`src/config.py`** (`OBD_PORT`), not a systemd argument. Re-run the install script after moving the repo to refresh absolute paths in the unit file.

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

Edit **`src/config.py`**: RPM range, colours, over-rev margin/blink, gear ratios, OBD (`OBD_PORT`, `OBD_PROTOCOL`, etc.).

## RPM bar (top row) — how it lights

Assumes default **`config.py`**: `RPM_START = 2000`, `RPM_MAX = 4500`, `RPM_BASE_PAIRS = 3`, `OVER_REV_ALERT_MARGIN_RPM = 500` (alert when **`rpm > 5000`**). The bar grows **symmetrically** from the outer columns toward the centre; the first three “pair bands” from the outside are **blue**, the innermost active pair is **red** (`rpm_shift`).

**Legend (one character = one LED on the top row, left → right):**

| Symbol | Meaning |
|--------|---------|
| `B` | Blue (`rpm_base`) |
| `R` | Red (`rpm_shift`) |
| `.` | Off |

**Sweep in 100 RPM steps from 2001** (representative ranges):

| RPM range | Top row pattern |
|-----------|-----------------|
| 2001–2601 | `B......B` |
| 2701–3201 | `BB....BB` |
| 3301–3801 | `BBB..BBB` |
| 3901–4901 | `BBBRRBBB` |

**Above 5000 RPM** (`rpm > RPM_MAX + OVER_REV_ALERT_MARGIN_RPM`): the normal bar is **not** shown; the **entire** top row alternates for over-rev warning:

| Phase | Top row |
|-------|---------|
| ALERT_ON | `RRRRRRRR` |
| ALERT_OFF | `........` |

Blink period: `OVER_REV_BLINK_PERIOD_SEC` (default 0.16 s).

**Exact pair count** (from `display.update_rpm_lights`):  
`active_pairs = ceil(4 × (rpm − RPM_START) / (RPM_MAX − RPM_START))` with four column-pairs on an 8-wide matrix. That gives band edges at **2625**, **3250**, **3875** (between 1↔2, 2↔3, 3↔4 pairs). The table above uses **100 RPM** steps and matches those bands for the listed intervals.

## Troubleshooting

- **Red pattern on the matrix (error glyph)** — OBD did not connect: no ELM327 on USB, wrong device, or ignition off. Check logs: `journalctl -u dash-dashboard.service -b --no-pager` (look for `No OBD-II adapters` or serial errors).
- **Force a serial port** — set `OBD_PORT = "/dev/ttyUSB0"` or `"/dev/ttyACM0"` in `src/config.py` if auto-detection fails, then `sudo systemctl restart dash-dashboard.service`.
- **Read-only / overlay root** — if you enabled overlay in `raspi-config`, kernel and initramfs updates need a **writable** `/boot/firmware`. Disable overlay (or remount appropriately) before `apt full-upgrade`; otherwise `dpkg` may leave packages half-configured (`Read-only file system` when copying initramfs).

## Gear prediction

`RPM / speed` is matched to `GEARS_RATIOS` within `GEAR_TOLERANCE`. The **`GearPipeline`** (in `gear_predictor.py`) applies, in order:

1. **Neutral deadband** — `NEUTRAL_SPEED_ON` / `NEUTRAL_SPEED_OFF` (hysteresis so speed ~3–6 km/h does not flip 0 ↔ gear).
2. **Upshift guard** (RPM jump) as before.
3. **Median of the last `GEAR_FILTER_LEN` (3) samples** — dampens a single bad OBD frame.
4. **Hysteresis** — `GEAR_HYSTERESIS_K` consecutive median values must agree; between gears, the new ratio must be closer by `GEAR_HYSTERESIS_DEV_MARGIN` than the current stable gear.
5. **Unknown hold** — if the stable gear is not yet valid, the last good digit is kept for `GEAR_UNKNOWN_HOLD_SEC` (e.g. 0.2 s).

(Historyczna funkcja `predict_gear()` została usunięta — aktualnie używana jest tylko `GearPipeline`, bo daje stabilniejszy wynik.)

## Requirements (Python packages)

- `rpi_ws281x`
- `obd`
- `psutil` (for `main_perf.py`)

## License

MIT — see `LICENSE`.
