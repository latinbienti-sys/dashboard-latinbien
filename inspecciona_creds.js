const fs = require('fs');
const os = require('os');
const path = require('path');
['odoo-credentials-motors.json', '.odoo-credentials-motors.json', 'odoo-credentials-lbm.json', 'odoo-credentials-web.json'].forEach(n => {
  const p = path.join(os.homedir(), n);
  if (fs.existsSync(p)) {
    try {
      const c = JSON.parse(fs.readFileSync(p, 'utf8'));
      console.log(n, '-> claves:', Object.keys(c).join(','), '| host:', c.host || '-', '| db:', c.db || '-', '| login:', (c.login || '(sin login)'));
    } catch (e) { console.log(n, '-> ERROR parseo:', e.message.slice(0, 80)); }
  } else console.log(n, '-> no existe');
});
