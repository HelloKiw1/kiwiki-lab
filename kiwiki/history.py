import sqlite3
import threading
import time
from pathlib import Path

from .battery import get_battery_status
from .host_agent import get_host_agent_status
from .network import get_network_status
from .system import get_system_status


BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_DB_PATH = BASE_DIR / "data" / "history.db"
COLLECTION_INTERVAL_SECONDS = 60
RAW_RETENTION_SECONDS = 7 * 24 * 60 * 60
HOURLY_RETENTION_SECONDS = 90 * 24 * 60 * 60

NUMERIC_FIELDS = (
    "cpu_percent",
    "memory_percent",
    "storage_percent",
    "battery_percent",
    "battery_temperature_c",
    "battery_current_average",
    "battery_voltage_mv",
    "network_rssi",
    "network_link_speed_mbps",
)
COUNTER_FIELDS = ("network_bytes_sent", "network_bytes_received")
ALL_RAW_FIELDS = NUMERIC_FIELDS + COUNTER_FIELDS


def _empty_history(range_name="1h", granularity="minute"):
    return {"range": range_name, "granularity": granularity, "points": []}


def _numeric(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def collect_current_metrics():
    """Collect only the values that are persisted in the history database."""

    host_agent_status = get_host_agent_status()
    system = get_system_status(host_agent_status)
    battery = get_battery_status(host_agent_status)
    network = get_network_status(host_agent_status)
    return {
        "cpu_percent": system.get("cpu_percent"),
        "memory_percent": (system.get("memory") or {}).get("percent"),
        "storage_percent": (system.get("storage") or {}).get("percent"),
        "battery_percent": battery.get("percent"),
        "battery_temperature_c": battery.get("temperature_c"),
        "battery_current_average": battery.get("current_average"),
        "battery_voltage_mv": battery.get("voltage_mv"),
        "network_bytes_sent": network.get("bytes_sent"),
        "network_bytes_received": network.get("bytes_received"),
        "network_rssi": network.get("rssi"),
        "network_link_speed_mbps": network.get("link_speed_mbps"),
    }


class HistoryStore:
    def __init__(self, path=HISTORY_DB_PATH):
        self.path = Path(path)

    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path), timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self):
        connection = self._connect()
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metrics_raw (
                    timestamp INTEGER PRIMARY KEY,
                    cpu_percent REAL,
                    memory_percent REAL,
                    storage_percent REAL,
                    battery_percent REAL,
                    battery_temperature_c REAL,
                    battery_current_average REAL,
                    battery_voltage_mv REAL,
                    network_bytes_sent INTEGER,
                    network_bytes_received INTEGER,
                    network_rssi REAL,
                    network_link_speed_mbps REAL
                );

                CREATE INDEX IF NOT EXISTS idx_metrics_raw_timestamp
                    ON metrics_raw(timestamp);

                CREATE TABLE IF NOT EXISTS metrics_hourly (
                    hour_timestamp INTEGER PRIMARY KEY,
                    sample_count INTEGER NOT NULL,
                    cpu_percent_avg REAL,
                    cpu_percent_min REAL,
                    cpu_percent_max REAL,
                    memory_percent_avg REAL,
                    memory_percent_min REAL,
                    memory_percent_max REAL,
                    storage_percent_avg REAL,
                    storage_percent_min REAL,
                    storage_percent_max REAL,
                    battery_percent_avg REAL,
                    battery_percent_min REAL,
                    battery_percent_max REAL,
                    battery_temperature_c_avg REAL,
                    battery_temperature_c_min REAL,
                    battery_temperature_c_max REAL,
                    battery_current_average_avg REAL,
                    battery_current_average_min REAL,
                    battery_current_average_max REAL,
                    battery_voltage_mv_avg REAL,
                    battery_voltage_mv_min REAL,
                    battery_voltage_mv_max REAL,
                    network_rssi_avg REAL,
                    network_rssi_min REAL,
                    network_rssi_max REAL,
                    network_link_speed_mbps_avg REAL,
                    network_link_speed_mbps_min REAL,
                    network_link_speed_mbps_max REAL,
                    network_bytes_sent_total INTEGER,
                    network_bytes_received_total INTEGER
                );
                """
            )
            connection.commit()
        finally:
            connection.close()

    def record(self, metrics, timestamp=None):
        timestamp = int(timestamp or time.time()) // 60 * 60
        connection = self._connect()
        try:
            values = [timestamp] + [_numeric(metrics.get(field)) for field in ALL_RAW_FIELDS]
            placeholders = ", ".join("?" for _ in values)
            columns = ", ".join(("timestamp",) + ALL_RAW_FIELDS)
            connection.execute(
                f"INSERT OR IGNORE INTO metrics_raw ({columns}) VALUES ({placeholders})",
                values,
            )
            self._rollup_hour(connection, timestamp // 3600 * 3600)
            self._purge(connection, int(time.time()))
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _stats(rows, field):
        values = [row[field] for row in rows if row[field] is not None]
        if not values:
            return None, None, None
        return sum(values) / len(values), min(values), max(values)

    @staticmethod
    def _counter_total(rows, field):
        previous = None
        total = 0
        found = False
        for row in rows:
            value = row[field]
            if value is None:
                continue
            found = True
            if previous is not None:
                total += max(0, value - previous)
            previous = value
        return total if found else None

    def _rollup_hour(self, connection, hour_timestamp):
        rows = connection.execute(
            "SELECT * FROM metrics_raw WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp",
            (hour_timestamp, hour_timestamp + 3600),
        ).fetchall()
        if not rows:
            return

        values = {"hour_timestamp": hour_timestamp, "sample_count": len(rows)}
        for field in NUMERIC_FIELDS:
            average, minimum, maximum = self._stats(rows, field)
            values[f"{field}_avg"] = average
            values[f"{field}_min"] = minimum
            values[f"{field}_max"] = maximum
        values["network_bytes_sent_total"] = self._counter_total(rows, "network_bytes_sent")
        values["network_bytes_received_total"] = self._counter_total(rows, "network_bytes_received")

        columns = tuple(values)
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(f"{column}=excluded.{column}" for column in columns if column != "hour_timestamp")
        connection.execute(
            f"INSERT INTO metrics_hourly ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT(hour_timestamp) DO UPDATE SET {updates}",
            tuple(values[column] for column in columns),
        )

    def _purge(self, connection, now):
        connection.execute(
            "DELETE FROM metrics_raw WHERE timestamp < ?",
            (now - RAW_RETENTION_SECONDS,),
        )
        connection.execute(
            "DELETE FROM metrics_hourly WHERE hour_timestamp < ?",
            (now - HOURLY_RETENTION_SECONDS,),
        )

    def summary(self, range_name):
        ranges = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600, "7d": 7 * 24 * 3600}
        seconds = ranges[range_name]
        use_hourly = range_name == "7d"
        granularity = "hour" if use_hourly else "minute"
        table = "metrics_hourly" if use_hourly else "metrics_raw"
        timestamp_column = "hour_timestamp" if use_hourly else "timestamp"
        start = int(time.time()) - seconds

        connection = self._connect()
        try:
            rows = connection.execute(
                f"SELECT * FROM {table} WHERE {timestamp_column} >= ? ORDER BY {timestamp_column}",
                (start,),
            ).fetchall()
        finally:
            connection.close()

        points = []
        previous_sent = None
        previous_received = None
        for row in rows:
            if use_hourly:
                point = {"timestamp": row["hour_timestamp"]}
                for field in NUMERIC_FIELDS:
                    point[field] = row[f"{field}_avg"]
                    point[f"{field}_min"] = row[f"{field}_min"]
                    point[f"{field}_max"] = row[f"{field}_max"]
                point["network_rx_bytes"] = row["network_bytes_received_total"]
                point["network_tx_bytes"] = row["network_bytes_sent_total"]
            else:
                point = {"timestamp": row["timestamp"]}
                for field in ALL_RAW_FIELDS:
                    point[field] = row[field]
                sent = row["network_bytes_sent"]
                received = row["network_bytes_received"]
                point["network_tx_bytes"] = max(0, sent - previous_sent) if sent is not None and previous_sent is not None else None
                point["network_rx_bytes"] = max(0, received - previous_received) if received is not None and previous_received is not None else None
                previous_sent = sent if sent is not None else previous_sent
                previous_received = received if received is not None else previous_received
            points.append(point)

        return {"range": range_name, "granularity": granularity, "points": points}


_collector_lock = threading.Lock()
_collector_thread = None


def _collector_loop(store):
    while True:
        try:
            store.record(collect_current_metrics())
        except Exception:
            # History is optional; monitoring and the web server must continue.
            pass
        time.sleep(COLLECTION_INTERVAL_SECONDS)


def start_history_collector():
    global _collector_thread
    with _collector_lock:
        if _collector_thread is not None and _collector_thread.is_alive():
            return
        store = HistoryStore()
        try:
            store.initialize()
        except Exception:
            return
        _collector_thread = threading.Thread(
            target=_collector_loop,
            args=(store,),
            daemon=True,
            name="kiwiki-history-collector",
        )
        _collector_thread.start()


def get_history_summary(range_name="1h"):
    if range_name not in {"1h", "6h", "24h", "7d"}:
        raise ValueError("Unsupported history range")
    try:
        store = HistoryStore()
        store.initialize()
        return store.summary(range_name)
    except Exception:
        return _empty_history(range_name, "hour" if range_name == "7d" else "minute")
