const fs = require('fs');
let h = fs.readFileSync('reporte/tablero_ventas.html', 'utf8');

// Remover referencias al gráfico Facturado por mes que quedaron colgantes
h = h.replace(/id="bMesesFact"/g, '');
h = h.replace(/id="tMesFact"/g, '');
h = h.replace(/bMesesFact/g, '');
h = h.replace(/tMesFact/g, '');

// Also remove any leftover "Facturado por mes" text variations
h = h.replace(/Facturado por mes \(fecha de factura\)/g, '');
h = h.replace(/Facturado por mes y status/g, '');

fs.writeFileSync('reporte/tablero_ventas.html', h, 'utf8');
console.log('HTML limpiado. Guardado.');