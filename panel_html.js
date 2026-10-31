const fs = require('fs');
const h = fs.readFileSync('reporte/tablero_ventas.html', 'utf8');
const s = h.indexOf('<div class="tab-panel" id="pPerfil"');
if (s >= 0) {
  console.log(h.substring(s, s + 500));
} else {
  console.log('pPerfil panel not found');
}