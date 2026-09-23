let language = localStorage.getItem("kiwiki-language") || "en";
let currentTheme = localStorage.getItem("kiwiki-theme") || "dark";
let currentStatusData = null;
let currentHistoryPayload = null;

const translations = {
    "INFRASTRUCTURE MONITOR": "MONITOR DE INFRAESTRUTURA",
    "LOCAL INSTANCE": "INSTÂNCIA LOCAL",
    "SERVER STATUS": "STATUS DO SERVIDOR",
    "HOSTNAME": "NOME DO HOST",
    "IP ADDRESS": "ENDEREÇO IP",
    "KIWIKI UPTIME": "UPTIME DO KIWIKI",
    "MEMORY": "MEMÓRIA",
    "STORAGE": "ARMAZENAMENTO",
    "BATTERY": "BATERIA",
    "THERMAL": "TEMPERATURA",
    "NETWORK": "REDE",
    "ACTIVE": "ATIVO",
    "Processor": "Processador",
    "Disk": "Disco",
    "Power": "Energia",
    "Temperature": "Temperatura",
    "Traffic": "Tráfego",
    "Current load": "Carga atual",
    "Battery sensor": "Sensor da bateria",
    "TELEMETRY": "TELEMETRIA",
    "Performance history": "Histórico de desempenho",
    "CPU usage": "Uso da CPU",
    "Processor load": "Carga do processador",
    "Memory usage": "Uso de memória",
    "RAM consumption": "Consumo de RAM",
    "Battery level": "Nível da bateria",
    "Charge percentage": "Percentual de carga",
    "Network throughput": "Tráfego de rede",
    "Traffic between samples": "Tráfego entre amostras",
    "Received": "Recebido",
    "Sent": "Enviado",
    "AVAILABILITY": "DISPONIBILIDADE",
    "Services": "Serviços",
    "ANDROID HOST": "HOST ANDROID",
    "Device": "Dispositivo",
    "HOST AGENT": "AGENTE DO HOST",
    "MANUFACTURER": "FABRICANTE",
    "MODEL": "MODELO",
    "LINK SPEED": "VELOCIDADE DO LINK",
    "OPERATING SYSTEM": "SISTEMA OPERACIONAL",
    "INTERVAL": "INTERVALO",
    "LOCAL SERVER DASHBOARD": "PAINEL DO SERVIDOR LOCAL",
    "5s status / 60s history": "status 5s / histórico 60s",
    "Loading history...": "Carregando histórico...",
    "Checking services...": "Verificando serviços...",
    "Light theme": "Tema claro",
    "Dark theme": "Tema escuro",
    "Change theme": "Mudar tema",
    "Change language": "Mudar idioma",
    "Not available on this device": "Não disponível neste dispositivo",
    "System operational": "Sistema operacional",
    "Dashboard unavailable": "Dashboard indisponível",
    "Unable to retrieve system metrics": "Não foi possível obter as métricas do sistema",
    "Connection error": "Erro de conexão",
    "Updated": "Atualizado",
    "All core metrics are being monitored": "Todas as métricas principais estão sendo monitoradas",
    "Kiwiki uptime": "Uptime do Kiwiki",
    "Health": "Saúde",
    "NORMAL": "NORMAL",
    "HIGH": "ALTO",
    "N/A": "N/D",
    "SENSOR OK": "SENSOR OK",
    "No historical data yet": "Ainda não há dados históricos",
    "History unavailable": "Histórico indisponível",
    "minute": "minuto",
    "hour": "hora",
    "samples": "amostras",
    "RUNNING": "EM EXECUÇÃO"
};

function t(value) {
    return language === "pt-BR" ? (translations[value] || value) : value;
}

function unavailableText() {
    return t("Not available on this device");
}

function translateStatus(value) {
    if (language !== "pt-BR") return value;
    return {
        Charging: "Carregando",
        Discharging: "Descarregando",
        "Not available": "Não disponível",
        Unknown: "Desconhecido",
        Online: "Online",
        Offline: "Offline"
    }[value] || value;
}

function markStaticText() {
    document.querySelectorAll("body *").forEach((element) => {
        if (element.children.length === 0) {
            const key = element.textContent.trim();
            if (translations[key]) element.dataset.i18nKey = key;
        }
    });
}

function translateStaticText() {
    document.querySelectorAll("[data-i18n-key]").forEach((element) => {
        element.textContent = t(element.dataset.i18nKey);
    });
}

function updatePreferenceButtons() {
    byId("theme-icon").textContent = currentTheme === "dark" ? "☼" : "☾";
    byId("theme-label").textContent = t(currentTheme === "dark" ? "Light theme" : "Dark theme");
    byId("language-toggle").textContent = language === "en" ? "PT-BR" : "EN";
    byId("theme-toggle").title = t("Change theme");
    byId("theme-toggle").setAttribute("aria-label", t("Change theme"));
    byId("language-toggle").title = t("Change language");
    byId("language-toggle").setAttribute("aria-label", t("Change language"));
}

function setTheme(theme) {
    currentTheme = theme === "light" ? "light" : "dark";
    localStorage.setItem("kiwiki-theme", currentTheme);
    document.body.dataset.theme = currentTheme;
    document.querySelector('meta[name="theme-color"]').content = currentTheme === "light" ? "#eef2f5" : "#0b0f14";
    updatePreferenceButtons();
}

function setLanguage(nextLanguage) {
    language = nextLanguage === "pt-BR" ? "pt-BR" : "en";
    localStorage.setItem("kiwiki-language", language);
    document.documentElement.lang = language === "pt-BR" ? "pt-BR" : "en";
    translateStaticText();
    updatePreferenceButtons();
    if (currentStatusData) renderStatus(currentStatusData);
    if (currentHistoryPayload) renderHistory(currentHistoryPayload);
}
let activeRange = "24h";

function byId(id) {
    return document.getElementById(id);
}

function formatBytes(bytes) {
    if (!Number.isFinite(bytes)) return unavailableText();
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
    return Number.isFinite(value) ? value.toLocaleString() : unavailableText();
}

function setProgress(id, value) {
    const element = byId(id);
    element.style.width = Number.isFinite(value) ? `${Math.max(0, Math.min(100, value))}%` : "0%";
}

function setMetric(valueId, barId, tagId, value) {
    const valid = Number.isFinite(value);
    byId(valueId).textContent = valid ? value.toFixed(1) : "-";
    setProgress(barId, value);
    byId(tagId).textContent = valid ? t(value >= 85 ? "HIGH" : "NORMAL") : t("N/A");
    byId(tagId).className = `tag ${valid && value >= 85 ? "warning" : valid ? "online" : ""}`;
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    }[character]));
}

function renderServices(services) {
    const list = byId("services-list");
    const online = services.filter((service) => service.status === "Online").length;
    byId("services-tag").textContent = `${online}/${services.length} ${t("ONLINE")}`;
    byId("services-tag").className = `tag ${online === services.length && services.length ? "online" : "warning"}`;
    list.innerHTML = services.map((service) => {
        const status = service.status || "Unknown";
        const className = String(status).toLowerCase();
        return `<div class="service-row"><span>${escapeHtml(service.name)}</span><span class="service-status ${className}"><i></i>${escapeHtml(translateStatus(status))}</span></div>`;
    }).join("");
}

function renderStatus(data) {
    const system = data.system || {};
    const memory = system.memory || {};
    const storage = system.storage || {};
    const battery = data.battery || {};
    const network = data.network || {};
    const device = data.device || {};
    const uptime = system.uptime || { seconds: null, formatted: unavailableText() };

    byId("server-status").textContent = t("System operational");
    byId("hostname").textContent = "Kiwiki Lab";
    byId("server-summary").textContent = `${t("All core metrics are being monitored")} / ${t("Kiwiki uptime")}: ${uptime.formatted}`;
    byId("ip-address").textContent = network.ip || unavailableText();
    byId("overview-uptime").textContent = uptime.formatted || unavailableText();
    byId("os-value").textContent = system.os || unavailableText();
    byId("python-value").textContent = system.python_version || unavailableText();
    byId("last-updated").textContent = `${t("Updated")} ${new Date().toLocaleTimeString()}`;

    setMetric("cpu-value", "cpu-bar", "cpu-tag", system.cpu_percent);
    setMetric("ram-value", "ram-bar", "ram-tag", memory.percent);
    setMetric("storage-value", "storage-bar", "storage-tag", storage.percent);
    setMetric("battery-value", "battery-bar", "battery-tag", battery.percent);

    byId("ram-detail").textContent = `${formatBytes(memory.used_bytes)} of ${formatBytes(memory.total_bytes)}`;
    byId("storage-detail").textContent = `${formatBytes(storage.used_bytes)} of ${formatBytes(storage.total_bytes)}`;
    byId("battery-detail").textContent = battery.available ? translateStatus(battery.status || "Unknown") : unavailableText();
    byId("battery-health").textContent = battery.available && battery.health ? `${t("Health")}: ${battery.health}` : unavailableText();
    byId("battery-unit").textContent = battery.available ? "%" : "";
    byId("temperature-value").textContent = Number.isFinite(battery.temperature_c) ? battery.temperature_c.toFixed(1) : unavailableText();
    byId("temperature-unit").textContent = Number.isFinite(battery.temperature_c) ? "°C" : "";
    byId("temperature-tag").textContent = Number.isFinite(battery.temperature_c) ? t("SENSOR OK") : t("N/A");
    byId("temperature-tag").className = `tag ${Number.isFinite(battery.temperature_c) ? "online" : ""}`;

    byId("sent-value").textContent = formatBytes(network.bytes_sent);
    byId("received-value").textContent = formatBytes(network.bytes_received);
    byId("packet-detail").textContent = `${formatCount(network.packets_sent)} ${t("Sent").toLowerCase()} • ${formatCount(network.packets_received)} ${t("Received").toLowerCase()}`;
    byId("link-speed").textContent = Number.isFinite(network.link_speed_mbps) ? `${network.link_speed_mbps} Mbps` : unavailableText();
    byId("rssi-value").textContent = Number.isFinite(network.rssi) ? `${network.rssi} dBm` : unavailableText();

    const uptimeAvailable = Number.isFinite(uptime.seconds);
    byId("uptime-tag").textContent = uptimeAvailable ? t("RUNNING") : t("N/A");
    byId("uptime-tag").className = `tag ${uptimeAvailable ? "online" : ""}`;
    byId("device-manufacturer").textContent = device.manufacturer || unavailableText();
    byId("device-model").textContent = device.model || unavailableText();
    byId("device-name").textContent = device.device || unavailableText();
    byId("android-version").textContent = device.android || unavailableText();
    renderServices(data.services || []);
}

function chartDimensions(svg) {
    const values = svg.getAttribute("viewBox").split(" ").map(Number);
    return { width: values[2], height: values[3], left: 8, right: 8, top: 10, bottom: 22 };
}

function drawLineChart(id, points, series, options = {}) {
    const svg = byId(id);
    const dimensions = chartDimensions(svg);
    const innerWidth = dimensions.width - dimensions.left - dimensions.right;
    const innerHeight = dimensions.height - dimensions.top - dimensions.bottom;
    const values = series.flatMap((item) => points.map((point) => point[item.key]).filter(Number.isFinite));
    svg.innerHTML = "";

    if (!values.length) {
        svg.innerHTML = `<text class="empty-label" x="${dimensions.width / 2}" y="${dimensions.height / 2}" text-anchor="middle">${t("No historical data yet")}</text>`;
        return;
    }

    let minimum = options.min ?? Math.min(...values);
    let maximum = options.max ?? Math.max(...values);
    if (minimum === maximum) {
        const padding = minimum === 0 ? 1 : Math.abs(minimum) * 0.08;
        minimum -= padding;
        maximum += padding;
    }

    const grid = [0, 1, 2, 3].map((index) => {
        const ratio = index / 3;
        const y = dimensions.top + innerHeight * ratio;
        const labelValue = maximum - (maximum - minimum) * ratio;
        return `<line class="grid-line" x1="${dimensions.left}" y1="${y}" x2="${dimensions.width - dimensions.right}" y2="${y}"></line><text class="axis-label" x="${dimensions.left}" y="${y - 4}">${labelValue.toFixed(0)}</text>`;
    }).join("");
    svg.innerHTML = grid;
    if (points.length) {
        const firstDate = new Date(points[0].timestamp * 1000);
        const lastDate = new Date(points[points.length - 1].timestamp * 1000);
        const dateOptions = points.length > 48 ? { month: "short", day: "numeric" } : { hour: "2-digit", minute: "2-digit" };
        svg.insertAdjacentHTML("beforeend", `<text class="axis-label" x="${dimensions.left}" y="${dimensions.height - 3}">${firstDate.toLocaleString([], dateOptions)}</text>`);
        svg.insertAdjacentHTML("beforeend", `<text class="axis-label" x="${dimensions.width - dimensions.right}" y="${dimensions.height - 3}" text-anchor="end">${lastDate.toLocaleString([], dateOptions)}</text>`);
    }

    series.forEach((item, seriesIndex) => {
        const coordinates = points.map((point, index) => {
            const value = point[item.key];
            if (!Number.isFinite(value)) return null;
            const x = dimensions.left + (points.length === 1 ? innerWidth / 2 : index / (points.length - 1) * innerWidth);
            const y = dimensions.top + (maximum - value) / (maximum - minimum) * innerHeight;
            return `${x.toFixed(2)},${y.toFixed(2)}`;
        }).filter(Boolean);
        if (!coordinates.length) return;
        const path = coordinates.map((coordinate, index) => `${index ? "L" : "M"}${coordinate}`).join(" ");
        const className = seriesIndex ? "chart-line secondary" : "chart-line";
        svg.insertAdjacentHTML("beforeend", `<path class="${className}" d="${path}" stroke="${item.color}"></path>`);
    });
}

function renderHistory(payload) {
    const points = payload.points || [];
    const rangeLabel = String(payload.range || activeRange).toUpperCase();
    const historySummary = points.length ? `${rangeLabel} / ${points.length} ${t(payload.granularity || "minute")} ${t("samples")}` : `${rangeLabel} / ${t("No historical data yet")}`;
    byId("history-meta").textContent = historySummary;
    drawLineChart("cpu-chart", points, [{ key: "cpu_percent", color: "#61c7d8" }], { min: 0, max: 100 });
    drawLineChart("ram-chart", points, [{ key: "memory_percent", color: "#a794d1" }], { min: 0, max: 100 });
    drawLineChart("temperature-chart", points, [{ key: "battery_temperature_c", color: "#d88686" }]);
    drawLineChart("battery-chart", points, [{ key: "battery_percent", color: "#75c99b" }], { min: 0, max: 100 });
    drawLineChart("network-chart", points, [
        { key: "network_rx_bytes", color: "#61c7d8" },
        { key: "network_tx_bytes", color: "#a794d1" }
    ], { min: 0 });
}

async function loadHistory(range = activeRange) {
    activeRange = range;
    try {
        const response = await fetch(`/api/history/summary?range=${encodeURIComponent(range)}`, { cache: "no-store" });
        if (!response.ok) throw new Error("History request failed");
        currentHistoryPayload = await response.json();
        renderHistory(currentHistoryPayload);
    } catch (error) {
        currentHistoryPayload = { range, points: [], granularity: range === "7d" ? "hour" : "minute" };
        renderHistory(currentHistoryPayload);
        byId("history-meta").textContent = t("History unavailable");
    }
}

async function updateDashboard() {
    try {
        const response = await fetch("/api/status", { cache: "no-store" });
        if (!response.ok) throw new Error("Status request failed");
        currentStatusData = await response.json();
        renderStatus(currentStatusData);
    } catch (error) {
        byId("server-status").textContent = t("Dashboard unavailable");
        byId("server-summary").textContent = t("Unable to retrieve system metrics");
        byId("last-updated").textContent = t("Connection error");
    }
}

byId("theme-toggle").addEventListener("click", () => setTheme(currentTheme === "dark" ? "light" : "dark"));
byId("language-toggle").addEventListener("click", () => setLanguage(language === "en" ? "pt-BR" : "en"));
markStaticText();
setTheme(currentTheme);
setLanguage(language);

document.querySelectorAll(".range-button").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".range-button").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        loadHistory(button.dataset.range);
    });
});

updateDashboard();
loadHistory();
setInterval(updateDashboard, 5000);
setInterval(() => loadHistory(activeRange), 60000);
