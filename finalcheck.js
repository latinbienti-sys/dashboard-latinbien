const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
const checks = {
  'addEventListener': h.includes('addEventListener'),
  'data-tab pPerfil': h.includes('data-tab="pPerfil"'),
  'id pPerfil': h.includes('id="pPerfil"'),
  'tab-panel active': h.includes('tab-panel active'),
  'tab-btn active': h.match(/tab-btn active/) ? 'yes' : 'no'
};
Object.entries(checks).forEach(([k, v]) => console.log(k + ':', v));