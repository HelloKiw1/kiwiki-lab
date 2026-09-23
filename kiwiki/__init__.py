from pathlib import Path

from flask import Flask, jsonify, render_template

from .battery import get_battery_status
from .host_agent import get_device_status, get_host_agent_status
from .network import get_network_status
from .services import get_services_status
from .system import get_system_status


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/api/status")
    def api_status():
        host_agent_status = get_host_agent_status()
        return jsonify(
            {
                "system": get_system_status(host_agent_status),
                "battery": get_battery_status(host_agent_status),
                "network": get_network_status(host_agent_status),
                "device": get_device_status(host_agent_status),
                "services": get_services_status(),
            }
        )

    return app
