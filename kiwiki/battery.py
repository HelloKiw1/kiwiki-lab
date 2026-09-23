from pathlib import Path

import psutil


NOT_AVAILABLE = None
POWER_SUPPLY_PATH = Path("/sys/class/power_supply")
THERMAL_PATH = Path("/sys/class/thermal")


def _read_number(path):
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _read_text(path):
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _sysfs_battery():
    if not POWER_SUPPLY_PATH.exists():
        return None

    batteries = sorted(POWER_SUPPLY_PATH.glob("*/capacity"))
    for capacity_path in batteries:
        capacity = _read_number(capacity_path)
        if capacity is None:
            continue

        battery_dir = capacity_path.parent
        status = _read_text(battery_dir / "status")
        temperature = _read_number(battery_dir / "temp")
        if temperature is not None:
            temperature = temperature / 10 if temperature > 100 else temperature

        return {
            "available": True,
            "percent": round(capacity, 1),
            "status": status or "Unknown",
            "temperature_c": round(temperature, 1) if temperature is not None else NOT_AVAILABLE,
        }
    return None


def _thermal_temperature():
    if not THERMAL_PATH.exists():
        return None

    for temperature_path in sorted(THERMAL_PATH.glob("thermal_zone*/temp")):
        temperature = _read_number(temperature_path)
        if temperature is not None:
            return round(temperature / 1000 if temperature > 150 else temperature, 1)
    return None


def get_battery_status():
    battery = None
    try:
        battery = psutil.sensors_battery()
    except (AttributeError, OSError):
        pass

    if battery is not None:
        return {
            "available": True,
            "percent": round(battery.percent, 1),
            "status": "Charging" if battery.power_plugged else "Discharging",
            "temperature_c": NOT_AVAILABLE,
        }

    battery = _sysfs_battery()
    if battery is None:
        return {
            "available": False,
            "percent": NOT_AVAILABLE,
            "status": "Not available",
            "temperature_c": _thermal_temperature(),
        }

    return battery

