const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
const s = h.indexOf('<div class="tab-panel active" id="pPerfil"');
if (s >= 0) {
  console.log(h.substring(s, s + 600));
} else {
  console.log('active panel not found');
}