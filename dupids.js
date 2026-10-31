const h = require('fs').readFileSync('reporte/tablero_ventas.html', 'utf8');
const idMatches = h.match(/id=["']([^"']+)["']/g);
if (!idMatches) { console.log('No IDs found'); process.exit(0); }
const ids = idMatches.map(m => m.replace(/id=["']/,'').replace(/["]$/,''));
const unique = new Set(ids);
const duplicates = ids.filter((id, i) => ids.indexOf(id) !== i);
console.log('Total IDs:', ids.length);
console.log('Unique IDs:', unique.size);
console.log('Duplicate IDs:', duplicates.length > 0 ? duplicates : 'none');