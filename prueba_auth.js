const fs = require('fs');
const os = require('os');
const path = require('path');
(async () => {
  const c = JSON.parse(fs.readFileSync(path.join(os.homedir(), 'odoo-credentials-motors.json'), 'utf8'));
  const r = await fetch('https://latinbienmotors.com/web/session/authenticate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { db: c.db || 'latinbien', login: c.login, password: c.password }, id: 1 }),
  });
  const j = await r.json();
  console.log('HTTP', r.status, '| uid:', (j.result && j.result.uid) || '(ninguno)', '| nombre:', (j.result && j.result.name) || '');
  if (j.error) console.log('error:', j.error.message);
})().catch(e => console.error('ERR', e.message));
