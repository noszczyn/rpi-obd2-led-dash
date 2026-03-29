# Raspberry Pi Read-Only Guide (ochrona karty SD)

Ten guide pozwala uruchamiac dashboard po podaniu zasilania i ograniczyc ryzyko uszkodzenia karty SD przy naglym odcieciu pradu (np. po zgaszeniu auta).

## 1) Najpierw autostart aplikacji

W repo jest skrypt:

```bash
cd /home/pi/dash
sudo bash scripts/install_autostart.sh /dev/ttyUSB0
```

Po instalacji:

```bash
systemctl status dash-dashboard.service --no-pager
journalctl -u dash-dashboard.service -f
```

## 2) Wlacz read-only przez raspi-config (zalecane)

Najbezpieczniej uzyc wbudowanej opcji Raspberry Pi OS:

```bash
sudo raspi-config
```

Nastepnie:

- `Performance Options`
- `Overlay File System`
- `Enable`
- potwierdz read-only dla partycji boot (jesli system pyta)
- reboot

Po restarcie system startuje w trybie nakladkowym (overlay), wiec nagle odciecie zasilania jest mniej ryzykowne dla karty SD.

## 3) Jak robic aktualizacje pozniej

Przed aktualizacjami kodu lub systemu:

```bash
sudo raspi-config
```

- `Performance Options` -> `Overlay File System` -> `Disable`
- reboot
- wykonaj zmiany (`git pull`, `make`, itp.)
- wlacz overlay ponownie i reboot

## 4) Szybka weryfikacja po konfiguracji

- Serwis dziala po reboocie:
  - `systemctl is-enabled dash-dashboard.service`
  - `systemctl status dash-dashboard.service --no-pager`
- Logi sa widoczne:
  - `journalctl -u dash-dashboard.service -n 50 --no-pager`
- Po odlaczeniu i ponownym podlaczeniu zasilania aplikacja startuje automatycznie.

## 5) Dodatkowe zalecenia dla auta

- Uzyj dobrego zasilacza 5V (stabilne napiecie) i przewodow o niskim spadku napiecia.
- Rozwaz superkondensator/UPS HAT, jesli zdarzaja sie szybkie zaniki zasilania podczas rozruchu.
- Trzymaj backup obrazu SD po skonfigurowaniu wszystkiego.
