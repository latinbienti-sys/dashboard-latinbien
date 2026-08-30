const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://localhost/pinturaschacao/pinturas-chacao.preview.emergentagent.com/index2f20.html', { waitUntil: 'networkidle', timeout: 30000 });
  
  // Wait for JS to execute
  await page.waitForTimeout(3000);
  
  // Full page screenshot
  await page.screenshot({ path: 'C:/Users/yarleyc/Documents/New OpenCode Project/screenshot-full.png', fullPage: true });
  
  // Scroll to the Color Studio section and screenshot
  await page.evaluate(() => {
    const el = document.getElementById('comparativos');
    if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
  });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'C:/Users/yarleyc/Documents/New OpenCode Project/screenshot-visualizador.png' });
  
  // Check for JS errors
  const paletteHTML = await page.evaluate(() => {
    const palette = document.getElementById('color-palette');
    return palette ? palette.innerHTML.substring(0, 200) : 'NOT FOUND';
  });
  console.log('Palette content:', paletteHTML);
  
  const wallZones = await page.evaluate(() => {
    const zones = document.querySelectorAll('.wall-zone');
    return zones.length;
  });
  console.log('Wall zones found:', wallZones);
  
  const wallPaints = await page.evaluate(() => {
    const paints = document.querySelectorAll('.wall-paint');
    return Array.from(paints).map(p => ({ id: p.id, fill: p.getAttribute('fill'), opacity: p.getAttribute('opacity') }));
  });
  console.log('Wall paints:', JSON.stringify(wallPaints));
  
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  
  await browser.close();
  console.log('Screenshots saved!');
})();
