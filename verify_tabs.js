const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
console.log('pPerfil presente:', h.includes('pPerfil'));
console.log('pFactu presente:', h.includes('pFactu'));
console.log('data-tab pFactu:', h.includes('data-tab="pFactu"'));
console.log('data-tab pPerfil:', h.includes('data-tab="pPerfil"'));
// Check for active class on tab buttons
const activeBtnMatch = h.match(/tab-btn active.*data-tab=/);
console.log('botón activo:', activeBtnMatch ? activeBtnMatch[0] : 'ninguno');
// Check for active panel
const activePanelMatch = h.match(/tab-panel active.*id=/);
console.log('panel activo:', activePanelMatch ? activePanelMatch[0] : 'ninguno');
// Check panel contents
console.log('hEdad en pPerfil:', h.includes('hEdad'));
console.log('hGenero en pPerfil:', h.includes('hGenero'));