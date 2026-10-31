const fs = require('fs');
const h = fs.readFileSync('reporte/tablero_ventas.html', 'utf8');

// Find tab buttons
const btns = [];
let i = 0;
while (true) {
  const idx = h.indexOf('data-tab="pFactu"', i);
  if (idx === -1) break;
  btns.push({idx, type: 'pFactu'});
  i = idx + 1;
}
i = 0;
while (true) {
  const idx = h.indexOf('data-tab="pPerfil"', i);
  if (idx === -1) break;
  btns.push({idx, type: 'pPerfil'});
  i = idx + 1;
}
// ... etc

// Show first 400 chars of tab section
const tabsStart = h.indexOf('<!-- Pestañas -->');
console.log('Tab section start:', tabsStart);
console.log('Tabs HTML:', h.substring(tabsStart, tabsStart + 150));
console.log('\\nFirst button class check:', h.substring(tabsStart + 18, tabsStart + 50));

// Check for the script that handles tabs
const scriptStart = h.indexOf('<script>');
console.log('Script start at:', scriptStart);

// Show the tab switch script
const scriptContent = h.substring(h.indexOf('document.querySelectorAll'), h.indexOf('</script>'));
console.log('Tab switch script:', scriptContent.substring(0, 500));