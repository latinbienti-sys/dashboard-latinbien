#!/usr/bin/env node
// Genera reporte/tablero.html desde datos/reporte_ventas_<hoy>.json
// Standalone: sin CDN ni dependencias, gráficos en CSS puro (estilo inventariohonda).
// Versión simplificada: UNA sola pestaña "Facturación" con TODO: KPIs, barras, tabla, forma de venta, perfil combinado.

'use strict';
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, 'datos');
// usa el reporte mas reciente disponible
const archivos = fs.readdirSync(DIR).filter(f => f.startsWith('reporte_ventas_') && f.endsWith('.json')).sort();
if (!archivos.length) { console.error('No hay datos/reporte_ventas_*.json; corre antes: node reporte_motors.js'); process.exit(1); }
const D = JSON.parse(fs.readFileSync(path.join(DIR, archivos[archivos.length - 1]), 'utf8'));

// Funciones auxiliares (una sola definición)
const fmtU = n => Number(n).toLocaleString('en-US');
const fmtM = n => Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 });
const sumTab = (tab, llave) => (tab.find(x => x.llave === llave) || { unidades: 0 }).unidades;
function edadMediana(det){
  const e = det.map(d => d.edad).filter(x => x != null).sort((a, b) => a - b);
  return e.length ? e[Math.floor(e.length / 2)] + ' años' : 'Sin dato';
}
function lagenteTop(tab){ return tab.length && tab[0].llave !== '(sin registrar)' ? String(tab[0].llave).replace(' (VE)', '') : '—' };

// ---- Fusionar perfil de faltantes (12) al perfil principal (47) = 59 total ----
const FF = D.facturacionClientes?.faltantes;
if (FF) {
  // Merge gender: add pending Caballero/Dama to main porGenero
  const mainGen = { Caballero: 0, Dama: 0 };
  D.porGenero.forEach(r => { if (r.llave === 'Caballero') mainGen.Caballero = r.unidades; if (r.llave === 'Dama') mainGen.Dama = r.unidades; });
  FF.porGenero.forEach(r => { mainGen[r.llave] = (mainGen[r.llave] || 0) + r.unidades; });
  D.porGenero = [
    {llave: 'Caballero', unidades: mainGen.Caballero, monto: 0, pedidos: 0, clientes: 0},
    {llave: 'Dama', unidades: mainGen.Dama, monto: 0, pedidos: 0, clientes: 0}
  ];
  // Merge edad rango: add pending ranges to main porEdad
  const mainEdad = {};
  D.porEdad.forEach(r => { mainEdad[r.llave] = r.unidades; });
  FF.porEdad.forEach(r => { mainEdad[r.llave] = (mainEdad[r.llave] || 0) + r.unidades; });
  // Ensure all ranges exist in correct order
  const order = ['35-44','45-54','25-34','55-64','65+','Sin dato'];
  D.porEdad = order.map(k => ({llave: k, unidades: mainEdad[k] || 0, monto: 0, pedidos: 0, clientes: 0}));
}

// Generación del HTML
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
*{-moz-box-sizing:border-box;-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0}
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
/* barras horizontales (dimensiones) */
.hrow{display:flex;align-items:center;gap:10px;margin-bottom:9px}
.hname{min-width:150px;font-size:12px;font-weight:700;color:var(--honda-blue)}
.hbar{flex:1;height:20px;border-radius:8px;background:#eef1f8;overflow:hidden}
.hfill{height:100%;border-radius:8px;background:linear-gradient(180deg,#e04a4a,#cc0000);transition:width .7s ease}
.hfill.g{background:linear-gradient(180deg,#34c07a,#1e9e5a)}
.hfill.y{background:linear-gradient(180deg,#fbbf24,#f59e0b)}
.hnum{min-width:118px;font-size:12px;text-align:right;white-space:nowrap;color:var(--text)}
/* --- SOLO UNA PESTAÑA: Facturación --- */
/* Ocultamos la navegación de pestañas y mostramos siempre el panel Facturación */
.tab-btn{display:none}
.tab-panel{display:block !important}
.tab-panel.active{display:block !important}
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

<!-- Facturacion Clientes (cuadra con inventariohonda / pestaña Facturación) -->
<div class="tab-panel active" id="pFactu">
  <div class="kpis">
    <div class="kpi"><div class="v">${fmtU(D.facturacionClientes.total.unidades)}</div><div class="l">Unidades facturadas (vehículo)</div></div>
    <div class="kpi green"><div class="v">$ ${fmtM(D.facturacionClientes.total.monto)}</div><div class="l">Monto facturado sin IVA</div></div>
    <div class="kpi"><div class="v">${fmtU(D.facturacionClientes.detalle.length)}</div><div class="l">Facturas emitidas (1 vehículo cada una)</div></div>
  </div>
  <div class="card"><h3>Forma de venta (de las 47 entregadas)</h3><div id="hForma"></div>
      <div class="mini">Contado (CRM): 20 clientes en etapa "Facturado Contado" → 16 ya entre las 47 entregadas. Los 4 faltantes (pendientes): F. Niño, M. Osorio y J. Guillen (facturados, sin entregar) y D. Esquivel (sin factura en Odoo). Crédito = el resto (plan de plazos SAV).
  </div>
  <div class="card"><h3>Facturado por mes (fecha de factura) — unidades y monto sin IVA, indiferente de entrega</h3>
    <div class="bars" id="bMesesFact"></div>
  </div>
  <div class="card"><table><thead><tr><th>Mes</th><th>Vehículos</th><th>Monto sin IVA</th></tr></thead><tbody id="tMesFact"></tbody></table>
    <div class="mini" style="margin-top:8px">Fuente: Facturación Clientes con etiqueta VENTAVEHICULOCONSIG = favorito "FacturacionVehiculo" en Odoo. Indiferente de entrega.</div>
  </div>
  <div class="grid cols2">
    <div class="card"><h3>Perfil del comprador — entregados + pendientes (59 total)</h3>
      <div id="hGenero"></div>
      <div class="mini">Género: Caballeros 35 + Damas 24 = 59 total.</div>
    </div>
    <div class="card"><h3>Por rango de edad</h3><div id="hEdad"></div></div>
  </div>
  <div class="grid cols2">
    <div class="card"><h3>Por departamento</h3><div id="hEstado"></div><div class="mini">Mérida 33, Táchira 3, Zulia 2, Monagas 1, Sin registrar 6.</div></div>
    <div class="card"><h3>Por actividad</h3><div id="hAct"></div><div class="mini">Clasificación del contacto en Odoo (Trabajador Profesional).</div></div>
  </div>
  <div class="card"><h3>Por profesión declarada (top 12)</h3><div id="hProf"></div><div class="mini">Texto libre del contacto; "(sin registrar)" = campo vacío en Motors.</div></div>
</div>
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
  // Merge edad rango: add pending ranges to main porEdad
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
function lagenteTop(tab){ return tab.length && tab[0].llave !== '(sin registrar)' ? tab[0].llave.replace(' (VE)', '') : '—' };

// ---- barras horizontales reutilizables ----
function hbars(id, tab, color, capTotal){
  const el = document.getElementById(id);
  if (!el) return;
  const filas = capTotal ? tab.slice(0, capTotal) : tab;
  const max = Math.max(...filas.map(r => r.unidades), 1);
  el.innerHTML = filas.map(r =>
    '<div class="hrow"><div class="hname" title="' + String(r.llave).replace(/"/g, '"') + '">' + r.llave + '</div>' +
    '<div class="hbar"><div class="hfill ' + (color || '') + '" style="width:' + (r.unidades / max * 100).toFixed(1) + '%"></div></div>' +
    '<div class="hnum"><b>' + r.unidades + '</b> un · ' + fmt$(r.monto) + '</div></div>').join('');
}
hbars('hEdad', RES.porEdad, 'y');
hbars('hGenero', RES.porGenero, 'g');
hbars('hEstado', RES.porEstado);
hbars('hAct', RES.porActividad, 'y');
hbars('hProf', RES.porProfesion, '', 12);

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
})();

// ---- Forma de venta (16 Contado CRM / 30+1 Crédito SAV) ----
(function(){
  const formaData = { Contado: 16, 'Crédito (SAV)': 30, 'Crédito (sin factura)': 1 };
  const hForma = document.getElementById('hForma');
  if (hForma) {
    let totalUnid = 0, totalMonto = 0;
    for (const [llave, unidad] of Object.entries(formaData)) {
      totalUnid += unidad;
    }
    hForma.innerHTML = Object.entries(formaData).map(([llave, unidad]) => 
      '<div class="hrow"><div class="hname">' + llave + '</div>' +
      '<div class="hbar"><div class="hfill g" style="width:' + (unidad / totalUnid * 100).toFixed(1) + '%"></div></div>' +
      '<div class="hnum"><b>' + unidad + '</b> un</div></div>'
    ).join('');
  }
})();
</script>

<!-- Reservadas y Detalle Vendido eliminados para enfoque único -->

<footer>
  Vendido = pedidos con Status Operativo 6 (Entregado) por fecha de entrega · Reservado = VIN en almacén Reservas (RLBM) · Montos sin IVA, vehículos Honda.
  LatinBienMotors — consulta de solo lectura sobre Odoo. Fuente interna; no publicar fuera de la gerencia.
</footer>
</div>
</body>
</html>`;

const salida = path.join(__dirname, 'reporte', 'tablero_ventas.html');
fs.mkdirSync(path.dirname(salida), { recursive: true });
fs.writeFileSync(salida, html, 'utf8');
console.log('Tablero generado:', salida, '| datos:', archivos[archivos.length - 1]);