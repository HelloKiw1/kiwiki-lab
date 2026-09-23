from dataclasses import dataclass
import errno
import socket


@dataclass(frozen=True)
class ServiceConfig:
    """Configuration for one independently monitored service.

    TCP is the only check currently enabled. ``process_names`` and
    ``systemd_unit`` are kept as extension points for future read-only checks.
    """

    id: str
    name: str
    ports: tuple[int, ...] = ()
    process_names: tuple[str, ...] = ()
    systemd_unit: str | None = None


# Add another entry here when a new service should be monitored. Each entry is
# checked independently, so one database being online does not affect another.
SERVICES = (
    ServiceConfig(id="kiwiki", name="Kiwiki Lab", ports=(5000,)),
    ServiceConfig(id="codex", name="Django / Codex", ports=(8000,)),
    ServiceConfig(id="nginx", name="Nginx", ports=(8080, 8081)),
ServiceConfig(id="ssh", name="SSH", ports=(8022,)),
    ServiceConfig(id="postgresql", name="PostgreSQL", ports=(5432,)),
    ServiceConfig(id="mysql", name="MySQL / MariaDB", ports=(3306,)),
    ServiceConfig(id="redis", name="Redis", ports=(6379,)),
)


def _check_port(port, host="127.0.0.1", timeout=0.25):
    """Return True for open, False for refused, or None when unknown."""

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except ConnectionRefusedError:
        return False
    except TimeoutError:
        return None
    except OSError as error:
        if error.errno == errno.ECONNREFUSED:
            return False
        return None
    except (TypeError, ValueError):
        return None


def _check_service(service):
    checks = {port: _check_port(port) for port in service.ports}
    open_ports = [port for port, is_open in checks.items() if is_open is True]

    if open_ports:
        status = "Online"
    elif not checks or all(is_open is False for is_open in checks.values()):
        status = "Offline" if checks else "Unknown"
    else:
        status = "Unknown"

    return status, open_ports


def get_services_status():
    statuses = []
    for service in SERVICES:
        status, open_ports = _check_service(service)
        statuses.append(
            {
                "id": service.id,
                "name": service.name,
                "ports": list(service.ports),
                "open_ports": open_ports,
                "status": status,
            }
        )
    return statuses
