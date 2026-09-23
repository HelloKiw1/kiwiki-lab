import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


HOST_AGENT_URL = "http://127.0.0.1:9100/status"
HOST_AGENT_TIMEOUT = 1.5


def get_host_agent_status(timeout=HOST_AGENT_TIMEOUT):
    """Return the Host Agent payload, or None when it cannot be read."""

    request = Request(HOST_AGENT_URL, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.getcode() != 200:
                return None
            payload = response.read()
        data = json.loads(payload.decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ConnectionError, OSError, ValueError):
        return None
    except Exception:
        # The agent is an optional monitoring source and must never break the API.
        return None

    return data if isinstance(data, dict) else None


def get_device_status(host_agent_status):
    device = host_agent_status.get("device") if isinstance(host_agent_status, dict) else {}
    device = device if isinstance(device, dict) else {}
    return {
        "manufacturer": device.get("manufacturer"),
        "model": device.get("model"),
        "device": device.get("device"),
        "android": device.get("android"),
    }
