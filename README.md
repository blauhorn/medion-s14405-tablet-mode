# Medion S14405 Tablet Mode for Linux

**Experimental community workaround** for the MEDION S14405 convertible on Ubuntu/GNOME Wayland.

This project reads two Kionix accelerometers, infers a notebook/tablet posture and emits a Linux `SW_TABLET_MODE` event through `uinput`. On the tested system, GNOME/libinput use that event to disable the built-in keyboard/touchpad and permit auto-rotation. A udev rule fixes display accelerometer orientation.

## Status

- ✅ Tested interactively: tent mode, keyboard/touchpad disabled, return to notebook mode, rotation in four orientations, fully folded tablet posture.
- ✅ **Automatic startup after reboot verified** on the original test machine (23 October 2026).
- ⚠️ Calibrated for **one S14405**, not validated on other Medion models.
- ⚠️ The computed projected sensor angle is *not* the actual hinge angle. Certain positions or motions may be ambiguous.

## Hardware and environment

- Medion S14405 with `KIOX020A` (keyboard base) and `KIOX010A` (display)
- Ubuntu GNOME / Wayland (tested using kernel `7.0.0-38-generic`)
- Python 3, `python3-evdev`, `iio-sensor-proxy`, systemd, udev

## How it works

1. Poll each sensor's IIO raw acceleration (`/sys/bus/iio/devices/iio:device*`).
2. Compare projected X/Z gravity vectors and classify observed states using empirical thresholds (not mechanical hinge degrees).
3. Wait two seconds for a stable state, then send `EV_SW / SW_TABLET_MODE` via `python-evdev`'s `UInput`.
4. Use the udev `ACCEL_LOCATION` and `ACCEL_MOUNT_MATRIX` properties for correct GNOME rotation.

## Installation

**Important:** save your files, test with an external USB keyboard available, and inspect scripts before running as root. Installation replaces no existing files; it refuses to proceed if destination files exist. If you already followed a manual setup, you have to back up/remove the matching files before using this installer. Do **not** run a second instance of the service.

```bash
sudo ./scripts/install.sh
systemctl status medion-tablet.service
journalctl -u medion-tablet.service -f
```

Reboot and test the tablet mode **and recovery to laptop mode**. Automatic startup was verified on the original test machine. If the service cannot find the sensors, inspect `journalctl -u medion-tablet.service`.

### Important: remove a forced kernel switch

If you previously added `intel_hid.enable_sw_tablet_mode=2` to `GRUB_CMDLINE_LINUX_DEFAULT`, remove it from `/etc/default/grub`, run `sudo update-grub`, and reboot **before** testing this project. On the tested S14405, the otherwise inactive Intel HID tablet switch conflicted with the virtual switch and prevented keyboard/touchpad suspension.

## Uninstall / emergency recovery

If the keyboard or touchpad is unexpectedly disabled, use an external USB keyboard, switch back to laptop posture, or stop the service:

```bash
sudo systemctl stop medion-tablet.service
```

To uninstall:

```bash
sudo ./scripts/uninstall.sh
```

The uninstall script deletes the project-owned files at the documented paths; **do not** use it if you have merged your own custom rules into them. It does not uninstall the OS packages.

## Configuration

- Mode thresholds are in `src/medion-tablet-service.py`, function `classify()`.
- The calibrated matrix for the display sensor is `0, -1, 0; -1, 0, 0; 0, 0, -1` in `udev/61-medion-sensors.rules`.
- `ACCEL_LOCATION=base` is set for `KIOX020A` and `display` for `KIOX010A`.
- The switch reports **notebook mode by default** and switches after two seconds of stable classification.

## On-screen keyboard (Ubuntu GNOME / Wayland)

GNOME has a built-in on-screen keyboard; no additional keyboard application or root-level service is needed. To enable it for the signed-in user:

```bash
gsettings set org.gnome.desktop.a11y.applications screen-keyboard-enabled true
```

Alternatively, enable **Settings → Accessibility → Typing → Screen Keyboard**. With touch input, it should appear when a supported text field is tapped. Tap the keyboard's down-arrow button to hide it, or swipe up from the bottom of the touchscreen to bring it back. Some applications, particularly those running under XWayland, may not trigger it reliably. This is a **per-user GNOME setting**, not an action performed by this project's root-run tablet detection daemon; the setting may also make the keyboard available while in laptop mode.

## Troubleshooting

```bash
for d in /sys/bus/iio/devices/iio:device*; do echo "$(cat "$d/name"): $(cat "$d"/in_accel_{x,y,z}_raw | xargs)"; done
monitor-sensor
sudo libinput debug-events --show-keycodes
```

If the screen does not rotate, verify the display accelerometer and GNOME rotation lock. If keyboard/touchpad remain active, look for another `SW_TABLET_MODE` device, especially a forced Intel HID switch. `libinput debug-events` should show the virtual switch toggle to `state 1` in tablet mode and `state 0` on return.

## Known limitations

- Sensor-only gravity calculations cannot guarantee an unambiguous hinge angle in all spatial positions or while moving.
- This is a model-specific workaround, not an upstream kernel fix.
- Runs as root to access `/dev/uinput` and sensors; restricting privileges is potential future work.

## License

MIT — see [LICENSE](LICENSE).
