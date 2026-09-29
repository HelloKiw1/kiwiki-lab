#!/usr/bin/env python3

import json
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
PORT = 9100
INTERFACE = "wlan0"


def run_json(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


def run_text(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except Exception:
        return None


def getprop(name):
    return run_text(["getprop", name])


def read_int(path):
    try:
        return int(Path(path).read_text().strip())
    except Exception:
        return None


def get_uptime():
    # CLOCK_BOOTTIME inclui tempo em suspensão quando disponível.
    clock = getattr(time, "CLOCK_BOOTTIME", None)

    if clock is not None:
        try:
            return float(time.clock_gettime(clock))
        except Exception:
            pass

    # Fallback seguro no Android.
    try:
        return float(time.monotonic())
    except Exception:
        return None


def get_device():
    return {
        "manufacturer": getprop("ro.product.manufacturer"),
        "model": getprop("ro.product.model"),
        "device": getprop("ro.product.device"),
        "android": getprop("ro.build.version.release"),
    }


def get_battery():
    data = run_json(["termux-battery-status"])

    if not isinstance(data, dict):
        return {
            "available": False,
            "percentage": None,
            "status": "Not available",
            "health": None,
            "plugged": None,
            "temperature_c": None,
            "voltage_mv": None,
            "current_average": None,
            "technology": None,
        }

    return {
        "available": True,
        "percentage": data.get("percentage"),
        "status": data.get("status"),
        "health": data.get("health"),
        "plugged": data.get("plugged"),
        "temperature_c": data.get("temperature"),
        "voltage_mv": data.get("voltage"),
        "current_average": data.get("current_average"),
        "technology": data.get("technology"),
    }


def get_wifi():
    data = run_json(["termux-wifi-connectioninfo"])

    if not isinstance(data, dict):
        return {
            "available": False,
            "ip": None,
            "frequency_mhz": None,
            "link_speed_mbps": None,
            "rssi": None,
            "ssid": None,
        }

    return {
        "available": True,
        "ip": data.get("ip"),
        "frequency_mhz": data.get("frequency_mhz"),
        "link_speed_mbps": data.get("link_speed_mbps"),
        "rssi": data.get("rssi"),
        "ssid": data.get("ssid"),
    }


def get_network():
    base = Path("/sys/class/net") / INTERFACE / "statistics"

    return {
        "available": True,
        "interface": INTERFACE,
        "bytes_received": read_int(base / "rx_bytes"),
        "bytes_sent": read_int(base / "tx_bytes"),
        "packets_received": read_int(base / "rx_packets"),
        "packets_sent": read_int(base / "tx_packets"),
    }


def build_status():
    return {
        "device": get_device(),
        "battery": get_battery(),
        "wifi": get_wifi(),
        "network": get_network(),
        "agent_uptime_seconds": get_uptime(),
        "agent": {
            "name": "Kiwiki Host Agent",
            "version": "2.0",
            "port": PORT,
        },
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            payload = json.dumps(
                build_status(),
                ensure_ascii=False
            ).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/health":
            payload = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Kiwiki Host Agent listening on http://{HOST}:{PORT}")
    server.serve_forever()
