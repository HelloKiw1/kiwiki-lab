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


def get_network_status():
    counters = psutil.net_io_counters()
    return {
        "ip": _server_ip(),
        "bytes_sent": counters.bytes_sent if counters else 0,
        "bytes_received": counters.bytes_recv if counters else 0,
        "packets_sent": counters.packets_sent if counters else 0,
        "packets_received": counters.packets_recv if counters else 0,
    }

