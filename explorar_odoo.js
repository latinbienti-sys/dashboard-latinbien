#!/usr/bin/env node
// Exploracion SOLO LECTURA del Odoo de Latinbien (misma conexion que coach-comercial).
// Uso:
//   node explorar_odoo.js filtros <modelo> [texto]      -> favoritos/filtros guardados de un modelo
//   node explorar_odoo.js campos <modelo> [palabras...] -> campos de un modelo (filtra por palabras)
//   node explorar_odoo.js muestra <modelo> <dominio> <n> -> registro de ejemplo ("[]" con JSON)
//   node explorar_odoo.js cuenta <modelo> <dominio>      -> search_count
//
// Solo metodos de lectura. Credenciales via ~/.odoo-credentials.json (no se imprimen).

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const METODOS_PERMITIDOS = new Set(['search_read', 'read', 'fields_get', 'search_count']);

function credenciales() {
  const DEBUG = process.env.DEBUG_RPC === '1';
  let c = {};
  let archivo = null;
  // Preferencia: Motors (con y sin punto al inicio) -> base. Sin mezclar usuarios.
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
    // El archivo de credenciales manda sobre el entorno (evita cruzar instancias)
    db: c.db || process.env.ODOO_DB || 'latinbien',
    login: c.login || process.env.ODOO_USER,
    password: c.password || process.env.ODOO_PASS,
  };
  if (!cfg.login || !cfg.password) throw new Error('Faltan credenciales');
  if (DEBUG) console.error('>> archivo usado:', archivo, '| login:', cfg.login, '| db:', cfg.db, '| url:', cfg.url);
  return cfg;
}

async function conectar() {
  const cfg = credenciales();
  let cookie = '';
  const DEBUG = process.env.DEBUG_RPC === '1';
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
    if (j.error) {
      if (DEBUG) console.error('<< error detalles:', JSON.stringify(j.error).slice(0, 500));
      throw new Error((j.error.data && j.error.data.message) || j.error.message);
    }
    return j.result;
  };
  const auth = await rpc('/web/session/authenticate', { db: cfg.db, login: cfg.login, password: cfg.password });
  if (!auth || !auth.uid) throw new Error('No se pudo iniciar sesion en Odoo');
  const llamar = (model, method, args = [], kwargs = {}) => {
    if (!METODOS_PERMITIDOS.has(method)) throw new Error(`Metodo bloqueado (solo lectura): ${method}`);
    return rpc('/web/dataset/call_kw', { model, method, args, kwargs });
  };
  return { llamar };
}

const dominioPython = s => {
  let out = '', i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === "'" || c === '"') {
      let j = i + 1, val = '';
      while (j < s.length && s[j] !== c) { if (s[j] === '\\') { val += s[j + 1]; j += 2; } else val += s[j++]; }
      out += JSON.stringify(val); i = j + 1;
    } else if (c === '(') { out += '['; i++; }
    else if (c === ')') { out += ']'; i++; }
    else if (/[A-Za-z_]/.test(c)) {
      const m = s.slice(i).match(/^[A-Za-z_][A-Za-z0-9_.]*/)[0];
      const lit = { True: 'true', False: 'false', None: 'null' }[m];
      if (!lit) throw new Error('dominio con expresion: ' + m);
      out += lit; i += m.length;
    } else { out += c; i++; }
  }
  return JSON.parse(out.replace(/,\s*\]/g, ']'));
};

(async () => {
  const { llamar } = await conectar();
  const [cmd, model, ...resto] = process.argv.slice(2);

  if (cmd === 'filtros') {
    const texto = resto[0] || '';
    const dom = [['model_id', '=', model]];
    if (texto) dom.push(['name', 'ilike', texto]);
    const favs = await llamar('ir.filters', 'search_read', [dom, ['name', 'domain', 'context', 'is_default']]);
    favs.sort((a, b) => a.name.localeCompare(b.name));
    favs.forEach(f => console.log(`\n== ${f.name}${f.is_default ? ' (por defecto)' : ''}\n   dominio: ${f.domain}\n   contexto: ${f.context}`));
    return;
  }

  if (cmd === 'campos') {
    const palabras = resto.filter(Boolean).map(p => p.toLowerCase());
    const fg = await llamar(model, 'fields_get', [], { attributes: ['type', 'string', 'selection', 'relation'] });
    const nombres = Object.keys(fg);
    const sel = c => (fg[c].selection || []).map(o => `${o[0]}=${o[1]}`).join(' | ');
    const elegir = palabras.length
      ? nombres.filter(n => palabras.some(p => (n + ' ' + (fg[n].string || '')).toLowerCase().includes(p)))
      : nombres;
    elegir.sort();
    elegir.forEach(n => console.log(`${n} [${fg[n].type}] ${fg[n].string || ''}${fg[n].relation ? ' -> ' + fg[n].relation : ''}${fg[n].selection ? ' :: ' + sel(n) : ''}`));
    console.log(`\n(${elegir.length} de ${nombres.length} campos)`);
    return;
  }

  if (cmd === 'muestra') {
    const dominio = dominioPython(resto[0] || '[]');
    const n = Number(resto[1] || 3);
    const campos = resto[2] ? resto[2].split(',').filter(Boolean) : undefined;
    const regs = await llamar(model, 'search_read', [dominio], { limit: n, fields: campos });
    console.log(JSON.stringify(regs, null, 2));
    return;
  }

  if (cmd === 'cuenta') {
    const dominio = dominioPython(resto[0] || '[]');
    console.log(await llamar(model, 'search_count', [dominio]));
    return;
  }

  console.log('Uso: node explorar_odoo.js filtros|campos|muestra|cuenta ...');
})().catch(e => { console.error('Error: ' + e.message); process.exit(1); });
