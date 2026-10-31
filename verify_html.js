const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
const checks = {
  'pFactu panel': h.includes('id="pFactu"'),
  'no pPerfil data-tab': !h.includes('data-tab="pPerfil"'),
  'no pReservadas data-tab': !h.includes('data-tab="pReservadas"'),
  'no pDetalle data-tab': !h.includes('data-tab="pDetalle"'),
  'hGenero presente': h.includes('hGenero'),
  'hEdad presente': h.includes('hEdad'),
  'hEstado presente': h.includes('hEstado'),
  'hForma presente': h.includes('id="hForma"'),
  'KPI 59 unidades': h.match(/<div class="kpi"><div class="v">59<\/div>/),
  'KPI $1.891.076': h.includes('$ 1,891,076.96'),
  'tab-btn oculto por CSS': h.includes('tab-btn{display:none}') || h.match(/display:none.*tab-btn/)
};
Object.entries(checks).forEach(([k, v]) => console.log(k + ':', v ? '✅' : '❌'));