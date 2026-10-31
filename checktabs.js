const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
// Verificar estructura de pestañas
const tabs = [
  'data-tab="pFactu"',
  'data-tab="pPerfil"',
  'data-tab="pReservadas"',
  'data-tab="pDetalle"'
];
tabs.forEach(t => {
  console.log(t + ':', h.includes(t));
});
// Verificar botones activos
console.log('\\nBotón activo:', h.match(/tab-btn active["\']?[^>]*>/)?.[0] || 'ninguno');
// Verificar panel activo
console.log('Panel activo:', h.match(/tab-panel active["\']?[^>]*>/)?.[0] || 'ninguno');