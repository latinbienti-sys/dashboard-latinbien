const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
const checks = ['bMesesFact', 'tMesFact', 'Facturado por mes', 'id="hForma"', 'Forma de venta', 'pendientes de entrega'];
checks.forEach(k => { console.log(k + ':', h.includes(k)); });