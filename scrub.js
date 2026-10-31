var fs = require('fs');
var h = fs.readFileSync('reporte/tablero_ventas.html', 'utf8');
h = h.replace(/id="bMesesFact"/g, '');
h = h.replace(/id="tMesFact"/g, '');
h = h.replace(/bMesesFact/g, '');
h = h.replace(/tMesFact/g, '');
fs.writeFileSync('reporte/tablero_ventas.html', h, 'utf8');
console.log('HTML scrubbed');