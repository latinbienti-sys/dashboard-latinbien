const fs = require('fs');
const h = fs.readFileSync('reporte/tablero_ventas.html', 'utf8');
const s = h.indexOf('<script>');
const e = h.lastIndexOf('</script>');
const code = h.substring(s, e);

console.log('Script found, length:', code.length);
console.log('Has addEventListener:', code.includes('addEventListener'));
console.log('Has querySelectorAll:', code.includes('querySelectorAll'));
console.log('Has classList:', code.includes('classList'));
console.log('Has forEach:', code.includes('forEach'));

// Check the tab switching function specifically
const tabSwitchStart = code.indexOf('document.querySelectorAll');
if (tabSwitchStart >= 0) {
  console.log('\\nTab switch code found at index:', tabSwitchStart);
  console.log('Code around tab switch:');
  console.log(code.substring(tabSwitchStart, tabSwitchStart + 400));
}