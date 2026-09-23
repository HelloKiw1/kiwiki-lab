from datetime import datetime, timezone
import os
import platform
import socket
import sys

import psutil


def _percentage(value):
    return round(float(value), 1)


def _uptime():
    seconds = max(0, int(datetime.now(timezone.utc).timestamp() - psutil.boot_time()))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    return {
        "seconds": seconds,
        "formatted": f"{days}d {hours:02d}h {minutes:02d}m",
    }


def get_system_status():
    disk_path = os.path.abspath(os.sep)
    disk = psutil.disk_usage(disk_path)
    memory = psutil.virtual_memory()

    return {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}".strip(),
        "python_version": platform.python_version(),
        "cpu_percent": _percentage(psutil.cpu_percent(interval=None)),
        "memory": {
            "percent": _percentage(memory.percent),
            "used_bytes": memory.used,
            "total_bytes": memory.total,
        },
        "storage": {
            "percent": _percentage(disk.percent),
            "used_bytes": disk.used,
            "total_bytes": disk.total,
        },
        "uptime": _uptime(),
    }

