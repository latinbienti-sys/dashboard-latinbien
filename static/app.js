// --- Utilidades ---
const fmt = (v, dec) => {
    if (v === null || v === undefined || v === "") return "0";
    const n = Number(v);
    if (isNaN(n)) return String(v);
    const d = dec !== undefined ? dec : 2;
    return n.toLocaleString("es-VE", { minimumFractionDigits: d, maximumFractionDigits: d });
};

// Fecha local (no UTC: en Venezuela después de las 8 pm ya sería "mañana")
const today = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };

function addDias(fecha, delta) {
    const d = new Date(fecha + "T12:00:00");
    d.setDate(d.getDate() + delta);
    return d.toISOString().slice(0, 10);
}

const origenClass = (origen) => {
    const o = (origen || "").toUpperCase();
    if (o.includes("ERP")) return "origen-erp";
    if (o.includes("WS")) return "origen-ws";
    if (o.includes("MANUAL")) return "origen-manual";
    if (o.includes("SALDO")) return "origen-saldo";
    return "";
};

function mostrarToast(msg) {
    document.getElementById("toastMsg").textContent = msg;
    new bootstrap.Toast(document.getElementById("toast")).show();
}

// --- Estado global ---
let datosGlobal = null;
let fechaActual = today();
let modalRegistro = null;
let modalReporte = null;
let reporteActual = null;

// --- Render de tablas ---
function filaHTML(f, leible) {
    const boton = leible
        ? '<span class="text-muted">—</span>'
        : `<button class="btn btn-outline-primary btn-edit"
            onclick="abrirRegistro(${f.fila}, '${f.concepto.replace(/'/g, "\\'")}', ${f.lb ?? 0}, ${f.gr ?? 0}, ${f.jv ?? 0}, '${f.origen}')">
            <i class="bi bi-pencil"></i>
        </button>`;
    return `<tr>
        <td>${f.concepto}</td>
        <td class="valor-num">${fmt(f.lb)}</td>
        <td class="valor-num">${fmt(f.gr)}</td>
        <td class="valor-num">${fmt(f.jv)}</td>
        <td class="text-center"><span class="${origenClass(f.origen)}" title="${f.usuario ? "Registrado por " + f.usuario + " · " + (f.registrado || "").replace("T", " ").slice(0, 16) : ""}">${f.origen || "-"}</span>${f.usuario ? ' <i class="bi bi-person-check text-muted small"></i>' : ""}</td>
        <td class="text-center">${boton}</td>
    </tr>`;
}

async function cargarDatos() {
    try {
        const r = await fetch("/api/datos?fecha=" + fechaActual);
        if (r.status === 401) { location.href = "/login"; return; }
        const data = await r.json();
        if (data.error) { mostrarToast("Error: " + data.error); return; }
        datosGlobal = data;

        document.getElementById("inputFecha").value = fechaActual;
        document.getElementById("infoFecha").textContent = data.info.fecha_corte || "-";
        document.getElementById("infoBcv").textContent = fmt(data.info.tasa_bcv);
        document.getElementById("infoBinance").textContent = fmt(data.info.tasa_binance);
        document.getElementById("infoBrecha").textContent =
            (data.info.brecha != null ? Number(data.info.brecha).toFixed(2) + " %" : "-");

        const badge = document.getElementById("badgeDia");
        if (data.guardado) {
            badge.className = "badge text-bg-success";
            badge.textContent = "Día guardado";
        } else {
            badge.className = "badge text-bg-secondary";
            badge.textContent = "No guardado";
        }

        const alerta = document.getElementById("alertaPendiente");
        const pend = data.captura_pendiente || [];
        alerta.classList.toggle("d-none", !pend.length);
        alerta.innerHTML = pend.length
            ? `<i class="bi bi-exclamation-triangle"></i> Datos WS sin registrar para ${fechaActual}: <strong>${pend.join(", ")}</strong>`
            : "";

        document.getElementById("tbodyActivo").innerHTML = data.activo.map((f) => filaHTML(f, false)).join("");
        document.getElementById("tbodyPasivo").innerHTML = data.pasivo.map((f) => filaHTML(f, false)).join("");

        const ta = data.totales.total_activo;
        const tp = data.totales.total_pasivo;
        const an = data.totales.activo_menos_pasivo;
        const bcv = Number(data.info.tasa_bcv) || 0;
        document.getElementById("resActivo").textContent = `LB ${fmt(ta.lb)} · GR ${fmt(ta.gr)} · JV ${fmt(ta.jv)}`;
        document.getElementById("resPasivo").textContent = `LB ${fmt(tp.lb)} · GR ${fmt(tp.gr)} · JV ${fmt(tp.jv)}`;
        document.getElementById("resNeto").textContent = `LB ${fmt(an.lb)} · GR ${fmt(an.gr)} · JV ${fmt(an.jv)}`;
        const totalBs = (ta.lb + ta.gr + ta.jv) * bcv;
        document.getElementById("resBs").textContent = fmt(totalBs, 0);
        document.getElementById("resBs").title = `(Total activo × BCV ${fmt(bcv)})`;

        cargarHistorico();
    } catch (e) {
        mostrarToast("No se pudo cargar: " + e.message);
    }
}

// --- Navegación de días ---
function irFecha(fecha) {
    if (!fecha) return;
    fechaActual = fecha;
    cargarDatos();
}

function moverDia(delta) {
    irFecha(addDias(fechaActual, delta));
}

// --- Tasas automáticas ---
async function cargarTasas(notificar) {
    const spin = document.getElementById("spinBcv");
    if (spin) spin.className = "bi bi-arrow-repeat small spinner-border spinner-border-sm";
    try {
        const r = await fetch("/api/tasas");
        const t = await r.json();
        if (t.error) {
            mostrarToast("No se pudo obtener tasas: " + t.error);
        } else {
            document.getElementById("infoBcv").textContent = fmt(t.tasa_bcv);
            document.getElementById("infoBinance").textContent = fmt(t.tasa_binance);
            document.getElementById("infoBrecha").textContent =
                (t.brecha != null ? Number(t.brecha).toFixed(2) + " %" : "-");
            if (notificar) mostrarToast(`Tasas actualizadas: BCV ${fmt(t.tasa_bcv)} · Binance ${fmt(t.tasa_binance)} · Brecha ${fmt(t.brecha, 2)}%`);
        }
    } catch (e) {
        mostrarToast("Error obteniendo tasas: " + e.message);
    } finally {
        if (spin) spin.className = "bi bi-arrow-repeat small";
    }
}

// --- Guardar día completo ---
async function guardarDia() {
    if (!datosGlobal) return;
    const valores = [...datosGlobal.activo, ...datosGlobal.pasivo].map((f) => ({
        fila: f.fila, key: f.key, concepto: f.concepto,
        lb: Number(f.lb) || 0, gr: Number(f.gr) || 0, jv: Number(f.jv) || 0, origen: f.origen,
    }));
    const tasas = {
        tasa_bcv: Number(datosGlobal.info.tasa_bcv) || null,
        tasa_binance: Number(datosGlobal.info.tasa_binance) || null,
        brecha: Number(datosGlobal.info.brecha) || null,
    };
    const r = await fetch("/api/guardar_dia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fecha: fechaActual, valores, tasas }),
    });
    const data = await r.json();
    if (data.ok) {
        mostrarToast(data.msg);
        cargarDatos();
    } else {
        mostrarToast("Error: " + (data.error || "desconocido"));
    }
}

// --- Popup registro ---
function abrirRegistro(fila, concepto, lb, gr, jv, origen) {
    document.getElementById("mFila").value = fila;
    document.getElementById("mConcepto").value = concepto;
    document.getElementById("mLB").value = lb;
    document.getElementById("mGR").value = gr;
    document.getElementById("mJV").value = jv;
    document.getElementById("mOrigen").value = origen || "MANUAL";
    document.getElementById("erpStatus").textContent = "";
    modalRegistro.show();
}

async function guardarRegistro() {
    const payload = {
        fecha: fechaActual,
        fila: document.getElementById("mFila").value,
        origen: document.getElementById("mOrigen").value,
        lb: document.getElementById("mLB").value,
        gr: document.getElementById("mGR").value,
        jv: document.getElementById("mJV").value,
    };
    const r = await fetch("/api/guardar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    const data = await r.json();
    if (data.ok) {
        modalRegistro.hide();
        mostrarToast("Guardado correctamente");
        cargarDatos();
    } else {
        mostrarToast("Error: " + (data.error || "desconocido"));
    }
}

async function consultarERP() {
    const fila = document.getElementById("mFila").value;
    let key = null;
    if (datosGlobal) {
        const todos = [...datosGlobal.activo, ...datosGlobal.pasivo];
        const encontrado = todos.find((x) => String(x.fila) === String(fila));
        if (encontrado) key = encontrado.key;
    }
    const status = document.getElementById("erpStatus");
    status.textContent = "Consultando ERP (Odoo)...";
    const r = await fetch("/api/consultar_erp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, fecha: fechaActual }),
    });
    const data = await r.json();
    if (data.ok && (data.lb !== undefined || data.gr !== undefined || data.jv !== undefined)) {
        document.getElementById("mLB").value = data.lb ?? 0;
        document.getElementById("mGR").value = data.gr ?? 0;
        document.getElementById("mJV").value = data.jv ?? 0;
        document.getElementById("mOrigen").value = "ERP";
        status.textContent = `Valores de ERP cargados (${(data.fuente || key)}, ${data.indicador || ""})`;
    } else if (data.ok) {
        status.textContent = "Consulta OK pero sin valores para este concepto";
    } else {
        status.textContent = "Error: " + (data.error || "sin datos");
    }
}

// --- Histórico ---
async function cargarHistorico() {
    try {
        const r = await fetch("/api/historico");
        const dias = await r.json();
        const tbody = document.getElementById("tbodyHistorico");
        if (!dias.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Aún no hay días guardados.</td></tr>';
            return;
        }
        tbody.innerHTML = dias.map((d) => {
            const ta = d.total_activo || { lb: 0, gr: 0, jv: 0 };
            const tp = d.total_pasivo || { lb: 0, gr: 0, jv: 0 };
            const neto = {
                lb: (Number(ta.lb) || 0) - (Number(tp.lb) || 0),
                gr: (Number(ta.gr) || 0) - (Number(tp.gr) || 0),
                jv: (Number(ta.jv) || 0) - (Number(tp.jv) || 0),
            };
            const activa = d.fecha === fechaActual ? " hist-actual" : "";
            const sumTot = Number(ta.lb) + Number(ta.gr) + Number(ta.jv) || 0;
            return `<tr class="dak${activa}" onclick="irFecha('${d.fecha}')">
                <td><strong>${d.fecha}</strong></td>
                <td class="valor-num">${fmt(d.tasa_bcv)}</td>
                <td class="valor-num">${fmt(d.tasa_binance)}</td>
                <td class="valor-num">${d.brecha != null ? Number(d.brecha).toFixed(2) : "-"}</td>
                <td class="valor-num">${fmt(sumTot)}</td>
                <td class="valor-num">${fmt((Number(tp.lb) + Number(tp.gr) + Number(tp.jv)) || 0)}</td>
                <td class="valor-num">${fmt(neto.lb + neto.gr + neto.jv)}</td>
                <td class="text-center"><small class="text-muted">${(d.actualizado || "").slice(0, 16)}</small></td>
            </tr>`;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

// --- Reporte ---
async function verReporte() {
    try {
        const r = await fetch("/api/reporte?fecha=" + fechaActual);
        const rep = await r.json();
        reporteActual = rep;
        document.getElementById("reporteBody").innerHTML = renderReporte(rep);
        modalReporte.show();
    } catch (e) {
        mostrarToast("Error generando reporte: " + e.message);
    }
}

function renderReporte(rep) {
    if (rep.error) return `<div class="alert alert-danger">${rep.error}</div>`;
    const t = rep.tasas || {};
    const tot = rep.totales || {};
    const v = rep.variacion;
    const filaTotal = (r) => `LB ${fmt(r.lb)} · GR ${fmt(r.gr)} · JV ${fmt(r.jv)}`;

    let html = "";
    html += `<div class="row mb-3">
        <div class="col-md-4">
            <div class="card border-primary"><div class="card-body py-2">
                <small class="text-muted">Fecha</small>
                <h5>${rep.fecha}</h5>
                <span class="badge ${rep.guardado ? "text-bg-success" : "text-bg-secondary"}">${rep.guardado ? "Consolidado" : "Sin consolidar"}</span>
            </div></div>
        </div>
        <div class="col-md-3">
            <div class="card border-success"><div class="card-body py-2">
                <small class="text-muted">Tasa BCV</small><h5>${fmt(t.tasa_bcv)}</h5>
            </div></div>
        </div>
        <div class="col-md-3">
            <div class="card border-info"><div class="card-body py-2">
                <small class="text-muted">Tasa Binance</small><h5>${fmt(t.tasa_binance)}</h5>
            </div></div>
        </div>
        <div class="col-md-2">
            <div class="card border-danger"><div class="card-body py-2">
                <small class="text-muted">Brecha %</small><h5>${t.brecha != null ? Number(t.brecha).toFixed(2) : "-"}</h5>
            </div></div>
        </div>
    </div>`;

    html += `<table class="table table-bordered table-sm">
        <thead class="table-dark">
            <tr><th>Resumen</th><th class="text-end">LB</th><th class="text-end">GR</th><th class="text-end">JV</th></tr>
        </thead>
        <tbody>
            <tr><td>TOTAL ACTIVO</td><td class="valor-num">${fmt(tot.total_activo.lb)}</td><td class="valor-num">${fmt(tot.total_activo.gr)}</td><td class="valor-num">${fmt(tot.total_activo.jv)}</td></tr>
            <tr><td>TOTAL PASIVO</td><td class="valor-num">${fmt(tot.total_pasivo.lb)}</td><td class="valor-num">${fmt(tot.total_pasivo.gr)}</td><td class="valor-num">${fmt(tot.total_pasivo.jv)}</td></tr>
            <tr class="table-success"><td><strong>ACTIVO - PASIVO</strong></td><td class="valor-num"><strong>${fmt(tot.activo_menos_pasivo.lb)}</strong></td><td class="valor-num"><strong>${fmt(tot.activo_menos_pasivo.gr)}</strong></td><td class="valor-num"><strong>${fmt(tot.activo_menos_pasivo.jv)}</strong></td></tr>
        </tbody>
    </table>`;

    if (v) {
        html += `<div class="alert alert-warning">
            <strong>Variación vs ${v.fecha}:</strong><br>
            Total activo: ${filaTotal(v.total_activo)}<br>
            Total pasivo: ${filaTotal(v.total_pasivo)}<br>
            Neto (Activo - Pasivo): ${filaTotal(v.activo_menos_pasivo)}
        </div>`;
    } else {
        html += `<div class="alert alert-secondary">Sin día anterior registrado para comparar variación.</div>`;
    }

    html += `<h6 class="mt-3">Detalle por concepto</h6>
    <table class="table table-sm table-striped">
        <thead class="table-light">
            <tr><th>Concepto</th><th class="text-end">LB</th><th class="text-end">GR</th><th class="text-end">JV</th><th class="text-center">Origen</th></tr>
        </thead>
        <tbody>`;
    (rep.detalle || []).forEach((r) => {
        html += `<tr>
            <td>${r.concepto || r.key}</td>
            <td class="valor-num">${fmt(r.lb)}</td>
            <td class="valor-num">${fmt(r.gr)}</td>
            <td class="valor-num">${fmt(r.jv)}</td>
            <td class="text-center"><span class="${origenClass(r.origen)}">${r.origen || "-"}</span></td>
        </tr>`;
    });
    html += `</tbody></table>`;
    return html;
}

function descargarReporte() {
    if (!reporteActual) return;
    const blob = new Blob([JSON.stringify(reporteActual, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `reporte_${reporteActual.fecha}.json`;
    a.click();
}

// --- Backup ---
async function crearBackup() {
    const r = await fetch("/api/backup");
    const data = await r.json();
    mostrarToast(data.ok ? "Backup creado: " + data.archivo : "Error: " + data.error);
}

// --- Init ---
window.addEventListener("DOMContentLoaded", () => {
    modalRegistro = new bootstrap.Modal(document.getElementById("modalRegistro"));
    modalReporte = new bootstrap.Modal(document.getElementById("modalReporte"));
    cargarDatos();
    // Refrescar tasas automáticamente cada 10 minutos
    cargarTasas(false);
    setInterval(() => cargarTasas(false), 10 * 60 * 1000);
});