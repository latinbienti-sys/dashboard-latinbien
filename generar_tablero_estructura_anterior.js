#!/usr/bin/env node
// Genera reporte/tablero.html desde datos/reporte_ventas_<hoy>.json
// Standalone: sin CDN ni dependencias, gráficos en CSS puro (estilo inventariohonda).
'use strict';
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, 'datos');
// usa el reporte mas reciente disponible
const archivos = fs.readdirSync(DIR).filter(f => f.startsWith('reporte_ventas_') && f.endsWith('.json')).sort();
if (!archivos.length) { console.error('No hay datos/reporte_ventas_*.json; corre antes: node reporte_motors.js'); process.exit(1); }
const D = JSON.parse(fs.readFileSync(path.join(DIR, archivos[archivos.length - 1]), 'utf8'));

const fmtU = n => Number(n).toLocaleString('en-US');
const fmtM = n => Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 });
const sumTab = (tab, llave) => (tab.find(x => x.llave === llave) || { unidades: 0 }).unidades;
const factStatus = (tab, llave) => { const s = (tab || []).find(x => x.llave === llave); return s ? fmtU(s.unidades) : '0'; };
function edadMediana(det) {
  const e = det.map(d => d.edad).filter(x => x != null).sort((a, b) => a - b);
  return e.length ? e[Math.floor(e.length / 2)] + ' años' : 'Sin dato';
}
function lagenteTop(tab) { return tab.length && tab[0].llave !== '(sin registrar)' ? String(tab[0].llave).replace(' (VE)', '') : '—'; }

const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tablero Ventas — LatinBienMotors ${D.anio}</title>
<style>
:root{
  --honda-red:#cc0000; --honda-blue:#16213e; --bg:#f4f6fb; --card:#fff;
  --text:#1c2333; --muted:#5c6b8a; --accent:#0f3460; --border:#e3e8f2;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--text);padding:24px}
.wrap{max-width:1240px;margin:0 auto}
header{background:linear-gradient(135deg,var(--honda-blue),var(--accent));color:#fff;border-radius:14px;padding:22px 26px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;box-shadow:0 8px 22px rgba(0,0,0,.12)}
header .logo{font-size:25px;font-weight:800;letter-spacing:.5px}
header .logo span{color:#ffd24a}
header .meta{font-size:12px;opacity:.9;text-align:right;line-height:1.6}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:20px 0}
.kpi{background:var(--card);border-radius:12px;padding:16px;box-shadow:0 3px 10px rgba(0,0,0,.05);border-top:4px solid var(--accent)}
.kpi .v{font-size:27px;font-weight:800;color:var(--accent)}
.kpi .l{font-size:12px;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.4px}
.kpi.green{border-top-color:#1e9e5a}.kpi.green .v{color:#1e9e5a}
.kpi.yellow{border-top-color:#f59e0b}.kpi.yellow .v{color:#b45309}
.kpi.red{border-top-color:var(--honda-red)}.kpi.red .v{color:var(--honda-red)}
.card{background:var(--card);border-radius:12px;padding:18px;box-shadow:0 3px 10px rgba(0,0,0,.05);margin-bottom:16px}
.card h3{font-size:14px;color:var(--accent);margin-bottom:14px;display:flex;align-items:center;gap:8px}
.card h3::before{content:'';width:6px;height:18px;background:var(--honda-red);border-radius:3px}
.grid{display:grid;gap:16px}
@media(min-width:900px){.grid.cols2{grid-template-columns:1fr 1fr}.grid.cols3{grid-template-columns:repeat(3,1fr)}}
/* barras verticales (por mes) */
.bars{display:flex;align-items:flex-end;gap:10px;height:220px}
.bar-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;min-width:0}
.bar-col .bar{width:100%;max-width:64px;border-radius:8px 8px 0 0;background:linear-gradient(180deg,#cc0000,#8c0000);position:relative;transition:height .6s ease}
.bar-col .bar .cnt{position:absolute;top:-24px;left:0;right:0;text-align:center;font-weight:800;font-size:15px;color:#222}
.bar-col .mto{position:absolute;top:-42px;left:0;right:0;text-align:center;font-size:10px;color:var(--muted);font-weight:600}
.bar-col .lab{margin-top:8px;font-size:11px;color:var(--muted);text-align:center}
/* barras horizontales (dimensiones) */
.hrow{display:flex;align-items:center;gap:10px;margin-bottom:9px}
.hname{min-width:150px;font-size:12px;font-weight:700;color:var(--honda-blue)}
.hbar{flex:1;height:20px;border-radius:8px;background:#eef1f8;overflow:hidden}
.hfill{height:100%;border-radius:8px;background:linear-gradient(180deg,#e04a4a,#cc0000);transition:width .7s ease}
.hfill.g{background:linear-gradient(180deg,#34c07a,#1e9e5a)}
.hfill.y{background:linear-gradient(180deg,#fbbf24,#f59e0b)}
.hnum{min-width:118px;font-size:12px;text-align:right;white-space:nowrap;color:var(--text)}
/* tabs */
.tabs{display:flex;gap:8px;margin:18px 0 0;flex-wrap:wrap}
.tab-btn{background:#e8ecf6;border:none;color:var(--accent);font-weight:700;font-size:14px;padding:10px 22px;border-radius:10px 10px 0 0;cursor:pointer}
.tab-btn.active{background:var(--card);color:var(--honda-red)}
.tab-panel{display:none}.tab-panel.active{display:block}
/* tablas */
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--border)}
th{background:var(--honda-blue);color:#fff;font-size:11px;text-transform:uppercase;letter-spacing:.4px;position:sticky;top:0}
tr:nth-child(even){background:#f8faff}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.tfoot td{font-weight:800;background:#eef2fb}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;color:#fff}
.b-cr{background:#536dfe}.b-co{background:#1e9e5a}.b-sf{background:#94a3b8}
.btn-f{background:#e8ecf6;border:none;border-radius:8px;padding:6px 14px;margin:2px 4px 8px 0;font-weight:700;color:var(--accent);cursor:pointer;font-size:12px}
.btn-f.active{background:var(--honda-red);color:#fff}
.mini{font-size:11px;color:var(--muted)}
footer{text-align:center;margin-top:20px;font-size:12px;color:var(--muted);line-height:1.7}
.scroll{max-height:420px;overflow:auto;border:1px solid var(--border);border-radius:10px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div>
    <div class="logo">Tablero Ventas <span>LATINBIENMOTORS</span></div>
    <div style="font-size:13px;opacity:.85;margin-top:4px">Honda Mérida — Ingresos y perfil del comprador ${D.anio}</div>
  </div>
  <div class="meta">Fuente: Odoo latinbienmotors.com (BD latinbien) · solo lectura<br>Actualizado: ${D.generado.slice(0, 19).replace('T', ' ')} UTC · corte ${D.reservado.alCorte}</div>
</header>

<!-- KPIs -->
<div class="kpis">
  <div class="kpi green"><div class="v">${fmtU(D.total.unidades)}</div><div class="l">Unidades entregadas ${D.anio}</div></div>
  <div class="kpi"><div class="v">$ ${fmtM(D.total.monto)}</div><div class="l">Monto entregado sin IVA</div></div>
  <div class="kpi"><div class="v">${fmtU(D.total.pedidos)}</div><div class="l">Pedidos entregados</div></div>
  <div class="kpi"><div class="v">$ ${fmtM(D.total.monto / (D.total.unidades || 1))}</div><div class="l">Ticket promedio sin IVA</div></div>
  <div class="kpi yellow"><div class="v">${fmtU(D.reservado.unidades)}</div><div class="l">Reservadas (almacén Reservas)</div></div>
  <div class="kpi red"><div class="v">${fmtU(D.facturadoNoEntregado.unidades)}</div><div class="l">Facturadas no entregadas (FNE)</div></div>
</div>

<!-- Pestañas -->
<div class="tabs">
  <button class="tab-btn active" data-tab="pFactu">Facturación (59)</button>
  <button class="tab-btn" data-tab="pPerfil">Perfil del Cliente</button>
  <button class="tab-btn" data-tab="pReservadas">Reservadas</button>
  <button class="tab-btn" data-tab="pDetalle">Detalle Vendido</button>
</div>

<!-- Facturacion Clientes (cuadra con inventariohonda / pestaña Facturación) -->
<div class="tab-panel active" id="pFactu">
  <div class="kpis">
    <div class="kpi"><div class="v">${fmtU(D.facturacionClientes.total.unidades)}</div><div class="l">Unidades facturadas (vehículo)</div></div>
    <div class="kpi green"><div class="v">$ ${fmtM(D.facturacionClientes.total.monto)}</div><div class="l">Monto facturado sin IVA</div></div>
    <div class="kpi"><div class="v">${fmtU(D.facturacionClientes.detalle.length)}</div><div class="l">Facturas emitidas (1 vehículo cada una)</div></div>
  </div>
  <div class="card">
    <tbody id="tMesFact"></tbody></table>
    <div class="mini" style="margin-top:8px">Fuente: Facturación Clientes con etiqueta VENTAVEHICULOCONSIG = favorito "FacturacionVehiculo" en Odoo. Indiferente de entrega.</div>
  </div>
  <div class="card"><h3>Forma de venta (de las 47 entregadas)</h3><div id="hForma"></div>
      <div class="mini">Contado (CRM): 20 clientes en etapa "Facturado Contado" → 16 ya entre las 47 entregadas. Los 4 faltantes (pendientes): F. Niño, M. Osorio y J. Guillen (facturados, sin entregar) y D. Esquivel (sin factura en Odoo). Crédito = el resto (plan de plazos SAV).</div>
  </div>
  <div class="grid cols2">
    <div class="card"><h3>Perfil del comprador — pendientes de entrega</h3>
      <div id="fFGen"></div>
      <div class="mini" style="margin-top:4px">Género.</div>
      <div id="fFEdad" style="margin-top:10px"></div>
    </div>
    <div class="card"><h3>Perfil del comprador — pendientes (datos de ficha)</h3>
      <div id="fFEstado"></div>
      <div class="mini" style="margin-top:4px">Departamento del cliente.</div>
      <div id="fFAct" style="margin-top:10px"></div>
      <div class="mini" style="margin-top:4px">Actividad. Los "Sin dato" = campo vacío en la ficha de Motors.</div>
    </div>
  </div>
</div>

<!-- Perfil -->
<div class="tab-panel" id="pPerfil">
  <div class="kpis">
    <div class="kpi"><div class="v">${fmtU(sumTab(D.porGenero, 'Caballero'))}</div><div class="l">Caballeros</div></div>
    <div class="kpi"><div class="v">${fmtU(sumTab(D.porGenero, 'Dama'))}</div><div class="l">Damas</div></div>
    <div class="kpi"><div class="v">${edadMediana(D.detalle)}</div><div class="l">Edad mediana de comprador</div></div>
    <div class="kpi"><div class="v">${lagenteTop(D.porEstado) || '—'}</div><div class="l">Departamento principal</div></div>
  </div>
  <div class="card"><h3>Por rango de edad</h3><div id="hEdad"></div></div>
  <div class="grid cols2">
    <div class="card"><h3>Por género (Dama / Caballero)</h3><div id="hGenero"></div></div>
    <div class="card"><h3>Por departamento</h3><div id="hEstado"></div></div>
  </div>
  <div class="grid cols2">
    <div class="card"><h3>Por actividad</h3><div id="hAct"></div><div class="mini">Clasificación del contacto en Odoo (Trabajador Profesional).</div></div>
    <div class="card"><h3>Por profesión declarada (top 12)</h3><div id="hProf"></div><div class="mini">Texto libre del contacto; "(sin registrar)" = campo vacío en Motors.</div></div>
  </div>
</div>

<!-- Reservadas -->
<div class="tab-panel" id="pReservadas">
  <div class="kpis">
    <div class="kpi yellow"><div class="v">${fmtU(D.reservado.unidades)}</div><div class="l">Reservadas al corte ${D.reservado.alCorte}</div></div>
    <div class="kpi red"><div class="v">${fmtU(D.facturadoNoEntregado.unidades)}</div><div class="l">Facturadas no entregadas</div></div>
  </div>
  <div class="card"><h3>Detalle de reservas (almacén Reservas RLBM)</h3>
    <table><thead><tr><th>Modelo</th><th>Color / VIN</th><th>Cliente reservante</th><th>Género</th><th>Edad</th><th>Departamento</th><th>Profesión</th></tr></thead>
    <tbody id="tRes"></tbody></table>
    <div class="mini" style="margin-top:8px">Contacto obtenido del traslado a Reservas (stock.move). Las dimensiones dependen de la ficha del contacto en Odoo Motors.</div>
  </div>
  <div class="card"><h3>Facturadas no entregadas (FNE, informativo)</h3>
    <table><thead><tr><th>Modelo / VIN</th><th>Unid.</th></tr></thead><tbody id="tFNE"></tbody></table>
  </div>
</div>

<!-- Detalle -->
<div class="tab-panel" id="pDetalle">
  <div class="card">
    <h3>Detalle del vendido ${D.anio} (una fila = una unidad)</h3>
    <div id="filtMes" style="margin-bottom:6px"></div>
    <div class="scroll"><table><thead><tr><th>Mes</th><th>Entrega</th><th>Pedido</th><th>Cliente</th><th>Modelo</th><th>Monto sin IVA</th><th>Forma</th><th>Género</th><th>Edad</th><th>Depto</th><th>Profesión</th></tr></thead>
    <tbody id="tDet"></tbody></table></div>
  </div>
</div>

<footer>
  Vendido = pedidos con Status Operativo 6 (Entregado) por fecha de entrega · Reservado = VIN en almacén Reservas (RLBM) · Montos sin IVA, vehículos Honda.<br>
  LatinBienMotors — consulta de solo lectura sobre Odoo. Fuente interna; no publicar fuera de la gerencia.
</footer>
</div>

<script>
"use strict";
const RES = ${JSON.stringify(D)};
// ---- Fusionar perfil de faltantes (12) al perfil principal (47) = 59 total ----
const FF = RES.facturacionClientes?.faltantes;
if (FF) {
  // Merge gender: add pending Caballero/Dama to main porGenero
  const mainGen = { Caballero: 0, Dama: 0 };
  RES.porGenero.forEach(r => { if (r.llave === 'Caballero') mainGen.Caballero = r.unidades; if (r.llave === 'Dama') mainGen.Dama = r.unidades; });
  FF.porGenero.forEach(r => { mainGen[r.llave] = (mainGen[r.llave] || 0) + r.unidades; });
  RES.porGenero = [
    {llave: 'Caballero', unidades: mainGen.Caballero, monto: 0, pedidos: 0, clientes: 0},
    {llave: 'Dama', unidades: mainGen.Dama, monto: 0, pedidos: 0, clientes: 0}
  ];
  // Merge age rango: add pending ranges to main porEdad
  const mainEdad = {};
  RES.porEdad.forEach(r => { mainEdad[r.llave] = r.unidades; });
  FF.porEdad.forEach(r => { mainEdad[r.llave] = (mainEdad[r.llave] || 0) + r.unidades; });
  // Ensure all ranges exist in correct order
  const order = ['35-44','45-54','25-34','55-64','65+','Sin dato'];
  RES.porEdad = order.map(k => ({llave: k, unidades: mainEdad[k] || 0, monto: 0, pedidos: 0, clientes: 0}));
}
function fmtU(n){ return Number(n).toLocaleString('en-US'); }
function fmtM(n){ return Number(n).toLocaleString('en-US', {maximumFractionDigits: 2}); }
const sumTab = (tab, llave) => (tab.find(x => x.llave === llave) || {unidades: 0}).unidades;
function edadMediana(det){
  const e = det.map(d => d.edad).filter(x => x != null).sort((a, b) => a - b);
  return e.length ? e[Math.floor(e.length / 2)] + ' años' : 'Sin dato';
}
function lagenteTop(tab){ return tab.length && tab[0].llave !== '(sin registrar)' ? tab[0].llave.replace(' (VE)', '') : '—'; }

// ---- barras horizontales reutilizables ----
function hbars(id, tab, color, capTotal){
  const el = document.getElementById(id);
  if (!el) return;
  const filas = capTotal ? tab.slice(0, capTotal) : tab;
  const max = Math.max(...filas.map(r => r.unidades), 1);
  el.innerHTML = filas.map(r =>
    '<div class="hrow"><div class="hname" title="' + String(r.llave).replace(/"/g, '&quot;') + '">' + r.llave + '</div>' +
    '<div class="hbar"><div class="hfill ' + (color || '') + '" style="width:' + (r.unidades / max * 100).toFixed(1) + '%"></div></div>' +
    '<div class="hnum"><b>' + r.unidades + '</b> un · ' + fmt$(r.monto) + '</div></div>').join('');
}
hbars('hEdad', RES.porEdad, 'y');
hbars('hGenero', RES.porGenero, 'g');
hbars('hEstado', RES.porEstado);
hbars('hAct', RES.porActividad, 'y');
hbars('hProf', RES.porProfesion, '', 12);
hbars('hForma', RES.porForma, 'g');

// ---- Facturación Clientes (cuadra con inventariohonda: fecha de factura, indiferente de entrega) ----
(function(){
  const F = RES.facturacionClientes;
  if (!F) return;
  const NOMBRES_MES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
  // barras por mes: altura = monto, encabezado = unidades
  const eBF = document.getElementById('bMesesFact');
  if (eBF) {
    const max = Math.max.apply(null, F.porMes.map(r => r.monto).concat(1));
    eBF.innerHTML = F.porMes.map(r => {
      const p = String(r.llave).split('-');
      const nom = NOMBRES_MES[Number(p[1]) - 1] + ' ' + p[0].slice(2);
      return '<div class="bar-col"><div class="mto">' + fmt$(r.monto) + '</div>' +
        '<div class="bar" style="height:' + (r.monto / max * 84).toFixed(1) + '%"><div class="cnt">' + r.unidades + '</div></div>' +
        '<div class="lab">' + nom + '</div></div>';
    }).join('');
  }
  // tabla desglose por mes / status
  const eTF = document.getElementById('tMesFact');
  if (eTF) {
    let tEnt = 0, tNoe = 0, tSin = 0;
    const filas = F.porMes.map(r => {
      return '<tr><td>' + r.llave + '</td><td class="num"><b>' + r.unidades + '</b></td><td class="num">' + fmt$(r.monto) + '</td></tr>';
    }).join('');
    eTF.innerHTML = filas + '<tr class="tfoot"><td>TOTAL</td><td class="num">' + F.total.unidades + '</td><td class="num">' + fmt$(F.total.monto) + '</td></tr>';
  }
  // perfil combinado ya está integrado en RES.porGenero y RES.porEdad (anterior)
// No Mostrar barras fFGen/fFEdad/fFEstado/fFAct separadas
  // (Los datos de los 12 faltantes ya fueron sumados al perfil principal arriba)
})();

// ---- tablas ---

const bdg = f => f && /contado/i.test(f) ? 'b-co' : /sin factura/i.test(f) ? 'b-sf' : 'b-cr';
document.getElementById('tRes').innerHTML =
  RES.reservado.detalle.map((r, i) =>
    '<tr><td><b>' + r.modelo + '</b></td><td style="font-family:Consolas,monospace">' + r.vin + '</td><td>' + (r.cliente || '—') + '</td><td>' + r.genero + '</td><td>' + (r.edad != null ? r.edad : '—') + '</td><td>' + r.estado + '</td><td>' + r.profesion + '</td></tr>').join('');
document.getElementById('tFNE').innerHTML =
  RES.facturadoNoEntregado.detalle.map(u => '<tr><td>' + u.modelo + '</td><td class="num">' + u.unidades + '</td></tr>').join('') +
  '<tr class="tfoot"><td>TOTAL</td><td class="num">' + RES.facturadoNoEntregado.unidades + '</td></tr>';

// ---- detalle con filtro por mes ----
function pintarDetalle(mes){
  const filas = mes ? RES.detalle.filter(d => d.mes === mes) : RES.detalle;
  document.getElementById('tDet').innerHTML = filas.map(d =>
    '<tr><td>' + d.mes + '</td><td>' + d.fechaStr.slice(0, 10) + '</td><td>' + d.pedido + '</td><td>' + d.cliente + '</td><td>' + d.modelo + '</td>' +
    '<td class="num">' + fmt$(d.montoSinIva) + '</td><td><span class="badge ' + bdg(d.forma) + '">' + d.forma + '</span></td><td>' + d.genero + '</td><td>' + (d.edad != null ? d.edad : '—') + '</td><td>' + d.estado + '</td><td>' + d.profesion + '</td></tr>').join('');
}
(function(){
  const filt = document.getElementById('filtMes');
  const meses = [...new Set(RES.detalle.map(d => d.mes))].sort();
  filt.innerHTML = '<button class="btn-f active" data-m="">Todo (' + RES.detalle.length + ')</button>' +
    meses.map(m => '<button class="btn-f" data-m="' + m + '">' + m + '</button>').join('');
  filt.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    filt.querySelectorAll('button').forEach(x => x.classList.remove('active'));
    b.classList.add('active'); pintarDetalle(b.dataset.m);
  });
  pintarDetalle(null);
})();

// ---- pestañas ----
document.querySelectorAll('.tab-btn').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.tab-btn').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  b.classList.add('active'); document.getElementById(b.dataset.tab).classList.add('active');
}));
</script>
</body>
</html>`;

const salida = path.join(__dirname, 'reporte', 'tablero_ventas.html');
fs.mkdirSync(path.dirname(salida), { recursive: true });
fs.writeFileSync(salida, html, 'utf8');
console.log('Tablero generado:', salida, '| datos:', archivos[archivos.length - 1]);
