const unavailable = "Not available on this device";

function byId(id) {
    return document.getElementById(id);
}

function formatBytes(bytes) {
    if (!Number.isFinite(bytes)) return unavailable;
    const units = ["B", "KB", "MB", "GB", "TB"];
    let value = bytes;
    let index = 0;
    while (value >= 1024 && index < units.length - 1) {
        value /= 1024;
        index += 1;
    }
    return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatCount(value) {
    return Number.isFinite(value) ? value.toLocaleString() : unavailable;
}

function setProgress(id, value) {
    const element = byId(id);
    element.style.width = Number.isFinite(value) ? `${Math.max(0, Math.min(100, value))}%` : "0%";
}

function setMetric(valueId, barId, tagId, value) {
    const valid = Number.isFinite(value);
    byId(valueId).textContent = valid ? value.toFixed(1) : "—";
    setProgress(barId, value);
    byId(tagId).textContent = valid ? (value >= 85 ? "HIGH" : "NORMAL") : "N/A";
    byId(tagId).className = `tag ${valid && value >= 85 ? "warning" : valid ? "online" : ""}`;
}

function renderServices(services) {
    const list = byId("services-list");
    const online = services.filter((service) => service.status === "Online").length;
    byId("services-tag").textContent = `${online}/${services.length} ONLINE`;
    byId("services-tag").className = `tag ${online === services.length ? "online" : "warning"}`;
    list.innerHTML = services.map((service) => {
        const className = service.status.toLowerCase();
        return `<div class="service-row"><span>${service.name}</span><span class="service-status ${className}"><i></i>${service.status}</span></div>`;
    }).join("");
}

function renderStatus(data) {
    const system = data.system;
    const battery = data.battery;
    const network = data.network;
    const device = data.device || {};
    const uptime = system.uptime;

    byId("server-status").textContent = "System operational";
    byId("server-summary").textContent = `All core metrics are being monitored • ${uptime.formatted} uptime`;
    byId("hostname").textContent = "Kiwiki Lab";
    byId("ip-address").textContent = network.ip || unavailable;
    byId("os-value").textContent = system.os || unavailable;
    byId("python-value").textContent = system.python_version || unavailable;
    byId("last-updated").textContent = `Updated ${new Date().toLocaleTimeString()}`;

    setMetric("cpu-value", "cpu-bar", "cpu-tag", system.cpu_percent);
    setMetric("ram-value", "ram-bar", "ram-tag", system.memory.percent);
    setMetric("storage-value", "storage-bar", "storage-tag", system.storage.percent);
    setMetric("battery-value", "battery-bar", "battery-tag", battery.percent);

    byId("ram-detail").textContent = `${formatBytes(system.memory.used_bytes)} of ${formatBytes(system.memory.total_bytes)}`;
    byId("storage-detail").textContent = `${formatBytes(system.storage.used_bytes)} of ${formatBytes(system.storage.total_bytes)}`;
    byId("battery-detail").textContent = battery.available ? battery.status : unavailable;
    byId("battery-health").textContent = battery.available && battery.health ? `Health: ${battery.health}` : unavailable;
    byId("battery-unit").textContent = battery.available ? "%" : "";
    byId("temperature-value").textContent = Number.isFinite(battery.temperature_c) ? battery.temperature_c.toFixed(1) : unavailable;
    byId("temperature-unit").textContent = Number.isFinite(battery.temperature_c) ? "°C" : "";
    byId("temperature-tag").textContent = Number.isFinite(battery.temperature_c) ? "SENSOR OK" : "N/A";
    byId("temperature-tag").className = `tag ${Number.isFinite(battery.temperature_c) ? "online" : ""}`;

    byId("sent-value").textContent = formatBytes(network.bytes_sent);
    byId("received-value").textContent = formatBytes(network.bytes_received);
    byId("link-speed").textContent = Number.isFinite(network.link_speed_mbps) ? `${network.link_speed_mbps} Mbps` : unavailable;
    byId("rssi-value").textContent = Number.isFinite(network.rssi) ? `${network.rssi} dBm` : unavailable;
    byId("packet-detail").textContent = `${formatCount(network.packets_sent)} sent • ${formatCount(network.packets_received)} received`;
    byId("uptime-value").textContent = uptime.formatted;
    byId("device-manufacturer").textContent = device.manufacturer || unavailable;
    byId("device-model").textContent = device.model || unavailable;
    byId("device-name").textContent = device.device || unavailable;
    byId("android-version").textContent = device.android || unavailable;
    renderServices(data.services);
}

async function updateDashboard() {
    try {
        const response = await fetch("/api/status", { cache: "no-store" });
        if (!response.ok) throw new Error("Status request failed");
        renderStatus(await response.json());
    } catch (error) {
        byId("server-status").textContent = "Dashboard unavailable";
        byId("server-summary").textContent = "Unable to retrieve system metrics";
        byId("last-updated").textContent = "Connection error";
    }
}

updateDashboard();
setInterval(updateDashboard, 5000);
