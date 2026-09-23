from datetime import datetime, timezone
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


def _is_proot_or_android(host_agent_status=None):
    if host_agent_status is not None:
        return True
    markers = ("PROOT_TMP_DIR", "PROOT_LOADER", "TERMUX_VERSION", "ANDROID_ROOT", "ANDROID_DATA")
    return any(os.environ.get(marker) for marker in markers)


def _uptime(host_agent_status=None):
    if _is_proot_or_android(host_agent_status):
        return {"seconds": None, "formatted": "Not available"}

    boot_time = _safe_call(psutil.boot_time)
    if boot_time is None:
        return {"seconds": None, "formatted": "Not available"}

    seconds = max(0, int(datetime.now(timezone.utc).timestamp() - boot_time))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    return {
        "seconds": seconds,
        "formatted": f"{days}d {hours:02d}h {minutes:02d}m",
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
