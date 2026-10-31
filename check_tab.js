const fs = require('fs');
const h = fs.readFileSync('reporte/tablero_ventas.html', 'utf8');

// Check for pPerfil panel
const pPerfilPanel = h.indexOf('<div class="tab-panel" id="pPerfil"');
console.log('pPerfil panel index:', pPerfilPanel);

// Check for kpis inside pPerfil
if (pPerfilPanel >= 0) {
  const pPerfilSection = h.substring(pPerfilPanel, pPerfilPanel + 600);
  console.log('pPerfil has kpis:', pPerfilSection.includes('<div class="kpis"'));
  console.log('pPerfil has hEdad:', pPerfilSection.includes('hEdad'));
  console.log('pPerfil has hGenero:', pPerfilSection.includes('hGenero'));
}

// Check tab buttons
const tabBtns = h.match(/tab-btn[^>]*>/g);
console.log('tab buttons found:', tabBtns ? tabBtns.length : 0);
if (tabBtns) {
  tabBtns.forEach((btn, i) => {
    console.log('btn' + i + ':', btn.substring(0, 80));
  });
}

// Check if pFactu is active by default
const pFactuActive = h.match(/tab-btn active[^>]*data-tab="pFactu"/);
console.log('pFactu initially active:', pFactuActive ? 'yes' : 'no');

// Check pPerfil initially active
const pPerfilActive = h.match(/tab-btn active[^>]*data-tab="pPerfil"/);
console.log('pPerfil initially active:', pPerfilActive ? 'yes' : 'no');

// Check the script section
const scriptStart = h.indexOf('<script>');
const scriptEnd = h.lastIndexOf('</script>');
if (scriptStart >= 0 && scriptEnd > scriptStart) {
  const script = h.substring(scriptStart, scriptEnd);
  console.log('\\nScript length:', script.length);
  console.log('Script contains tab handler:', script.includes('addEventListener'));
  // Extract just the tab switching part
  const tabSwitchMatch = script.match(/document\.querySelectorAll\(['"]\\.tab-btn['"]\)[\s\S]{0,500}/);
  if (tabSwitchMatch) {
    console.log('\\nTab switch code:', tabSwitchMatch[0].substring(0, 300));
  }
}