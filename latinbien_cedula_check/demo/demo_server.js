const http = require('http');
const https = require('https');
const fs = require('fs');
const cred = JSON.parse(fs.readFileSync('C:/Users/yarleyc/.odoo-credentials.json', 'utf8'));
const HOST = cred.host, DB = cred.db, LOGIN = cred.login, PASS = cred.password;
let SESSION = null;

function post(path, body, cookie) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const headers = { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) };
    if (cookie) headers['Cookie'] = cookie;
    const req = https.request({ hostname: HOST, path, method: 'POST', headers, timeout: 120000 }, res => {
      let d = ''; res.on('data', c => d += c);
      res.on('end', () => { let j = {}; try { j = JSON.parse(d); } catch (e) {} resolve({ status: res.statusCode, headers: res.headers, body: j, raw: d }); });
    });
    req.on('error', reject); req.on('timeout', () => req.destroy(new Error('timeout')));
    req.write(data); req.end();
  });
}

async function getSession() {
  if (SESSION) return SESSION;
  const r = await post('/web/session/authenticate', { jsonrpc: '2.0', method: 'call', params: { db: DB, login: LOGIN, password: PASS }, id: 1 });
  if (!r.body || !r.body.result || !r.body.result.uid) throw new Error('auth falló');
  SESSION = ((r.headers['set-cookie'] || []).find(x => x.startsWith('session_id=')) || '').split(';')[0];
  return SESSION;
}

async function rpc(model, method, args, kwargs) {
  const sid = await getSession();
  const r = await post('/web/dataset/call_kw/' + model + '/' + method, { jsonrpc: '2.0', method: 'call', params: { model, method, args: args || [], kwargs: kwargs || {} }, id: 2 }, sid);
  if (r.body.error) throw new Error(r.body.error.data ? r.body.error.data.message : r.body.error.message);
  return r.body.result;
}

function candidates(ident, num) {
  const id = String(ident || '').toUpperCase().replace(/[^A-Z]/g, '').slice(0, 1);
  const digits = String(num || '').replace(/\D/g, '');
  if (!id || !digits) return [];
  const nz = digits.replace(/^0+/, '') || '0';
  const out = new Set([id + nz, id + digits]);
  [8, 9, 10].forEach(w => out.add(id + nz.padStart(w, '0')));
  return [...out];
}

async function check(ident, num) {
  const cands = candidates(ident, num);
  if (!cands.length) return 'no_existe';
  const r = await rpc('res.partner', 'search_read', [[['vat', 'in', cands]]], { fields: ['x_activacion_linea', 'x_credit_limit_aprobado'], limit: 1 });
  if (!r.length) return 'no_existe';
  const activa = r[0].x_activacion_linea === true || (r[0].x_credit_limit_aprobado > 0);
  return activa ? 'existe_con_linea' : 'existe_sin_linea';
}

const HTML = [
  '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
  '<title>Demo - Verificación de Cédula</title>',
  '<style>body{font-family:Arial,sans-serif;max-width:560px;margin:40px auto;padding:0 16px;color:#333}',
  '.s_website_form_field{margin-bottom:16px}label{display:block;font-weight:600;margin-bottom:6px}',
  'input,select{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;box-sizing:border-box}',
  '.row{display:flex;gap:10px}.row select{width:90px}</style></head><body>',
  '<h2 style="color:#213C83">Solicita tu crédito</h2>',
  '<p style="color:#666">Demo local (consulta Odoo en solo lectura, no guarda nada).</p>',
  '<form id="f">',
  '<div class="s_website_form_field"><label>Cédula / RIF *</label><div class="row">',
  '<select name="x_indentificador_rif"><option value="V">V</option><option value="E">E</option><option value="J">J</option><option value="G">G</option></select>',
  '<input type="text" name="x_contenido_rif" placeholder="Ej: 27018323" inputmode="numeric"></div></div>',
  '<div class="s_website_form_field"><label>Nombre y apellido *</label><input name="contact_name" type="text"></div>',
  '<div class="s_website_form_field"><label>Teléfono *</label><input name="phone" type="text"></div>',
  '<div class="s_website_form_field"><label>¿Cuánto dinero tienes disponible para la inicial? *</label><input name="x_inicial_disponible_moto" type="text"></div>',
  '<div class="s_website_form_field"><label>Profesión u Oficio *</label><input name="x_profesion" type="text"></div>',
  '<button type="button" style="background:#213C83;color:#fff;border:0;padding:12px 22px;border-radius:8px;font-weight:700">Enviar solicitud</button>',
  '</form>',
  '<script>',
  "(function(){var T={existe_con_linea:['#e7f5e9','#1b5e20','¡Ya eres cliente con una línea de crédito activa! Un asesor te contactará para ayudarte.'],existe_sin_linea:['#e8f0fe','#174ea6','Ya te conocemos. Completa tu solicitud para continuar con tu evaluación.'],no_existe:['#f8f9fa','#495057','Continúa con tu solicitud para iniciar tu evaluación de crédito.']};",
  "function rpc(i,n){return fetch('/api/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ident:i,num:n})}).then(function(r){return r.json()}).then(function(j){return j.estado}).catch(function(){return 'error'})}",
  "var numEl=document.querySelector('[name=\"x_contenido_rif\"]'),identEl=document.querySelector('[name=\"x_indentificador_rif\"]');",
  "var form=document.getElementById('f'),numWrap=numEl.closest('.s_website_form_field');",
  "var fields=[].slice.call(form.querySelectorAll('.s_website_form_field'));",
  "var b=document.createElement('div');b.style.display='none';b.style.padding='14px 16px';b.style.borderRadius='10px';b.style.margin='0 0 16px';b.style.fontWeight='600';b.style.lineHeight='1.4';numWrap.parentNode.insertBefore(b,numWrap);",
  "var link=document.createElement('a');link.href='#';link.textContent='Mostrar formulario';link.style.marginLeft='6px';link.style.textDecoration='underline';",
  "function vis(v){fields.forEach(function(f){if(f===numWrap)return;f.style.display=v?'':'none'})}",
  "function show(e){if(e==='rate_limited'||e==='error'){b.style.display='none';vis(true);return}var t=T[e];if(!t)return;b.style.display='block';b.style.background=t[0];b.style.color=t[1];b.textContent=t[2];if(e==='existe_con_linea'){vis(false);b.appendChild(link)}else{vis(true)}}",
  "link.addEventListener('click',function(ev){ev.preventDefault();vis(true);b.style.display='none'});",
  "var timer=null;function run(){var n=(numEl.value||'').replace(/\\D/g,'');if(n.length<6){b.style.display='none';vis(true);return}rpc(identEl.value,n).then(show)}",
  "function sched(){clearTimeout(timer);timer=setTimeout(run,600)}",
  "numEl.addEventListener('blur',sched);numEl.addEventListener('change',sched);identEl.addEventListener('change',sched);",
  "})();",
  '<\/script></body></html>',
].join('\n');

http.createServer((req, res) => {
  if (req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(HTML);
    return;
  }
  if (req.method === 'POST' && req.url === '/api/check') {
    let d = '';
    req.on('data', c => d += c);
    req.on('end', async () => {
      try {
        const b = JSON.parse(d || '{}');
        const estado = await check(b.ident, b.num);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ estado }));
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }
  res.writeHead(404); res.end('not found');
}).listen(8799, '127.0.0.1', () => console.log('Demo en http://localhost:8799'));
