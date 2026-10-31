const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
console.log('pPerfil tab index:', h.indexOf('id="pPerfil"'));
console.log('hEdad presente:', h.includes('hEdad'));
console.log('hGenero presente:', h.includes('hGenero'));
// Check for the panel div
const pPerfilMatch = h.match(/<div class="tab-panel" id="pPerfil">[\s\S]{0,500}/);
if (pPerfilMatch) {
  console.log('\\npPerfil panel snippet:', pPerfilMatch[0].substring(0, 200));
}