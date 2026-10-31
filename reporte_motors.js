#!/usr/bin/env node
// Reporte de ventas de vehículos - LatinBienMotors (latinbienmotors.com, BD latinbien).
// SOLO LECTURA (mismos métodos permitidos que coach-comercial). No escribe nada en Odoo.
//
// Definiciones = mismas de inventariohonda (generar_inventario.py):
//   VENDIDO    : sale.order con x_status_operativos='6' (Entregado), mes por commitment_date.
//                Unidades = líneas cuyo producto contiene "honda"; monto = price_subtotal (sin IVA).
//   RESERVADO  : unidades (lotes/VIN) con cantidad > 0 en ubicaciones internas "RLBM%" (almacén Reservas).
//                Contacto = último stock.move done cuyo destino fue RLBM/FNE (igual que la página).
//   En factura: x_contado (Es contado?) define Contado vs Crédito.
//
// Dimensiones del cliente (res.partner): genero (f=Dama, m=Caballero), edad (birthdate_date),
// departamento (state_id), profesion (work_profesion) y actividad (work_profesional / work_ramo).
//
// Uso:  node reporte_motors.js [--anio 2026]
// Genera: datos/reporte_ventas_<AAAA-MM-DD>.json  (+ resumen en consola)

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const METODOS_PERMITIDOS = new Set(['search_read', 'read', 'fields_get', 'search_count']);
const DIR = path.join(__dirname, 'datos');
const TZ = -4; // Caracas

function credenciales() {
  let c = {}, archivo = null;
  for (const ruta of [
    path.join(os.homedir(), 'odoo-credentials-motors.json'),
    path.join(os.homedir(), '.odoo-credentials-motors.json'),
    path.join(os.homedir(), '.odoo-credentials.json'),
  ]) {
    if (fs.existsSync(ruta)) { c = JSON.parse(fs.readFileSync(ruta, 'utf8')); archivo = ruta; break; }
  }
  let url = c.host || process.env.ODOO_URL || 'https://latinbienmotors.com';
  if (!/^https?:\/\//.test(url)) url = 'https://' + url;
  const cfg = {
    url: url.replace(/\/+$/, ''),
    db: c.db || process.env.ODOO_DB || 'latinbien',
    login: c.login || process.env.ODOO_USER,
    password: c.password || process.env.ODOO_PASS,
    archivo,
  };
  if (!cfg.login || !cfg.password) throw new Error('Faltan credenciales');
  return cfg;
}

async function conectar() {
  const cfg = credenciales();
  let cookie = '';
  const rpc = async (ruta, params) => {
    let r;
    for (let intento = 1; ; intento++) {
      try {
        r = await fetch(cfg.url + ruta, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(cookie ? { Cookie: cookie } : {}) },
          body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params, id: Date.now() }),
        });
        break;
      } catch (e) {
        if (intento >= 4) throw e;
        await new Promise(res => setTimeout(res, 2000 * intento));
      }
    }
    const sc = r.headers.get('set-cookie');
    if (sc) cookie = sc.split(';')[0];
    if (!r.ok) throw new Error(`HTTP ${r.status} en ${ruta}`);
    const j = await r.json();
    if (j.error) throw new Error((j.error.data && j.error.data.message) || j.error.message);
    return j.result;
  };
  const auth = await rpc('/web/session/authenticate', { db: cfg.db, login: cfg.login, password: cfg.password });
  if (!auth || !auth.uid) throw new Error('No se pudo iniciar sesion en Odoo');
  const llamar = (model, method, args = [], kwargs = {}) => {
    if (!METODOS_PERMITIDOS.has(method)) throw new Error(`Metodo bloqueado (solo lectura): ${method}`);
    return rpc('/web/dataset/call_kw', { model, method, args, kwargs });
  };
  return { llamar, archivo: cfg.archivo };
}

const n2 = n => String(n).padStart(2, '0');
const nombre = v => (Array.isArray(v) ? v[1] : v) || '';
const hoyStr = () => { const d = new Date(Date.now() + TZ * 3600000); return `${d.getUTCFullYear()}-${n2(d.getUTCMonth() + 1)}-${n2(d.getUTCDate())}`; };
const esVehiculo = n => /honda/i.test(String(n || ''));

function edadDe(nac, hoyISO) {
  if (!nac) return null;
  const n = new Date(nac + 'T00:00:00Z'), h = new Date(hoyISO + 'T00:00:00Z');
  if (isNaN(n)) return null;
  let e = h.getUTCFullYear() - n.getUTCFullYear();
  const m = h.getUTCMonth() - n.getUTCMonth();
  if (m < 0 || (m === 0 && h.getUTCDate() < n.getUTCDate())) e--;
  return e >= 0 && e < 120 ? e : null;
}
const rangoEdad = e => (e == null ? 'Sin dato' : e < 25 ? '18-24' : e < 35 ? '25-34' : e < 45 ? '35-44' : e < 55 ? '45-54' : e < 65 ? '55-64' : '65+');
const estiloLbl = { dependiente_privado: 'Dependiente sector privado', dependiente_publico: 'Dependiente sector público', independiente_formal: 'Independiente formal', infdependiente_informal: 'Independiente informal', independiente: 'Independiente', bajo_dependencia: 'Bajo dependencia' };
const generoLbl = g => (g === 'f' ? 'Dama' : g === 'm' ? 'Caballero' : g && g !== 'false' ? 'Otros' : 'Sin dato');
const normTxt = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^A-Z0-9]/gi, '').toUpperCase();
function lcsLen(A, B) {
  const m = A.length, n = B.length;
  if (!m || !n) return 0;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) for (let j = 1; j <= n; j++)
    dp[i][j] = A[i - 1] === B[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
  return dp[m][n];
}
// Empareja el cliente del pedido con los contactos de la etapa CRM indicada.
// Prioriza ID de contacto; si no, nombre casi-igual (contactos a veces duplicados).
function matcherCRM(leads) {
  const ids = new Set(), nombres = [];
  leads.forEach(l => {
    if (Array.isArray(l.partner_id) && l.partner_id[0]) { ids.add(l.partner_id[0]); nombres.push(l.partner_id[1]); }
    const deNombre = String(l.name || '').replace(/^Oportunidad de /i, '').trim();
    if (deNombre) nombres.push(deNombre);
  });
  const listaN = nombres.map(n => normTxt(n)).filter(Boolean);
  return p => {
    const pid = Array.isArray(p.partner_id) ? p.partner_id[0] : null;
    if (pid && ids.has(pid)) return true;
    const N = normTxt(nombre(p.partner_id));
    if (!N) return false;
    return listaN.some(X => X === N || (lcsLen(X, N) / Math.min(X.length, N.length)) >= 0.92);
  };
}

// ---------- 1) Pedidos ENTREGADOS (status 6) ----------
async function main() {
  const [ , , anioArg ] = process.argv;
  const anio = Number(anioArg) || 2026;
  const d0 = `${anio}-01-01 04:00:00`, d1 = `${anio + 1}-01-01 04:00:00`;
  const hoyISO = hoyStr();
  const { llamar, archivo: archivoCreds } = await conectar();
  console.log(`Conectado a latinbienmotors.com (creds: ${path.basename(archivoCreds || '')}) - solo lectura`);
  console.log(`Ventana de entregas: ${anio} (por commitment_date)`);

  // ---------- 1) Pedidos ENTREGADOS (status 6) ----------
  const pedidos = [];
  for (let off = 0; ; off += 200) {
    const lote = await llamar('sale.order', 'search_read',
      [[['x_status_operativos', '=', '6'], ['commitment_date', '>=', d0], ['commitment_date', '<', d1]]],
      { fields: ['id', 'name', 'partner_id', 'commitment_date', 'date_order', 'user_id', 'order_line', 'invoice_ids', 'planes', 'tenure'], offset: off, limit: 200, order: 'commitment_date asc' });
    pedidos.push(...lote);
    if (lote.length < 200) break;
  }
  console.log(`Pedidos entregados: ${pedidos.length}`);

  // ---------- 2) Lineas de pedido (vehiculos) ----------
  const pedIds = pedidos.map(p => p.id);
  const lineasPed = [];
  for (let i = 0; i < pedIds.length; i += 200) {
    const lote = await llamar('sale.order.line', 'search_read',
      [[['order_id', 'in', pedIds.slice(i, i + 200)]]],
      { fields: ['order_id', 'product_id', 'product_uom_qty', 'price_subtotal'] });
    lineasPed.push(...lote.filter(l => l.order_id && pedIds.includes(l.order_id[0])));
  }
  const porPedido = {};
  lineasPed.forEach(l => { if (esVehiculo(l.product_id && l.product_id[1])) (porPedido[l.order_id[0]] = porPedido[l.order_id[0]] || []).push(l); });

  // ---------- 3) Facturas del pedido -> forma de venta (Contado/Credito) ----------
  const invIds = [...new Set(pedidos.flatMap(p => p.invoice_ids || []))];
  const formaDeInv = {};
  for (let i = 0; i < invIds.length; i += 200) {
    const factura = await llamar('account.move', 'read', [invIds.slice(i, i + 200), ['x_contado', 'move_type']]);
    (factura || []).forEach(f => formaDeInv[f.id] = f);
  }
  // ---------- 3b) Contado vía CRM: etapa "Facturado Contado" (id 12) ----------
  const leadsContado = await llamar('crm.lead', 'search_read',
    [[['stage_id', '=', 12], ['active', 'in', [true, false]]]], { fields: ['partner_id', 'name'] });
  const esContadoCRM = matcherCRM(leadsContado);
  console.log(`CRM: ${leadsContado.length} oportunidades en etapa "Facturado Contado"`);
  function formaVenta(p) {
    const invs = (p.invoice_ids || []).map(id => formaDeInv[id]).filter(Boolean);
    const vent = invs.filter(f => f.move_type === 'out_invoice' || f.move_type === 'out_refund');
    // Contado definido por el CRM: cliente con Oportunidad en etapa "Facturado Contado".
    if (esContadoCRM(p)) return 'Contado';
    if (vent.some(f => f.x_contado === true)) return 'Contado';
    if (vent.length) return 'Crédito (SAV)';
    if (p.planes && p.planes !== 'false') return 'Crédito (sin factura)';
    return 'Sin factura';
  }

  // ---------- 4) Reservado: unidades en RLBM (almacen Reservas) ----------
  const prefijos = {};
  for (const p of ['RLBM%', 'FNE%', 'CLBM%']) {
    const locs = await llamar('stock.location', 'search_read', [[['complete_name', 'like', p]]], { fields: ['id', 'complete_name', 'usage'] });
    prefijos[p.slice(0, -1)] = locs.filter(l => l.usage === 'internal').map(l => ({ id: l.id, name: l.complete_name }));
  }
  const rlbmIds = prefijos['RLBM'].map(l => l.id), fneIds = prefijos['FNE'].map(l => l.id), clbmIds = prefijos['CLBM'].map(l => l.id);

  async function quantsDe(ids) {
    const out = [];
    for (let i = 0; i < ids.length; i += 100) {
      const lote = await llamar('stock.quant', 'search_read',
        [[['location_id', 'in', ids.slice(i, i + 100)], ['quantity', '>', 0], ['lot_id', '!=', false]]],
        { fields: ['product_id', 'lot_id', 'quantity', 'reserved_quantity'] });
      out.push(...lote);
    }
    return out;
  }
  const quantsReserva = rlbmIds.length ? await quantsDe(rlbmIds) : [];
  const quantsFNE = fneIds.length ? await quantsDe(fneIds) : [];

  // Contacto por lote: ultimo movimiento done hacia RLBM/FNE.
  // La clave es el ID del lote. Si en el traslado el partner es la propia
  // empresa (LATINBIEN MOTORS C.A) se guarda solo como respaldo.
  const contactoPorLote = {};
  const esEmpresaPropia = n => /latinbien\s*motors/i.test(n);
  if (clbmIds.length || rlbmIds.length) {
    const movs = await llamar('stock.move', 'search_read',
      [[['location_dest_id', 'in', [...rlbmIds, ...fneIds]], ['location_id', 'in', [...clbmIds, ...rlbmIds]], ['state', '=', 'done']]],
      { fields: ['lot_ids', 'partner_id', 'date', 'product_id'], limit: 1000 });
    movs.forEach(m => {
      const lotes = (Array.isArray(m.lot_ids) ? m.lot_ids : []).flatMap(x => (Array.isArray(x) ? x[0] : [x]));
      const pid = Array.isArray(m.partner_id) ? m.partner_id[0] : null;
      const pname = nombre(m.partner_id);
      const propia = !pid || esEmpresaPropia(pname);
      const fecha = String(m.date || '');
      lotes.forEach(lid => {
        const prev = contactoPorLote[lid];
        if (!prev) contactoPorLote[lid] = { fecha, pid, pname, propia };
        else if (fecha > prev.fecha) {
          // si el nuevo es la empresa y ya teniamos contacto real, no lo pisamos
          if (!(propia && !prev.propia)) contactoPorLote[lid] = { fecha, pid, pname, propia };
        } else if (prev.propia && !propia) contactoPorLote[lid] = { fecha, pid, pname, propia };
      });
    });
  }

  // Consolidar unidades reservadas (por producto+lote, misma logica de la pagina)
  const aggRes = {};
  quantsReserva.forEach(q => {
    if (!esVehiculo(q.product_id && q.product_id[1])) return;
    const lotId = Array.isArray(q.lot_id) ? q.lot_id[0] : 0;
    const k = `${q.product_id[0]}#${lotId}`;
    const e = aggRes[k] || (aggRes[k] = { modelo: nombre(q.product_id), vin: nombre(q.lot_id), lotId, unidades: 0 });
    e.unidades += Number(q.quantity);
  });
  const reservadas = Object.values(aggRes).map(u => ({ ...u }));
  const aggFNE = {};
  quantsFNE.forEach(q => {
    if (!esVehiculo(q.product_id && q.product_id[1])) return;
    const lotId = Array.isArray(q.lot_id) ? q.lot_id[0] : 0;
    const k = `${q.product_id[0]}#${lotId}`;
    const e = aggFNE[k] || (aggFNE[k] = { modelo: nombre(q.product_id), vin: nombre(q.lot_id), unidades: 0 });
    e.unidades += Number(q.quantity);
  });
  const factNoEntregadas = Object.values(aggFNE);

  // ---------- 4b) Facturación Clientes (favorito "FacturacionVehiculo": etiqueta 81) ----------
  // Reglas = página inventariohonda: todas las facturas con la etiqueta, indiferente de entrega;
  // unidades y monto sin IVA = líneas Honda con cantidad > 0 (price_subtotal).
  const tagInvs = [];
  for (let off = 0; ; off += 200) {
    const lote = await llamar('account.move', 'search_read',
      [[['invoice_tag_ids', 'in', [81]]]],
      { fields: ['id', 'name', 'invoice_date', 'partner_id', 'invoice_user_id', 'x_status_operativos', 'state'], offset: off, limit: 200, order: 'invoice_date asc' });
    tagInvs.push(...lote);
    if (lote.length < 200) break;
  }
  const tagIds = tagInvs.filter(f => f.state !== 'cancel').map(f => f.id);
  const lineasInv = {};
  for (let i = 0; i < tagIds.length; i += 200) {
    const ls = await llamar('account.move.line', 'search_read',
      [[['move_id', 'in', tagIds.slice(i, i + 200)], ['quantity', '>', 0]]],
      { fields: ['move_id', 'product_id', 'quantity', 'price_subtotal'] });
    ls.forEach(l => {
      if (!esVehiculo(l.product_id && l.product_id[1])) return;
      const mid = Array.isArray(l.move_id) ? l.move_id[0] : null;
      if (!mid) return;
      const e = lineasInv[mid] || (lineasInv[mid] = { unidades: 0, monto: 0, modelos: [] });
      e.unidades += Number(l.quantity) || 0;
      e.monto += Number(l.price_subtotal) || 0;
      e.modelos.push(nombre(l.product_id));
    });
  }
  const STATUS_LBL = { '6': '6. CVG - ENTREGADO', '9': '5. FACTURADO- NO ENTREGADO' };
  const factDetalle = tagInvs
    .filter(f => f.state !== 'cancel')
    .map(f => {
      const L = lineasInv[f.id] || { unidades: 0, monto: 0, modelos: [] };
      return {
        factura: f.name, id: f.id,
        partnerId: Array.isArray(f.partner_id) ? f.partner_id[0] : 0,
        fecha: String(f.invoice_date || '').slice(0, 10),
        mes: String(f.invoice_date || '').slice(0, 7),
        cliente: nombre(f.partner_id),
        ejecutivo: nombre(f.invoice_user_id) || 'Sin asignar',
        status: STATUS_LBL[String(f.x_status_operativos || '')] || 'False',
        unidades: L.unidades,
        montoSinIva: Math.round(L.monto * 100) / 100,
        modelos: L.modelos,
      };
    });
  const ESTADO_COLUMNA = { '6. CVG - ENTREGADO': 'entregadas', '5. FACTURADO- NO ENTREGADO': 'factNoEntregadas', 'False': 'sinStatus' };
  function vacioMes() { return { unidades: 0, monto: 0, entregadas: 0, mEnt: 0, factNoEntregadas: 0, mNoEnt: 0, sinStatus: 0, mSin: 0 }; }
  const mTot = vacioMes(), mPorMes = {}, mPorStatus = {};
  factDetalle.forEach(f => {
    mTot.unidades += f.unidades; mTot.monto += f.montoSinIva;
    const c = ESTADO_COLUMNA[f.status]; const m = mPorMes[f.mes] || (mPorMes[f.mes] = vacioMes());
    m.unidades += f.unidades; m.monto += f.montoSinIva;
    m[c] += 1;
    m['m' + { entregadas: 'Ent', factNoEntregadas: 'NoEnt', sinStatus: 'Sin' }[c]] += f.montoSinIva;
    const ps = mPorStatus[f.status] || (mPorStatus[f.status] = { llave: f.status, unidades: 0, monto: 0 });
    ps.unidades += f.unidades; ps.monto += f.montoSinIva;
  });

  // ---------- 4c) Emparejador de entregadas vs facturadas + IDs de partners de facturas ----------
  const entregIds = new Set(pedidos.map(p => Array.isArray(p.partner_id) ? p.partner_id[0] : 0));
  const entregNombres = pedidos.map(p => normTxt(nombre(p.partner_id))).filter(Boolean);
  const esEntregadoFact = (pid, pname) => {
    if (pid && entregIds.has(pid)) return true;
    const N = normTxt(pname);
    if (!N) return false;
    return entregNombres.some(X => X === N || (lcsLen(X, N) / Math.min(X.length, N.length)) >= 0.92);
  };
  const factPartnerIds = [...new Set(factDetalle.map(f => f.partnerId).filter(Boolean))];

  // ---------- 5) Dimensiones de clientes (pedidos + reservados + facturadas) ----------
  const partnerIds = [...new Set([
    ...pedidos.map(p => Array.isArray(p.partner_id) ? p.partner_id[0] : null).filter(Boolean),
    ...factPartnerIds,
    ...(Object.values(contactoPorLote).map(c => c.pid).filter(Boolean)),
  ])];
  const partners = {};
  for (let i = 0; i < partnerIds.length; i += 200) {
    const lote = await llamar('res.partner', 'read', [partnerIds.slice(i, i + 200),
      ['name', 'gender', 'birthdate_date', 'state_id', 'work_profesion', 'work_profesional', 'work_ramo', 'work_state_id']]);
    (lote || []).forEach(p => {
      const st = nombre(p.state_id) || nombre(p.work_state_id) || '';
      partners[p.id] = {
        id: p.id, nombre: p.name, genero: p.gender || '',
        nacimiento: p.birthdate_date || '', edad: edadDe(p.birthdate_date, hoyISO),
        estado: st,
        profesion: p.work_profesion || '(sin registrar)',
        actividad: estiloLbl[p.work_profesional] || (p.work_profesional ? p.work_profesional : '(sin registrar)'),
        ramo: p.work_ramo || '',
      };
    });
  }

  // ---------- 5b) Perfil del cliente de los FALTANTES (facturados, no entregados) ----------
  function contarPerfil(filas, campo) {
    const o = {};
    filas.forEach(r => { const k = String(r[campo] || '(sin registrar)'); o[k] = (o[k] || 0) + 1; });
    return Object.entries(o).map(([llave, unidades]) => ({ llave, unidades })).sort((a, b) => b.unidades - a.unidades);
  }
  const filasFalt = factDetalle
    .filter(f => !esEntregadoFact(f.partnerId, f.cliente))
    .map(f => {
      const p = partners[f.partnerId] || {};
      return {
        factura: f.factura, fecha: f.fecha, mes: f.mes, cliente: f.cliente, ejecutivo: f.ejecutivo,
        status: f.status, unidades: f.unidades, montoSinIva: f.montoSinIva, modelos: f.modelos,
        genero: generoLbl(p.genero), edad: p.edad ?? null, edadRango: rangoEdad(p.edad),
        estado: (p.estado || '').replace(' (VE)', '') || '(sin registrar)',
        profesion: p.profesion || '(sin registrar)', actividad: p.actividad || '(sin registrar)',
      };
    })
    .sort((a, b) => String(a.mes).localeCompare(String(b.mes)));
  const faltantesPerfil = {
    definicion: 'Facturas con etiqueta VENTAVEHICULOCONSIG cuyo cliente no aparece entre los pedidos entregados (status 6), por ID o nombre',
    unidades: filasFalt.reduce((s, f) => s + f.unidades, 0),
    monto: Math.round(filasFalt.reduce((s, f) => s + f.montoSinIva, 0) * 100) / 100,
    detalle: filasFalt,
    porGenero: contarPerfil(filasFalt, 'genero'),
    porEdad: contarPerfil(filasFalt, 'edadRango'),
    porEstado: contarPerfil(filasFalt, 'estado'),
    porActividad: contarPerfil(filasFalt, 'actividad'),
  };
  console.log(`\nFacturadas pendientes de entrega: ${filasFalt.length} unidades - $${faltantesPerfil.monto}`);
  filasFalt.forEach(f => console.log(` ${f.fecha} | ${String(f.cliente).padEnd(34)} | ${f.genero.padEnd(11)} | ${f.edadRango.padEnd(8)} | ${f.status}`));

  // ---------- 6) Filas de ventas (una por unidad vehiculo) ----------
  const MESES_PERIODO = [];
  for (let m = 0; m < 12; m++) MESES_PERIODO.push(`${anio}-${n2(m + 1)}`);
  const filas = [];
  pedidos.forEach(p => {
    const partner = partners[Array.isArray(p.partner_id) ? p.partner_id[0] : null] || null;
    const lineas = porPedido[p.id] || [];
    lineas.forEach(l => {
      if (!esVehiculo(l.product_id && l.product_id[1])) return;
      const unidades = Number(l.product_uom_qty) || 0;
      if (unidades <= 0) return;
      filas.push({
        pedido: p.name, fechaStr: String(p.commitment_date || p.date_order || ''), mes: String(p.commitment_date || '').slice(0, 7),
        unidades, montoSinIva: Number(l.price_subtotal) || 0,
        modelo: nombre(l.product_id), clienteId: partner ? partner.id : null,
        cliente: partner ? partner.nombre : nombre(p.partner_id),
        forma: formaVenta(p), ejecutivo: nombre(p.user_id) || 'Sin asignar',
        genero: partner ? generoLbl(partner.genero) : 'Sin dato', edad: partner ? partner.edad : null,
        edadRango: partner ? rangoEdad(partner.edad) : 'Sin dato',
        estado: partner ? (partner.estado || '(sin registrar)') : '(sin registrar)',
        profesion: partner ? partner.profesion : '(sin registrar)',
        actividad: partner ? partner.actividad : '(sin registrar)',
        ramo: partner ? partner.ramo : '',
        partner: partner, // para referencia
      });
    });
  });

  // Filas de reservados (al corte)
  const filasRes = reservadas.map(u => {
    const c = contactoPorLote[u.lotId]; // se busca por ID del lote
    const partner = c && c.pid ? partners[c.pid] : null;
    return {
      vin: u.vin, modelo: u.modelo, cliente: partner ? partner.nombre : (c ? c.pname : ''),
      genero: partner ? generoLbl(partner.genero) : 'Sin dato',
      edad: partner ? partner.edad : null, edadRango: partner ? rangoEdad(partner.edad) : 'Sin dato',
      estado: partner ? (partner.estado || '(sin registrar)') : '(sin registrar)',
      profesion: partner ? partner.profesion : '(sin registrar)',
      actividad: partner ? partner.actividad : '(sin registrar)',
      ramo: partner ? partner.ramo : '',
    };
  });

  // ---------- 7) Resumenes agrupados ----------
  function resumen(filasBase, agrupador) {
    const o = {};
    filasBase.forEach(f => {
      const k = agrupador(f);
      const slot = o[k] || (o[k] = { llave: k, unidades: 0, monto: 0, pedidos: {}, clientes: new Set() });
      slot.unidades += f.unidades; slot.monto += f.montoSinIva; slot.pedidos[f.pedido] = 1; slot.clientes.add(f.clienteId || f.cliente);
    });
    return Object.values(o).map(s => ({ llave: s.llave, unidades: s.unidades, monto: Math.round(s.monto * 100) / 100, pedidos: Object.keys(s.pedidos).length, clientes: s.clientes.size }))
      .sort((a, b) => b.unidades - a.unidades || b.monto - a.monto);
  }
  const base = filas.map(f => ({ ...f, partner: undefined }));
  const res = {
    generado: new Date().toISOString(), fuente: 'latinbienmotors.com (BD latinbien), solo lectura', anio,
    total: { unidades: base.reduce((s, f) => s + f.unidades, 0).toFixed(2), monto: Math.round((base.reduce((s, f) => s + f.montoSinIva, 0)) * 100) / 100, pedidos: pedidos.length },
    porMes: resumen(base, f => f.mes || '(sin fecha)'),
    porForma: resumen(base, f => f.forma),
    facturacionClientes: {
      origen: 'account.move con etiqueta VENTAVEHICULOCONSIG (favorito "FacturacionVehiculo") - indiferente de entrega',
      alCorte: hoyISO,
      total: { unidades: Math.round(mTot.unidades * 100) / 100, monto: Math.round(mTot.monto * 100) / 100, facturas: factDetalle.length },
      porMes: Object.keys(mPorMes).sort().map(k => ({ llave: k, ...mPorMes[k], monto: Math.round(mPorMes[k].monto * 100) / 100, mEnt: Math.round(mPorMes[k].mEnt * 100) / 100, mNoEnt: Math.round(mPorMes[k].mNoEnt * 100) / 100, mSin: Math.round(mPorMes[k].mSin * 100) / 100 })),
      porStatus: Object.values(mPorStatus).map(s => ({ ...s, monto: Math.round(s.monto * 100) / 100 })).sort((a, b) => b.unidades - a.unidades),
      faltantes: faltantesPerfil,
      detalle: factDetalle,
    },
    contadoCRM: {
      origen: 'crm.lead etapa 12 "Facturado Contado" - latinbienmotors.com',
      leads: leadsContado.length,
      clientes: leadsContado.map(l => String(l.name || '').replace(/^Oportunidad de /i, '').trim()).filter(Boolean),
      unidadesContadoEntregadas: base.filter(f => f.forma === 'Contado').reduce((s, f) => s + f.unidades, 0),
    },
    porEstado: resumen(base, f => f.estado),
    porGenero: resumen(base, f => f.genero),
    porEdad: resumen(base, f => f.edadRango),
    porActividad: resumen(base, f => f.actividad),
    porProfesion: resumen(base, f => f.profesion),
    porRamo: resumen(base, f => f.ramo || '(sin registrar)'),
    detalle: base.map(({ partner, ...d }) => d),
    reservado: { alCorte: hoyISO, unidades: filasRes.length, detalle: filasRes },
    facturadoNoEntregado: { unidades: factNoEntregadas.reduce((s, u) => s + u.unidades, 0), detalle: factNoEntregadas },
  };
  // ordenar meses
  res.porMes.sort((a, b) => String(a.llave).localeCompare(String(b.llave)));

  fs.mkdirSync(DIR, { recursive: true });
  const ruta = path.join(DIR, `reporte_ventas_${hoyISO}.json`);
  fs.writeFileSync(ruta, JSON.stringify(res, null, 2));

  // ---------- 8) Consola ----------
  const fmt$ = n => '$ ' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const tabla = (t, titulo, esMes) => {
    console.log(`\n== ${titulo} ==`);
    console.log('llave | unidades | monto');
    t.forEach((r) => console.log(`${String(r.llave).padEnd(28)} | ${String(r.unidades).padStart(4)} | ${fmt$(r.monto)}`));
  };
  console.log(`\nTOTAL ${anio}: ${res.total.unidades} unidades vehiculo (Honda) - ${fmt$(res.total.monto)} sin IVA - ${res.total.pedidos} entregas`);
  tabla(res.porMes, 'Vendido por MES');
  tabla(res.porForma, 'Por FORMA DE VENTA');
  tabla(res.porGenero, 'Por GENERO (Dama/Caballero)');
  tabla(res.porEdad, 'Por EDAD');
  tabla(res.porEstado.slice(0, 15), 'Por ESTADO/DEPARTAMENTO (top 15)');
  tabla(res.porActividad, 'Por ACTIVIDAD');
  tabla(res.porProfesion.slice(0, 15), 'Por PROFESION (top 15)');
  console.log(`\n== RESERVADO (almacen Reservas RLBM), al corte ${hoyISO} ==`);
  console.log(`Unidades: ${res.reservado.unidades} | Facturado no entregado (FNE): ${res.facturadoNoEntregado.unidades}`);
  filasRes.forEach(f => console.log(`${f.vin.padEnd(20)} | ${f.modelo.slice(0, 38).padEnd(38)} | ${f.cliente.padEnd(34)} | ${f.genero} | ${f.edadRango} | ${f.estado}`));
  console.log('\nJSON completo: ' + ruta);
}

main().catch(e => { console.error('Error: ' + e.message); process.exit(1); });
