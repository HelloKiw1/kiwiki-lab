import os
import platform
import socket

import psutil


def _percentage(value):
    return round(float(value), 1) if value is not None else None


def _safe_call(function, default=None):
    try:
        return function()
    except (PermissionError, OSError, ValueError, psutil.Error):
        return default


def _format_uptime(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts or seconds % 60:
        parts.append(f"{seconds % 60}s")
    return " ".join(parts)


def _uptime(host_agent_status=None):
    if not isinstance(host_agent_status, dict):
        return {"seconds": None, "formatted": "Not available", "source": "unavailable"}

    try:
        seconds = int(float(host_agent_status.get("agent_uptime_seconds")))
    except (TypeError, ValueError):
        return {"seconds": None, "formatted": "Not available", "source": "unavailable"}

    if seconds < 0:
        return {"seconds": None, "formatted": "Not available", "source": "unavailable"}

    return {
        "seconds": seconds,
        "formatted": _format_uptime(seconds),
        "source": "host_agent",
    }


def get_system_status(host_agent_status=None):
    disk_path = os.path.abspath(os.sep)
    disk = _safe_call(lambda: psutil.disk_usage(disk_path))
    memory = _safe_call(psutil.virtual_memory)
    cpu_percent = _safe_call(lambda: psutil.cpu_percent(interval=None))

    try:
        operating_system = f"{platform.system()} {platform.release()}".strip()
    except (PermissionError, OSError):
        operating_system = None

    return {
        "hostname": _safe_call(socket.gethostname),
        "os": operating_system,
        "python_version": _safe_call(platform.python_version),
        "cpu_percent": _percentage(cpu_percent),
        "memory": {
            "percent": _percentage(getattr(memory, "percent", None)),
            "used_bytes": getattr(memory, "used", None),
            "total_bytes": getattr(memory, "total", None),
        },
        "storage": {
            "percent": _percentage(getattr(disk, "percent", None)),
            "used_bytes": getattr(disk, "used", None),
            "total_bytes": getattr(disk, "total", None),
        },
        "uptime": _uptime(host_agent_status),
    }
