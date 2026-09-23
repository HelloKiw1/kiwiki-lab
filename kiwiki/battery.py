from pathlib import Path

import psutil

from .host_agent import get_host_agent_status


NOT_AVAILABLE = None
POWER_SUPPLY_PATH = Path("/sys/class/power_supply")
THERMAL_PATH = Path("/sys/class/thermal")
_AGENT_STATUS_UNSET = object()


def _number(value, digits=None):
    if value is None:
        return None
    try:
        result = float(value)
        return round(result, digits) if digits is not None else result
    except (TypeError, ValueError):
        return None


def _agent_battery_status(host_agent_status):
    if not isinstance(host_agent_status, dict):
        return None
    battery = host_agent_status.get("battery")
    if not isinstance(battery, dict):
        return None

    raw_status = battery.get("status")
    status = str(raw_status).replace("_", " ").title() if raw_status else "Unknown"
    return {
        "available": bool(battery.get("available")),
        "percent": _number(battery.get("percentage"), 1),
        "status": status,
        "temperature_c": _number(battery.get("temperature_c"), 1),
        "health": battery.get("health"),
        "plugged": battery.get("plugged"),
        "voltage_mv": _number(battery.get("voltage_mv"), 1),
        "current_average": _number(battery.get("current_average"), 1),
        "technology": battery.get("technology"),
    }


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
    try:
        if not POWER_SUPPLY_PATH.exists():
            return None
        batteries = sorted(POWER_SUPPLY_PATH.glob("*/capacity"))
    except (PermissionError, OSError):
        return None

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
    try:
        if not THERMAL_PATH.exists():
            return None
        temperature_paths = sorted(THERMAL_PATH.glob("thermal_zone*/temp"))
    except (PermissionError, OSError):
        return None

    for temperature_path in temperature_paths:
        temperature = _read_number(temperature_path)
        if temperature is not None:
            return round(temperature / 1000 if temperature > 150 else temperature, 1)
    return None


def _local_battery_status():
    battery = None
    try:
        battery = psutil.sensors_battery()
    except (AttributeError, PermissionError, OSError, psutil.Error):
        pass

    if battery is not None:
        return {
            "available": True,
            "percent": round(battery.percent, 1),
            "status": "Charging" if battery.power_plugged else "Discharging",
            "temperature_c": NOT_AVAILABLE,
            "health": NOT_AVAILABLE,
            "plugged": battery.power_plugged,
            "voltage_mv": NOT_AVAILABLE,
            "current_average": NOT_AVAILABLE,
            "technology": NOT_AVAILABLE,
        }

    battery = _sysfs_battery()
    if battery is None:
        return {
            "available": False,
            "percent": NOT_AVAILABLE,
            "status": "Not available",
            "temperature_c": _thermal_temperature(),
            "health": NOT_AVAILABLE,
            "plugged": NOT_AVAILABLE,
            "voltage_mv": NOT_AVAILABLE,
            "current_average": NOT_AVAILABLE,
            "technology": NOT_AVAILABLE,
        }

    battery.update(
        {
            "health": NOT_AVAILABLE,
            "plugged": NOT_AVAILABLE,
            "voltage_mv": NOT_AVAILABLE,
            "current_average": NOT_AVAILABLE,
            "technology": NOT_AVAILABLE,
        }
    )
    return battery


def get_battery_status(host_agent_status=_AGENT_STATUS_UNSET):
    if host_agent_status is _AGENT_STATUS_UNSET:
        host_agent_status = get_host_agent_status()

    agent_battery = _agent_battery_status(host_agent_status)
    return agent_battery if agent_battery is not None else _local_battery_status()
