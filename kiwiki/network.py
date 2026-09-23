import socket

import psutil

from .host_agent import get_host_agent_status


_AGENT_STATUS_UNSET = object()


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
        "interface": None,
        "link_speed_mbps": None,
        "frequency_mhz": None,
        "rssi": None,
        "bytes_sent": None,
        "bytes_received": None,
        "packets_sent": None,
        "packets_received": None,
    }


def _agent_network_status(host_agent_status):
    if not isinstance(host_agent_status, dict):
        return None

    wifi = host_agent_status.get("wifi")
    network = host_agent_status.get("network")
    if not isinstance(wifi, dict) and not isinstance(network, dict):
        return None
    wifi = wifi if isinstance(wifi, dict) else {}
    network = network if isinstance(network, dict) else {}
    return {
        "ip": wifi.get("ip"),
        "interface": network.get("interface"),
        "link_speed_mbps": wifi.get("link_speed_mbps"),
        "frequency_mhz": wifi.get("frequency_mhz"),
        "rssi": wifi.get("rssi"),
        "bytes_sent": network.get("bytes_sent"),
        "bytes_received": network.get("bytes_received"),
        "packets_sent": network.get("packets_sent"),
        "packets_received": network.get("packets_received"),
    }


def _local_network_status():
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


def get_network_status(host_agent_status=_AGENT_STATUS_UNSET):
    if host_agent_status is _AGENT_STATUS_UNSET:
        host_agent_status = get_host_agent_status()

    agent_network = _agent_network_status(host_agent_status)
    if agent_network is not None:
        return agent_network
    return _local_network_status()
