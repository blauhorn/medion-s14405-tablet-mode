#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Run with sudo: sudo ./scripts/uninstall.sh' >&2; exit 1; fi
systemctl disable --now medion-tablet.service 2>/dev/null || true
rm -f /etc/systemd/system/medion-tablet.service
rm -f /usr/local/lib/medion-tablet/medion-tablet-service.py
rmdir /usr/local/lib/medion-tablet 2>/dev/null || true
rm -f /etc/udev/rules.d/61-medion-sensors.rules
rm -f /etc/modules-load.d/medion-tablet.conf
systemctl daemon-reload
udevadm control --reload-rules
udevadm trigger --subsystem-match=iio
systemctl restart iio-sensor-proxy
printf 'Removed project files. python3-evdev and iio-sensor-proxy remain installed.\n'
