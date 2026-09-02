const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://localhost/pinturaschacao/pinturas-chacao.preview.emergentagent.com/index2f20.html', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  
  // Screenshot 1: Hero
  await page.screenshot({ path: 'C:/Users/yarleyc/Documents/New OpenCode Project/ss-1-hero.png' });
  
  // Scroll to Color Studio / comparativos
  await page.evaluate(() => {
    const el = document.getElementById('comparativos');
    if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
  });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'C:/Users/yarleyc/Documents/New OpenCode Project/ss-2-visualizador.png' });
  
  // Scroll down more to see the color palette
  await page.evaluate(() => window.scrollBy(0, 500));
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'C:/Users/yarleyc/Documents/New OpenCode Project/ss-3-paleta.png' });
  
  // Check what's actually on the page
  const info = await page.evaluate(() => {
    const palette = document.getElementById('color-palette');
    const wallPaints = document.querySelectorAll('.wall-paint');
    const wallZones = document.querySelectorAll('.wall-zone');
    const comparativos = document.getElementById('comparativos');
    return {
      paletteExists: !!palette,
      paletteChildCount: palette ? palette.children.length : 0,
      paletteHTML: palette ? palette.innerHTML.substring(0, 300) : 'NOT FOUND',
      wallPaintCount: wallPaints.length,
      wallZoneCount: wallZones.length,
      comparativosExists: !!comparativos,
      comparativosOffsetTop: comparativos ? comparativos.offsetTop : 0,
      rootContent: document.getElementById('root') ? document.getElementById('root').innerHTML.substring(0, 200) : 'EMPTY'
    };
  });
  console.log('Page info:', JSON.stringify(info, null, 2));
  
  await browser.close();
})();
