// --- Utilidades ---
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const C = { lb: css("--lb"), gr: css("--gr"), jv: css("--jv"), activo: css("--activo"),
            pasivo: css("--pasivo"), neto: css("--neto"), grid: css("--grid"), muted: css("--muted") };
const EMPRESAS = [["lb", "LB"], ["gr", "GR"], ["jv", "JV"]];

const fmt = (v, d = 2) => (v === null || v === undefined || isNaN(v)) ? "—"
    : Number(v).toLocaleString("es-VE", { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtCorto = (v) => Math.abs(v) >= 1e6 ? fmt(v / 1e6, 1) + " M" : Math.abs(v) >= 1e3 ? fmt(v / 1e3, 1) + " k" : fmt(v, 0);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const hoy = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };
const restarDias = (f, n) => { const d = new Date(f + "T12:00:00"); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); };
const fechaCorta = (f) => f.slice(8, 10) + "/" + f.slice(5, 7);
const ORIGEN_CLASE = { ERP: "text-success", WS: "text-primary", MANUAL: "text-warning", "SALDO INICIAL": "text-secondary" };

let datos = null;
let conceptoSel = "inventario";
const charts = {};

Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
Chart.defaults.font.size = 12;
Chart.defaults.color = C.muted;

function opcionesBase(apilado) {
    return {
        responsive: true, maintainAspectRatio: false, animation: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
            legend: { display: false },  // leyenda en HTML, encima del gráfico
            tooltip: {
                backgroundColor: "#fff", titleColor: "#212529", bodyColor: "#212529",
                borderColor: "#dee2e6", borderWidth: 1, padding: 10, boxPadding: 4, usePointStyle: true,
                callbacks: {
                    label: (ctx) => {
                        const extra = ctx.dataset._arrastrado?.[ctx.dataIndex] ? " (sin registro, último valor)" : "";
                        return ` ${ctx.dataset.label}: ${fmt(ctx.parsed.y)}${extra}`;
                    },
                    footer: apilado ? (items) => "Total: " + fmt(items.reduce((s, i) => s + i.parsed.y, 0)) : undefined,
                },
            },
        },
        scales: {
            x: { stacked: apilado, grid: { display: false }, border: { color: C.grid } },
            y: { stacked: apilado, grid: { color: C.grid }, border: { display: false },
                 ticks: { callback: (v) => fmtCorto(v), maxTicksLimit: 6 } },
        },
    };
}

function dibujar(id, config) {
    charts[id]?.destroy();
    charts[id] = new Chart(document.getElementById(id), config);
}

const linea = (label, data, color, extra = {}) => ({
    label, data, borderColor: color, backgroundColor: color, borderWidth: 2, tension: 0.25,
    pointRadius: data.length > 40 ? 0 : 4, pointHoverRadius: 6, pointBorderColor: "#fff", pointBorderWidth: 2,
    spanGaps: true, ...extra,
});

// --- Carga ---
// En Vercel no hay API: window.FUENTE_ESTATICA apunta a un JSON con todo el histórico
// y el rango de fechas se recorta aquí (los valores arrastrados ya vienen calculados).
let datosCompletos = null;

function recortar(d, desde, hasta) {
    const idx = d.fechas.map((f, i) => (f >= desde && f <= hasta ? i : -1)).filter((i) => i >= 0);
    const tomar = (arr) => idx.map((i) => arr[i]);
    const tomarSeries = (o) => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, Array.isArray(v) ? tomar(v) : v]));
    return {
        ...d, desde, hasta, fechas: tomar(d.fechas), tasa_bcv: tomar(d.tasa_bcv),
        conceptos: d.conceptos.map(tomarSeries),
        totales: Object.fromEntries(Object.entries(d.totales).map(([k, v]) => [k, tomarSeries(v)])),
    };
}

async function cargar() {
    const desde = document.getElementById("fDesde").value;
    const hasta = document.getElementById("fHasta").value;
    if (window.FUENTE_ESTATICA) {
        if (!datosCompletos) {
            datosCompletos = await (await fetch(window.FUENTE_ESTATICA, { cache: "no-store" })).json();
            const g = document.getElementById("infoGenerado");
            if (g) g.textContent = "Datos actualizados: " + (datosCompletos.generado || "").replace("T", " ").slice(0, 16);
        }
        datos = recortar(datosCompletos, desde, hasta);
    } else {
        const r = await fetch(`/api/consolidado?desde=${desde}&hasta=${hasta}`);
        if (r.status === 401) { location.href = "/login"; return; }
        datos = await r.json();
    }

    const hay = datos.fechas.length > 0;
    document.getElementById("sinDatos").classList.toggle("d-none", hay);
    document.getElementById("contenido").classList.toggle("d-none", !hay);
    document.getElementById("infoDias").textContent = hay
        ? `${datos.fechas.length} día(s) guardado(s): ${datos.fechas[0]} → ${datos.fechas.at(-1)}` : "";
    if (!hay) return;

    renderKpis();
    renderInventario();
    renderTotales();
    renderTabla();
    renderDetalle(conceptoSel);
}

function rango(dias) {
    const h = hoy();
    document.getElementById("fHasta").value = h;
    document.getElementById("fDesde").value = restarDias(h, dias);
    cargar();
}

// --- Inventario general = inventario en almacén + inventario en tránsito ---
function inventarioGeneral() {
    const inv = datos.conceptos.filter((c) => c.key === "inventario" || c.key === "inventario_transito");
    const out = {};
    for (const k of ["lb", "gr", "jv", "total"]) {
        out[k] = datos.fechas.map((_, i) => inv.reduce((s, c) => s + (c[k][i] || 0), 0));
    }
    return out;
}

// --- KPIs con variación contra el día guardado anterior ---
function deltaHTML(serie, subirEsBueno) {
    const n = serie.length;
    if (n < 2) return '<span class="neutro">Sin día anterior para comparar</span>';
    const d = serie[n - 1] - serie[n - 2];
    const pct = serie[n - 2] ? (d / Math.abs(serie[n - 2])) * 100 : null;
    if (Math.abs(d) < 0.005) return '<span class="neutro"><i class="bi bi-dash"></i> Sin cambio</span>';
    const bueno = (d > 0) === subirEsBueno;
    return `<span class="${bueno ? "bueno" : "malo"}"><i class="bi bi-arrow-${d > 0 ? "up" : "down"}-right"></i>
        ${d > 0 ? "+" : ""}${fmt(d)}${pct !== null ? ` (${pct > 0 ? "+" : ""}${fmt(pct, 1)} %)` : ""}</span>
        <span class="neutro">vs ${fechaCorta(datos.fechas[n - 2])}</span>`;
}

function renderKpis() {
    const inv = inventarioGeneral();
    const t = datos.totales;
    const items = [
        ["Inventario general (almacén + tránsito)", inv.total, true, "bi-box-seam"],
        ["Total activo", t.activo.total, true, "bi-arrow-up-circle"],
        ["Total pasivo", t.pasivo.total, false, "bi-arrow-down-circle"],
        ["Neto (activo − pasivo)", t.neto.total, true, "bi-check-circle"],
    ];
    const ult = datos.fechas.length - 1;
    document.getElementById("kpis").innerHTML = items.map(([titulo, serie, bueno, icono]) => `
        <div class="col-md-6 col-xl-3">
            <div class="card kpi h-100"><div class="card-body py-2">
                <small><i class="bi ${icono}"></i> ${titulo} · ${fechaCorta(datos.fechas[ult])}</small>
                <div class="valor">${fmt(serie[ult])}</div>
                <div class="delta">${deltaHTML(serie, bueno)}</div>
            </div></div>
        </div>`).join("");
}

// --- Gráficos ---
function renderInventario() {
    const inv = inventarioGeneral();
    dibujar("chInventario", {
        type: "bar",
        data: {
            labels: datos.fechas.map(fechaCorta),
            datasets: EMPRESAS.map(([k, label], i) => ({
                label, data: inv[k], backgroundColor: C[k],
                borderColor: "#fff", borderWidth: { top: 2 }, borderSkipped: false,
                borderRadius: i === EMPRESAS.length - 1 ? { topLeft: 4, topRight: 4 } : 0,
                maxBarThickness: 48,
            })),
        },
        options: opcionesBase(true),
    });
}

function renderTotales() {
    const t = datos.totales;
    dibujar("chTotales", {
        type: "line",
        data: {
            labels: datos.fechas.map(fechaCorta),
            datasets: [
                linea("Total activo", t.activo.total, C.activo),
                linea("Total pasivo", t.pasivo.total, C.pasivo),
                linea("Neto", t.neto.total, C.neto, { borderDash: [6, 4], borderWidth: 2.5 }),
            ],
        },
        options: opcionesBase(false),
    });
}

function renderDetalle(key) {
    const c = datos.conceptos.find((x) => x.key === key) || datos.conceptos[0];
    conceptoSel = c.key;
    document.getElementById("tituloDetalle").textContent = c.concepto;
    dibujar("chDetalle", {
        type: "line",
        data: {
            labels: datos.fechas.map(fechaCorta),
            datasets: [
                ...EMPRESAS.map(([k, label]) => linea(label, c[k], C[k], {
                    _arrastrado: c.arrastrado,
                    pointBackgroundColor: c[k].map((_, i) => (c.arrastrado[i] ? "#fff" : C[k])),
                    pointBorderColor: c[k].map((_, i) => (c.arrastrado[i] ? C[k] : "#fff")),
                })),
                linea("Consolidado", c.total, C.neto, { borderDash: [6, 4], borderWidth: 2.5, _arrastrado: c.arrastrado }),
            ],
        },
        options: opcionesBase(false),
    });
    const nArr = c.arrastrado.filter(Boolean).length;
    document.getElementById("notaDetalle").textContent = nArr
        ? `Puntos huecos: ${nArr} día(s) sin registro de este concepto; se muestra el último valor conocido.` : "";
    document.querySelectorAll(".fila-concepto").forEach((tr) => tr.classList.toggle("activa", tr.dataset.key === c.key));
}

// --- Tabla con sparkline por concepto ---
function sparkline(serie) {
    const w = 110, h = 26, p = 3;
    const vals = serie.map((v) => v ?? null);
    const nums = vals.filter((v) => v !== null);
    if (nums.length < 2) return '<span class="text-muted small">—</span>';
    const min = Math.min(...nums), max = Math.max(...nums), span = max - min || 1;
    const x = (i) => p + (i * (w - 2 * p)) / (vals.length - 1);
    const y = (v) => h - p - ((v - min) / span) * (h - 2 * p);
    const pts = vals.map((v, i) => (v === null ? null : `${x(i).toFixed(1)},${y(v).toFixed(1)}`)).filter(Boolean);
    const last = vals.length - 1;
    return `<svg class="spark" width="${w}" height="${h}" role="img" aria-label="Tendencia de ${fmt(nums[0])} a ${fmt(nums.at(-1))}">
        <title>${datos.fechas.map((f, i) => `${fechaCorta(f)}: ${fmt(vals[i])}`).join("\n")}</title>
        <polyline points="${pts.join(" ")}" fill="none" stroke="${C.muted}" stroke-width="1.5" stroke-linejoin="round"/>
        <circle cx="${x(last)}" cy="${y(vals[last])}" r="3" fill="${C.neto}"/>
    </svg>`;
}

function renderTabla() {
    const n = datos.fechas.length;
    let html = "";
    for (const grupo of ["activo", "pasivo"]) {
        html += `<tr class="table-${grupo === "activo" ? "primary" : "danger"}"><td colspan="6" class="fw-semibold small">${grupo.toUpperCase()}</td></tr>`;
        for (const c of datos.conceptos.filter((x) => x.grupo === grupo)) {
            const ult = c.total[n - 1], ant = n > 1 ? c.total[n - 2] : null;
            const d = ult !== null && ant !== null ? ult - ant : null;
            const pct = d !== null && ant ? (d / Math.abs(ant)) * 100 : null;
            // En el pasivo, que suba es desfavorable
            const clase = d === null || Math.abs(d) < 0.005 ? "neutro" : ((d > 0) === (grupo === "activo") ? "bueno" : "malo");
            html += `<tr class="fila-concepto" data-key="${esc(c.key)}" onclick="renderDetalle('${esc(c.key)}')">
                <td>${esc(c.concepto)}${c.arrastrado[n - 1] ? ' <i class="bi bi-clock-history text-muted" title="Sin registro en el último día: se muestra el último valor conocido"></i>' : ""}</td>
                <td class="text-center small fw-semibold ${ORIGEN_CLASE[c.origen] || ""}">${esc(c.origen || "-")}</td>
                <td class="valor-num">${fmt(ult)}</td>
                <td class="valor-num ${clase}">${d === null ? "—" : (d > 0 ? "+" : "") + fmt(d)}</td>
                <td class="valor-num ${clase}">${pct === null ? "—" : (pct > 0 ? "+" : "") + fmt(pct, 1) + " %"}</td>
                <td class="text-center">${sparkline(c.total)}</td>
            </tr>`;
        }
    }
    document.getElementById("tbodyConceptos").innerHTML = html;
}

// --- Init ---
window.addEventListener("DOMContentLoaded", () => {
    document.getElementById("fDesde").addEventListener("change", cargar);
    document.getElementById("fHasta").addEventListener("change", cargar);
    rango(90);
});
