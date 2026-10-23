#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Run with sudo: sudo ./scripts/install.sh' >&2; exit 1; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for target in /etc/udev/rules.d/61-medion-sensors.rules /etc/systemd/system/medion-tablet.service /usr/local/lib/medion-tablet/medion-tablet-service.py; do
  if [[ -e "$target" ]]; then
    echo "Existing file: $target" >&2
    echo 'Back it up or remove it before installing; no files were changed.' >&2
    exit 1
  fi
done
apt-get update
apt-get install -y python3-evdev iio-sensor-proxy
install -D -m 644 "$ROOT/udev/61-medion-sensors.rules" /etc/udev/rules.d/61-medion-sensors.rules
install -D -m 644 "$ROOT/systemd/medion-tablet.service" /etc/systemd/system/medion-tablet.service
install -D -m 755 "$ROOT/src/medion-tablet-service.py" /usr/local/lib/medion-tablet/medion-tablet-service.py
printf 'uinput\n' > /etc/modules-load.d/medion-tablet.conf
modprobe uinput
udevadm control --reload-rules
udevadm trigger --subsystem-match=iio
systemctl restart iio-sensor-proxy
systemctl daemon-reload
systemctl enable --now medion-tablet.service
printf '\nInstalled. Check: systemctl status medion-tablet.service\n'
