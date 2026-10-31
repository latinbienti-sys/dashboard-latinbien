const fs = require('fs');

let content = fs.readFileSync('generar_tablero.js', 'utf8');
const lines = content.split('\n');

// Encontrar e eliminar las líneas del gráfico Facturado por mes
// Queremos eliminar:
// - Línea 125: <div class="card"> (o la que tiene h3 Facturado por mes)
// - Línea 126: <h3>Facturado por mes (fecha de factura) — unidades y monto sin IVA, indiferente de entrega</h3>
// - Línea 127: <div class="bars" id="bMesesFact"></div>
// - Línea 128: </div>
// - Línea 129: <div class="card"><h3>Facturado por mes (fecha de factura)</h3>
// - Línea 130: <table><thead><tr><th>Mes</th><th>Vehículos</th><th>Monto sin IVA</th></tr></thead>
// - Línea 131: <tbody id="tMesFact"></tbody></table>
// - Línea 132: <div class="mini" style="margin-top:8px">Fuente: Facturación Clientes con etiqueta VENTAVEHICULOCONSIG = favorito "FacturacionVehiculo" en Odoo. Indiferente de entrega.</div>
// - Línea 133: </div>

let newLines = [];
let skipUntil = -1; // Índice hasta donde saltar (inclusive)

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  
  // Marcar para comenzar a saltar después de la línea con el h3 de "Facturado por mes"
  if (skipUntil >= 0) {
    if (i <= skipUntil) {
      continue; // Saltar esta línea
    } else {
      skipUntil = -1; // Ya no estamos en modo saltar
    }
  }
  
  // Detectar la línea que inicia el bloque a eliminar: la tarjeta con h3 "Facturado por mes"
  if (line.includes('Facturado por mes (fecha de factura) — unidades y monto sin IVA, indiferente de entrega') || 
      line.includes('Facturado por mes (fecha de factura)</h3>')) {
    skipUntil = i + 4; // Saltar esta línea y las siguientes hasta que termine el bloque
    continue; // No agregar esta línea
  }
  
  // Alternativamente, detectar por el patrón del div bars
  if (line.includes('id="bMesesFact"') && skipUntil === -1) {
    // Este es el inicio del bloque a eliminar
    skipUntil = i + 8; // Saltar un poco más amplio
    continue;
  }
  
  // Si estamos en el rango known a eliminar basado en el número de línea aproximadamente
  // Líneas originales: 125-133 son el bloque a eliminar (aproximado)
  // Vamos a usar un enfoque diferente: saltar desde que vemos el primer h3 de "Facturado" hasta después del div mini
  
  newLines.push(line);
}

fs.writeFileSync('generar_tablero.js', newLines.join('\n'), 'utf8');
console.log('Limpieza completada. Líneas nuevas:', newLines.length);