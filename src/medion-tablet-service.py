#!/usr/bin/env python3
"""Medion S14405: infer tablet mode from two Kionix accelerometers.

Sensor-angle thresholds are based on one tested S14405 and are not a
mechanical hinge-angle measurement. GNOME handles screen rotation separately.
"""
import math
import signal
import time
from pathlib import Path
from evdev import UInput, ecodes

ROOT = Path('/sys/bus/iio/devices')
INTERVAL = 0.2
STABLE_TIME = 2.0


def find_sensor(identifier):
    for path in ROOT.glob('iio:device*'):
        if identifier in (path / 'name').read_text():
            return path
    raise RuntimeError(f'Missing accelerometer: {identifier}')


def xyz(device):
    return [int((device / f'in_accel_{axis}_raw').read_text()) for axis in 'xyz']


def classify(base, display):
    if not all(350 <= math.hypot(v[0], v[2]) <= 700 for v in (base, display)):
        return None
    ax, az = base[0], base[2]
    bx, bz = display[0], display[2]
    dot = ax * bx + az * bz
    cross = ax * bz - az * bx
    angle = math.degrees(math.atan2(cross, dot)) % 360
    if 145 <= angle <= 280:
        return 'TABLET'
    if 40 <= angle <= 120:
        return 'NOTEBOOK'
    return None


def main():
    base = find_sensor('KIOX020A')
    display = find_sensor('KIOX010A')
    stop = False

    def request_stop(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    with UInput({ecodes.EV_SW: [ecodes.SW_TABLET_MODE]}, name='Medion S14405 Tablet Mode') as ui:
        current = 'NOTEBOOK'
        candidate = None
        since = time.monotonic()

        def set_mode(mode):
            ui.write(ecodes.EV_SW, ecodes.SW_TABLET_MODE, int(mode == 'TABLET'))
            ui.syn()
            print(f'Mode: {mode}', flush=True)

        # The switch defaults to notebook mode. Re-evaluate after 2 s.
        set_mode(current)
        try:
            while not stop:
                try:
                    detected = classify(xyz(base), xyz(display))
                except (OSError, ValueError):
                    detected = None
                now = time.monotonic()
                if detected != candidate:
                    candidate, since = detected, now
                if detected is not None and detected != current and now - since >= STABLE_TIME:
                    set_mode(detected)
                    current = detected
                time.sleep(INTERVAL)
        finally:
            set_mode('NOTEBOOK')


if __name__ == '__main__':
    main()
