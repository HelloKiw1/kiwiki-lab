import socket

import psutil


def _server_ip():
    try:
        addresses = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        for address in addresses:
            candidate = address[4][0]
            if not candidate.startswith("127."):
                return candidate
    except (OSError, socket.gaierror):
        pass
    return None


def _empty_counters():
    return {
        "bytes_sent": None,
        "bytes_received": None,
        "packets_sent": None,
        "packets_received": None,
    }


def get_network_status():
    status = {"ip": _server_ip(), **_empty_counters()}

    try:
        counters = psutil.net_io_counters()
    except (PermissionError, OSError, psutil.Error):
        return status

    if counters is None:
        return status

    status.update(
        {
            "bytes_sent": getattr(counters, "bytes_sent", None),
            "bytes_received": getattr(counters, "bytes_recv", None),
            "packets_sent": getattr(counters, "packets_sent", None),
            "packets_received": getattr(counters, "packets_recv", None),
        }
    )
    return status
