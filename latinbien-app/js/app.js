/* ============================================================
   LatinBien App — Main Application Logic v2.0
   Mejoras: imágenes Odoo, offline, auth-guard, Club completo
   ============================================================ */

const APP = (() => {
  'use strict';

  // ========================================================================
  //  S T A T E
  // ========================================================================
  let _currentPage = 'home';
  let _categories = [];
  let _products = [];
  let _orders = [];
  let _creditLines = [];
  let _online = navigator.onLine;
  let _searchTimeout = null;
  let _cart = [];       // Carrito: [{id, name, price, image, qty}]
  let _pushSubscribed = false;

  // ========================================================================
  //  D O M   H E L P E R S
  // ========================================================================
  const $ = s => document.querySelector(s);
  const $$ = s => document.querySelectorAll(s);

  // ========================================================================
  //  I N I T
  // ========================================================================
  async function init() {
    AUTH.init();

    // Detectar cambios de conectividad
    window.addEventListener('online', () => { _online = true; });
    window.addEventListener('offline', () => {
      _online = false;
      showToast('📡 Sin conexión — mostrando datos en caché', 'warning');
    });

    // Registrar Service Worker
    if ('serviceWorker' in navigator) {
      try {
        const reg = await navigator.serviceWorker.register('sw.js');
        // Intentar suscribir a push notifications
        setupPushNotifications(reg);
      } catch (_) { /* no hay SW en file:// */ }
    }

    // Cargar carrito desde localStorage
    loadCart();

    // Verificar sesión contra Odoo
    const sessionUser = await AUTH.checkSession();
    if (sessionUser) {
      showApp();
      loadHomeData();
    } else {
      showLogin();
    }

    setupListeners();
  }

  // ========================================================================
  //  U I   T O G G L E S
  // ========================================================================
  function showLogin() {
    $('#loginScreen').style.display = 'flex';
    $('#appShell').style.display = 'none';
  }

  function showApp() {
    $('#loginScreen').style.display = 'none';
    $('#appShell').style.display = 'block';
  }

  function showLoading(containerId) {
    const el = $(`#${containerId}`);
    if (el) el.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
  }

  // ========================================================================
  //  T O A S T
  // ========================================================================
  function showToast(message, type = 'info') {
    const container = $('#toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('out');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  // ========================================================================
  //  A U T H   H A N D L E R S
  // ========================================================================
  async function handleLogin(e) {
    e.preventDefault();
    const email = $('#loginEmail').value.trim();
    const password = $('#loginPassword').value;
    const btn = $('#loginBtn');

    if (!email || !password) {
      showToast('Ingresa tu correo y contraseña', 'warning');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Ingresando…';

    try {
      await AUTH.login(email, password);
      showApp();
      // Resetear formulario
      $('#loginEmail').value = '';
      $('#loginPassword').value = '';
      btn.disabled = false;
      btn.textContent = 'Ingresar';
      loadHomeData();
      showToast('🎉 ¡Bienvenido a LatinBien!', 'success');
    } catch (err) {
      showToast(err.message || 'Error al iniciar sesión', 'error');
      btn.disabled = false;
      btn.textContent = 'Ingresar';
    }
  }

  async function handleLogout() {
    if (!confirm('¿Cerrar sesión?')) return;
    await AUTH.logout();
    showLogin();
    showToast('Sesión cerrada', 'warning');
  }

  // ========================================================================
  //  N A V I G A T I O N
  // ========================================================================
  function navigate(page) {
    if (page === _currentPage) return;

    // Rutas protegidas (requieren auth)
    const protectedPages = ['orders', 'profile'];
    if (protectedPages.includes(page) && !AUTH.isAuthenticated()) {
      showToast('🔒 Inicia sesión para ver esta sección', 'warning');
      return;
    }

    $$('.page').forEach(p => p.classList.remove('active'));

    const targetId = `page${page.charAt(0).toUpperCase()}${page.slice(1)}`;
    const target = $(`#${targetId}`);
    if (target) {
      target.classList.add('active');
      _currentPage = page;
    } else {
      $('#pageHome').classList.add('active');
      _currentPage = 'home';
    }

    // Tab bar sync
    $$('.tab-item').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.page === _currentPage);
    });

    // Cargar datos on-demand
    switch (_currentPage) {
      case 'home': loadHomeData(); break;
      case 'catalog': loadCatalog(); break;
      case 'credit': loadCreditData(); break;
      case 'club': loadClubData(); break;
      case 'profile': loadProfile(); break;
      case 'orders': loadOrders(); break;
      case 'cart': renderCartPage(); break;
      case 'payment': renderPaymentPage(); break;
    }
  }

  // ========================================================================
  //  P R O D U C T O S   —   R E N D E R
  // ========================================================================
  function renderProducts(containerId, products) {
    const container = $(`#${containerId}`);
    if (!container) return;

    if (!products || products.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1;">
          <div class="empty-icon">📦</div>
          <h3>No hay productos disponibles</h3>
          <p>Visita nuestro catálogo en línea</p>
          <a href="https://latinbien.com/shop" class="btn btn-primary btn-sm" style="margin-top:12px;" target="_blank" rel="noopener">Ir al catálogo</a>
        </div>`;
      return;
    }

    let html = '';
    products.forEach(p => {
      const price = p.list_price ? `$${Number(p.list_price).toFixed(2)}` : 'Consultar';
      const imgUrl = API.getProductImageUrl(p.id);
      const productUrl = p.website_url || `https://latinbien.com/shop/product/${p.id}`;
      const fallbackSvg = `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="#f3f4f6" width="100" height="100"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="30">📦</text></svg>')}`;

      html += `
        <div class="product-card">
          <a href="${productUrl}" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;display:block;">
            <img class="product-image" src="${imgUrl}" alt="${p.name.replace(/"/g, '&quot;')}" loading="lazy"
                 onerror="this.src='${fallbackSvg}'">
            <div class="product-info">
              <div class="product-name">${p.name}</div>
              <div class="product-price">${price}</div>
              ${p.default_code ? `<div class="product-sku">Cód: ${p.default_code}</div>` : ''}
            </div>
          </a>
          <button class="add-to-cart-btn" onclick="event.stopPropagation();APP.addToCart({id:${p.id},name:'${p.name.replace(/'/g,"\\'")}',list_price:${p.list_price||0}})" title="Agregar al carrito">+</button>
        </div>`;
    });
    container.innerHTML = html;
  }

  function renderMockProducts(containerId = 'featuredProducts', prefix = '') {
    const mock = [
      { id: 1, name: `${prefix}Laptop HP 15-dy5885wm`, list_price: 899.99, default_code: 'LAP-HP-001' },
      { id: 2, name: `${prefix}iPhone 15 Pro Max 256GB`, list_price: 1299.99, default_code: 'APP-IP15' },
      { id: 3, name: `${prefix}TV Samsung 55" 4K UHD`, list_price: 649.99, default_code: 'TV-SAM-55' },
      { id: 4, name: `${prefix}AirPods Pro 2da Gen`, list_price: 249.99, default_code: 'APP-AP2' },
      { id: 5, name: `${prefix}Monitor LG 27" IPS`, list_price: 329.99, default_code: 'MON-LG-27' },
      { id: 6, name: `${prefix}Teclado Mecánico Redragon`, list_price: 89.99, default_code: 'TEC-RED' },
    ];
    renderProducts(containerId, mock);
  }

  // ========================================================================
  //  H O M E
  // ========================================================================
  async function loadHomeData() {
    try {
      const cats = await API.getCategories();
      _categories = cats || [];
      renderHomeCategories();

      const products = await API.getFeaturedProducts(10);
      _products = products || [];
      renderProducts('featuredProducts', _products);
    } catch (err) {
      console.warn('Home fallback a mock:', err.message);
      renderHomeCategoriesFallback();
      renderMockProducts('featuredProducts');
    }
    // Siempre intentar crédito (silencioso si falla)
    loadCreditSummary();
  }

  function renderHomeCategories() {
    const container = $('#homeCategories');
    if (!container || _categories.length === 0) {
      renderHomeCategoriesFallback();
      return;
    }
    let html = '<button class="category-pill active" onclick="APP.filterByCategory(0)">🌟 Todo</button>';
    _categories.slice(0, 8).forEach(c => {
      html += `<button class="category-pill" onclick="APP.filterByCategory(${c.id})">${c.name}</button>`;
    });
    container.innerHTML = html;
  }

  function renderHomeCategoriesFallback() {
    const container = $('#homeCategories');
    if (!container) return;
    container.innerHTML = `
      <button class="category-pill active" onclick="APP.filterByCategory(0)">🌟 Todo</button>
      <button class="category-pill" onclick="APP.filterByCategory(0)">💻 Tecnología</button>
      <button class="category-pill" onclick="APP.filterByCategory(0)">📺 TV</button>
      <button class="category-pill" onclick="APP.filterByCategory(0)">📱 Celulares</button>
      <button class="category-pill" onclick="APP.filterByCategory(0)">🏠 Hogar</button>
    `;
  }

  function filterByCategory(categoryId) {
    $$('#homeCategories .category-pill').forEach(p => {
      const oc = p.getAttribute('onclick') || '';
      p.classList.toggle('active', oc.includes(`(${categoryId})`));
    });
    if (categoryId === 0) { renderProducts('featuredProducts', _products); return; }
    const filtered = _products.filter(p => {
      const ids = p.categ_id ? (Array.isArray(p.categ_id) ? p.categ_id : [p.categ_id]) : [];
      return ids.includes(categoryId);
    });
    renderProducts('featuredProducts', filtered.length ? filtered : _products);
  }

  async function loadCreditSummary() {
    const container = $('#creditSummary');
    if (!container || !AUTH.isAuthenticated()) return;
    try {
      const lines = await API.getCreditLines();
      _creditLines = lines || [];
      if (_creditLines.length > 0) {
        const line = _creditLines[0];
        const avail = Number(line.available_credit || 0);
        const limit = Number(line.credit_limit || 0);
        $('#availableCredit').textContent = `$${avail.toFixed(2)}`;
        $('#totalLimit').textContent = `$${limit.toFixed(2)}`;
        $('#usedCredit').textContent = `$${Math.max(0, limit - avail).toFixed(2)}`;
        $('#creditStatus').textContent = line.state === 'approved' ? '✅ Activo' : '⏳ Pendiente';
        container.style.display = 'block';
      }
    } catch (_) { /* silencioso */ }
  }

  // ========================================================================
  //  C A T A L O G
  // ========================================================================
  async function loadCatalog() {
    try {
      if (_categories.length === 0) {
        _categories = await API.getCategories();
      }
      renderCatalogCategories();
      const products = await API.getFeaturedProducts(50);
      _products = products || [];
      renderProducts('catalogProducts', _products);
    } catch (err) {
      console.warn('Catálogo fallback:', err.message);
      renderCatalogCategoriesFallback();
      renderMockProducts('catalogProducts', '');
    }
  }

  function renderCatalogCategories() {
    const container = $('#catalogCategories');
    if (!container || _categories.length === 0) {
      renderCatalogCategoriesFallback();
      return;
    }
    let html = '<button class="category-pill active" onclick="APP.filterCatalog(0)">🌟 Todos</button>';
    _categories.slice(0, 12).forEach(c => {
      html += `<button class="category-pill" onclick="APP.filterCatalog(${c.id})">${c.name}</button>`;
    });
    container.innerHTML = html;
  }

  function renderCatalogCategoriesFallback() {
    const container = $('#catalogCategories');
    if (!container) return;
    container.innerHTML = `
      <button class="category-pill active" onclick="APP.filterCatalog(0)">🌟 Todos</button>
      <button class="category-pill" onclick="APP.filterCatalog(0)">💻 Computación</button>
      <button class="category-pill" onclick="APP.filterCatalog(0)">📱 Teléfonos</button>
      <button class="category-pill" onclick="APP.filterCatalog(0)">📺 TV</button>
      <button class="category-pill" onclick="APP.filterCatalog(0)">🏠 Hogar</button>
      <button class="category-pill" onclick="APP.filterCatalog(0)">🎮 Consolas</button>
      <button class="category-pill" onclick="APP.filterCatalog(0)">🚗 Automotriz</button>`;
  }

  async function filterCatalog(categoryId) {
    $$('#catalogCategories .category-pill').forEach(p => {
      const oc = p.getAttribute('onclick') || '';
      p.classList.toggle('active', oc.includes(`(${categoryId})`));
    });
    showLoading('catalogProducts');
    try {
      const products = categoryId === 0
        ? await API.getFeaturedProducts(50)
        : await API.getProductsByCategory(categoryId, 50);
      _products = products || [];
      renderProducts('catalogProducts', _products);
    } catch (_) {
      renderProducts('catalogProducts', _products);
    }
  }

  // ========================================================================
  //  S E A R C H  (debounced)
  // ========================================================================
  async function handleSearch() {
    const query = $('#searchInput').value.trim();
    if (!query) { loadCatalog(); return; }
    showLoading('catalogProducts');
    try {
      const results = await API.searchProducts(query, 30);
      renderProducts('catalogProducts', results || []);
    } catch (_) {
      showToast('Error al buscar', 'error');
      renderProducts('catalogProducts', _products);
    }
  }

  // ========================================================================
  //  C R E D I T
  // ========================================================================
  async function loadCreditData() {
    if (!AUTH.isAuthenticated()) {
      showToast('🔒 Inicia sesión para ver tu crédito', 'warning');
      navigate('home');
      return;
    }
    try {
      const lines = await API.getCreditLines();
      _creditLines = lines || [];
      const container = $('#creditLinesList');
      const section = $('#myCreditLines');
      if (_creditLines.length > 0) {
        section.style.display = 'block';
        container.innerHTML = _creditLines.map(line => {
          const avail = Number(line.available_credit || 0).toFixed(2);
          const limit = Number(line.credit_limit || 0).toFixed(2);
          const statusMap = { approved: '✅ Aprobada', pending: '⏳ Pendiente', refused: '❌ Rechazada', cancel: '🚫 Cancelada' };
          return `
            <div class="plan-card" style="margin-bottom:10px;">
              <div class="plan-name">${line.name || 'Línea de crédito'}</div>
              <div style="font-size:13px;color:var(--gray-500);margin-bottom:8px;">Estado: ${statusMap[line.state] || line.state || '--'}</div>
              <div style="display:flex;justify-content:space-between;font-size:14px;">
                <span>Disponible: <strong style="color:var(--success);">$${avail}</strong></span>
                <span>Límite: <strong>$${limit}</strong></span>
              </div>
            </div>`;
        }).join('');
      }
    } catch (_) { /* silencioso */ }
  }

  // ========================================================================
  //  C L U B   (versión completa desde club-membresia.html)
  // ========================================================================
  function loadClubData() {
    const container = $('#clubContent');
    if (!container) return;

    container.innerHTML = `
      <!-- Niveles Membresía -->
      <div class="card" style="margin-bottom:12px;">
        <div class="card-body">
          <h3 style="font-size:16px;font-weight:700;color:var(--primary);margin-bottom:12px;">🏆 Niveles de Membresía</h3>
          <div class="plan-card" style="margin-bottom:8px;">
            <div class="plan-name">🥉 Básico</div>
            <div class="plan-initial">Inicial desde <strong>50%</strong></div>
            <div class="plan-details"><span>Crédito básico</span><span>6 a 20 cuotas</span></div>
          </div>
          <div class="plan-card featured" style="margin-bottom:8px;">
            <span class="plan-badge popular">⭐ Más popular</span>
            <div class="plan-name">🥈 Medio</div>
            <div class="plan-initial">Inicial desde <strong>30%</strong></div>
            <div class="plan-details"><span>Crédito preferencial</span><span>Descuentos en comercios</span><span>Envío gratis</span><span>Puntos dobles</span></div>
          </div>
          <div class="plan-card">
            <span class="plan-badge vip">👑 VIP</span>
            <div class="plan-name">🥇 VIP</div>
            <div class="plan-initial">Inicial desde <strong>20%</strong></div>
            <div class="plan-details"><span>Crédito premium</span><span>Descuentos en todos los comercios</span><span>Asesor 24/7</span><span>Puntos triples</span><span>Eventos VIP</span></div>
          </div>
          <div style="display:flex;gap:8px;margin-top:12px;">
            <a href="https://latinbien.com/web/signup" class="btn btn-primary btn-sm" target="_blank" rel="noopener">⭐ Afiliarse</a>
            <a href="https://latinbien.com/web/login" class="btn btn-outline btn-sm" target="_blank" rel="noopener">🔑 Iniciar sesión</a>
          </div>
        </div>
      </div>

      <!-- Beneficios -->
      <div class="card" style="margin-bottom:12px;">
        <div class="card-body">
          <h3 style="font-size:16px;font-weight:700;color:var(--primary);margin-bottom:12px;">✨ Beneficios del Club</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div style="background:var(--primary-ultra);border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:24px;">💰</span>
              <div style="font-size:12px;font-weight:600;color:var(--primary);margin-top:4px;">Crédito Preferencial</div>
              <div style="font-size:10px;color:var(--accent);font-weight:700;margin-top:2px;">Hasta 20 cuotas</div>
            </div>
            <div style="background:var(--accent-light);border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:24px;">🍽️</span>
              <div style="font-size:12px;font-weight:600;color:var(--primary);margin-top:4px;">Descuentos Comercios</div>
              <div style="font-size:10px;color:var(--accent);font-weight:700;margin-top:2px;">Hasta 30% OFF</div>
            </div>
            <div style="background:#fce7f3;border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:24px;">🚀</span>
              <div style="font-size:12px;font-weight:600;color:var(--primary);margin-top:4px;">Envío Prioritario</div>
              <div style="font-size:10px;color:var(--accent);font-weight:700;margin-top:2px;">Sin costo extra</div>
            </div>
            <div style="background:#dbeafe;border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:24px;">🏆</span>
              <div style="font-size:12px;font-weight:600;color:var(--primary);margin-top:4px;">Programa de Puntos</div>
              <div style="font-size:10px;color:var(--accent);font-weight:700;margin-top:2px;">Acumula y canjea</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Comercios Afiliados -->
      <div class="card" style="margin-bottom:12px;">
        <div class="card-body">
          <h3 style="font-size:16px;font-weight:700;color:var(--primary);margin-bottom:12px;">📍 Comercios Afiliados</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div style="background:var(--gray-100);border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:22px;">🍝</span>
              <div style="font-size:12px;font-weight:600;margin-top:4px;">Rest. La Nota</div>
              <div style="font-size:11px;color:var(--accent);font-weight:700;">15% OFF</div>
              <div style="font-size:10px;color:var(--gray-400);">Gastronomía</div>
            </div>
            <div style="background:var(--gray-100);border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:22px;">🏋️</span>
              <div style="font-size:12px;font-weight:600;margin-top:4px;">Gimnasio Bi Fit</div>
              <div style="font-size:11px;color:var(--accent);font-weight:700;">30% OFF</div>
              <div style="font-size:10px;color:var(--gray-400);">Fitness</div>
            </div>
            <div style="background:var(--gray-100);border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:22px;">🅿️</span>
              <div style="font-size:12px;font-weight:600;margin-top:4px;">Est. Rodeo Plaza</div>
              <div style="font-size:11px;color:var(--accent);font-weight:700;">20% OFF</div>
              <div style="font-size:10px;color:var(--gray-400);">Estacionamiento</div>
            </div>
            <div style="background:var(--gray-100);border-radius:var(--radius-sm);padding:14px;text-align:center;">
              <span style="font-size:22px;">💻</span>
              <div style="font-size:12px;font-weight:600;margin-top:4px;">Tecnología Plus</div>
              <div style="font-size:11px;color:var(--accent);font-weight:700;">10% OFF</div>
              <div style="font-size:10px;color:var(--gray-400);">Tecnología</div>
            </div>
          </div>
          <div style="margin-top:12px;background:var(--primary-ultra);border-radius:var(--radius-sm);padding:14px;text-align:center;">
            <p style="font-size:12px;color:var(--gray-600);margin-bottom:8px;">💡 ¿Tienes un comercio y quieres ser afiliado?</p>
            <a href="https://wa.me/584147348785?text=Quiero%20ser%20comercio%20afiliado" class="btn btn-secondary btn-sm" target="_blank" rel="noopener">🤝 Ser afiliado</a>
          </div>
        </div>
      </div>

      <!-- Pasos -->
      <div class="card" style="margin-bottom:12px;">
        <div class="card-body">
          <h3 style="font-size:16px;font-weight:700;color:var(--primary);margin-bottom:12px;">📋 ¿Cómo funciona?</h3>
          <div style="display:flex;gap:12px;overflow-x:auto;padding-bottom:8px;">
            ${[1,2,3,4].map(i => `
              <div style="flex:0 0 140px;background:var(--gray-100);border-radius:var(--radius-sm);padding:14px;text-align:center;">
                <div style="width:32px;height:32px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-weight:700;font-size:14px;">${i}</div>
                <div style="font-size:12px;font-weight:600;color:var(--primary);">
                  ${['Regístrate','Activa tu membresía','Compra y ahorra','Crece con nosotros'][i-1]}
                </div>
                <div style="font-size:10px;color:var(--gray-500);margin-top:4px;">
                  ${['Crea tu cuenta gratis','Selecciona tu nivel','Usa tu crédito y descuentos','Sube de nivel con pagos'][i-1]}
                </div>
              </div>`).join('')}
          </div>
        </div>
      </div>

      <!-- FAQ -->
      <div class="card" style="margin-bottom:12px;">
        <div class="card-body">
          <h3 style="font-size:16px;font-weight:700;color:var(--primary);margin-bottom:12px;">❓ Preguntas Frecuentes</h3>
          ${[
            {q:'¿Cuánto cuesta ser miembro?',a:'Ser miembro del Club Latinbien es completamente <strong>gratis</strong>. No hay cuotas de afiliación ni costos de mantenimiento.'},
            {q:'¿Cómo accedo a los descuentos?',a:'Presenta tu cédula o código de miembro en el comercio afiliado al pagar. El descuento se aplica automáticamente.'},
            {q:'¿Puedo subir de nivel?',a:'Sí. A medida que construyes un historial de pagos puntuales y realizas más contratos, asciendes automáticamente de nivel.'},
          ].map((faq, i) => `
            <div style="border:1px solid var(--gray-200);border-radius:var(--radius-sm);margin-bottom:8px;overflow:hidden;">
              <button onclick="this.parentElement.classList.toggle('open')" style="width:100%;padding:12px 14px;background:none;border:none;text-align:left;font-size:13px;font-weight:600;color:var(--dark);cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-family:inherit;">
                ${faq.q}
                <span style="font-size:18px;color:var(--accent);transition:transform 0.3s;">+</span>
              </button>
              <div style="max-height:0;overflow:hidden;transition:max-height 0.3s ease;padding:0 14px;">
                <p style="font-size:12px;color:var(--gray-600);padding-bottom:12px;">${faq.a}</p>
              </div>
            </div>`).join('')}
        </div>
      </div>

      <div style="text-align:center;padding:16px;">
        <a href="https://latinbien.com" class="btn btn-primary" target="_blank" rel="noopener">🌐 Conocer más en latinbien.com</a>
      </div>
    `;

    // Agregar lógica FAQ toggle
    container.querySelectorAll('[onclick*="toggle"]').forEach(el => {
      // Las funcionan inline, OK
    });
    // Hacer funcionar los FAQ inline
    container.querySelectorAll('button').forEach(btn => {
      if (btn.textContent.includes('¿')) {
        btn.addEventListener('click', function() {
          const parent = this.parentElement;
          parent.classList.toggle('open');
          const answer = parent.querySelector('div:last-child');
          if (parent.classList.contains('open')) {
            answer.style.maxHeight = answer.scrollHeight + 'px';
          } else {
            answer.style.maxHeight = '0';
          }
          const icon = this.querySelector('span:last-child');
          if (icon) icon.style.transform = parent.classList.contains('open') ? 'rotate(45deg)' : 'rotate(0)';
        });
      }
    });
  }

  // ========================================================================
  //  P R O F I L E
  // ========================================================================
  async function loadProfile() {
    const nameEl = $('#profileName');
    const emailEl = $('#profileEmail');
    const user = AUTH.getCurrentUser();
    if (!user) { navigate('home'); return; }

    nameEl.textContent = user.name || 'Usuario';
    emailEl.textContent = user.username || '';

    try {
      const partners = await API.getPartnerInfo();
      if (partners && partners.length > 0) {
        const p = partners[0];
        nameEl.textContent = p.name || user.name;
        emailEl.textContent = p.email || user.username;
      }
    } catch (_) { /* usar datos de sesión */ }
  }

  // ========================================================================
  //  O R D E R S
  // ========================================================================
  async function loadOrders() {
    const container = $('#ordersList');
    if (!container) return;

    if (!AUTH.isAuthenticated()) {
      navigate('home');
      return;
    }

    try {
      const orders = await API.getMyOrders(20);
      _orders = orders || [];
      renderOrders();
    } catch (err) {
      console.warn('Orders fallback:', err.message);
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>No pudimos cargar tus contratos</h3>
          <p style="margin-top:8px;">
            <a href="https://latinbien.com/my" class="btn btn-primary btn-sm" target="_blank" rel="noopener">Ir al sitio web</a>
          </p>
        </div>`;
    }
  }

  function renderOrders() {
    const container = $('#ordersList');
    if (!container) return;

    if (!_orders || _orders.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>No tienes contratos aún</h3>
          <p>Visita el catálogo y haz tu primera compra</p>
          <a href="https://latinbien.com/shop" class="btn btn-primary btn-sm" style="margin-top:12px;" target="_blank" rel="noopener">Ir al catálogo</a>
        </div>`;
      return;
    }

    const statusLabels = { draft: 'Borrador', sent: 'Enviado', sale: 'Vendido', done: 'Completado', cancel: 'Cancelado' };
    const html = _orders.map(order => {
      const status = order.state || 'draft';
      const date = order.date_order
        ? new Date(order.date_order).toLocaleDateString('es-VE', { year: 'numeric', month: 'long', day: 'numeric' })
        : 'Fecha no disponible';
      const amount = order.amount_total ? `$${Number(order.amount_total).toFixed(2)}` : '$0.00';
      return `
        <div class="order-item">
          <div class="order-header">
            <span class="order-ref">${order.name || 'Contrato'}</span>
            <span class="order-status status-${status}">${statusLabels[status] || status}</span>
          </div>
          <div class="order-body">
            <div class="order-date">📅 ${date}</div>
            <div class="order-amount">💰 ${amount}</div>
          </div>
        </div>`;
    }).join('');
    container.innerHTML = html;
  }

  // ========================================================================
  //  REPORT PAYMENT
  // ========================================================================
  function reportPayment() {
    window.open('https://latinbien.com/my', '_blank');
  }

  // ========================================================================
  //  C A R R I T O   D E   C O M P R A S
  // ========================================================================

  /**
   * Cargar carrito desde localStorage
   */
  function loadCart() {
    try {
      const stored = localStorage.getItem('latinbien_cart');
      if (stored) {
        _cart = JSON.parse(stored);
        if (!Array.isArray(_cart)) _cart = [];
      }
    } catch (_) { _cart = []; }
    updateCartBadge();
  }

  /**
   * Guardar carrito en localStorage
   */
  function saveCart() {
    try {
      localStorage.setItem('latinbien_cart', JSON.stringify(_cart));
    } catch (_) { /* quota exceed */ }
    updateCartBadge();
  }

  /**
   * Actualizar badge del carrito en tab y header
   */
  function updateCartBadge() {
    const count = _cart.reduce((sum, item) => sum + (item.qty || 1), 0);
    const badges = $$('.cart-badge');
    badges.forEach(b => {
      b.textContent = count;
      b.classList.toggle('visible', count > 0);
    });
  }

  /**
   * Agregar producto al carrito
   */
  function addToCart(product) {
    const existing = _cart.find(item => item.id === product.id);
    if (existing) {
      existing.qty = (existing.qty || 1) + 1;
    } else {
      _cart.push({
        id: product.id,
        name: product.name,
        price: product.list_price || 0,
        image: product.id,  // Se resuelve con API.getProductImageUrl
        qty: 1,
        url: product.website_url || `https://latinbien.com/shop/product/${product.id}`,
      });
    }
    saveCart();
    showToast(`✅ ${product.name} agregado al carrito`, 'success');
  }

  /**
   * Cambiar cantidad de un item
   */
  function updateCartQty(productId, delta) {
    const item = _cart.find(i => i.id === productId);
    if (!item) return;
    item.qty = Math.max(1, (item.qty || 1) + delta);
    saveCart();
    renderCartPage();
  }

  /**
   * Eliminar item del carrito
   */
  function removeFromCart(productId) {
    _cart = _cart.filter(i => i.id !== productId);
    saveCart();
    renderCartPage();
    showToast('Producto eliminado del carrito', 'warning');
  }

  /**
   * Vaciar carrito
   */
  function clearCart() {
    if (_cart.length === 0) return;
    if (!confirm('¿Vaciar carrito?')) return;
    _cart = [];
    saveCart();
    renderCartPage();
    showToast('Carrito vaciado', 'warning');
  }

  /**
   * Obtener total del carrito
   */
  function getCartTotal() {
    return _cart.reduce((sum, item) => sum + (item.price || 0) * (item.qty || 1), 0);
  }

  /**
   * Obtener cantidad total de items
   */
  function getCartCount() {
    return _cart.reduce((sum, item) => sum + (item.qty || 1), 0);
  }

  /**
   * Renderizar página del carrito
   */
  function renderCartPage() {
    const empty = $('#cartEmpty');
    const items = $('#cartItems');
    const summary = $('#cartSummary');

    if (!items || !summary || !empty) return;

    if (_cart.length === 0) {
      empty.style.display = 'block';
      items.style.display = 'none';
      summary.style.display = 'none';
      return;
    }

    empty.style.display = 'none';
    items.style.display = 'block';
    summary.style.display = 'block';

    // Items
    items.innerHTML = _cart.map(item => `
      <div class="cart-item">
        <img class="cart-item-image" src="${API.getProductImageUrl(item.id)}" alt="${item.name}"
             onerror="this.src='data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="#f3f4f6" width="100" height="100"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="24">📦</text></svg>')}'">
        <div class="cart-item-info">
          <div class="cart-item-name">${item.name}</div>
          <div class="cart-item-price">$${(item.price * (item.qty || 1)).toFixed(2)}</div>
          <div class="cart-item-actions">
            <button class="qty-btn" onclick="APP.updateCartQty(${item.id}, -1)">−</button>
            <span class="cart-item-qty">${item.qty || 1}</span>
            <button class="qty-btn" onclick="APP.updateCartQty(${item.id}, 1)">+</button>
            <button class="qty-btn remove" onclick="APP.removeFromCart(${item.id})" style="margin-left:8px;">✕</button>
          </div>
        </div>
      </div>
    `).join('');

    // Summary
    const subtotal = getCartTotal();
    const itemCount = getCartCount();
    summary.innerHTML = `
      <div class="cart-summary">
        <div class="cart-summary-row">
          <span>Productos (${itemCount})</span>
          <span>$${subtotal.toFixed(2)}</span>
        </div>
        <div class="cart-summary-row total">
          <span>Total estimado</span>
          <span class="amount">$${subtotal.toFixed(2)}</span>
        </div>
        <div class="cart-actions">
          <a href="https://latinbien.com/shop/cart" class="btn btn-primary btn-block" target="_blank" rel="noopener">
            🛒 Ir al carrito en latinbien.com
          </a>
          <button class="btn btn-outline btn-block" onclick="APP.clearCart()">
            🗑️ Vaciar carrito
          </button>
          <p style="font-size:11px;color:var(--gray-400);text-align:center;margin-top:8px;">
            Los precios son referenciales. El total final se calcula en el sitio web.
          </p>
        </div>
      </div>
    `;
  }

  // ========================================================================
  //  P A G O S   (reportar desde la app)
  // ========================================================================

  /**
   * Renderizar la página de pagos con datos del usuario
   */
  function renderPaymentPage() {
    // Resetear formulario
    const form = $('#paymentForm');
    const success = $('#paymentSuccess');
    if (form) form.style.display = 'block';
    if (success) success.style.display = 'none';

    // Prellenar fecha actual
    const dateInput = $('#payDate');
    if (dateInput) {
      dateInput.value = new Date().toISOString().split('T')[0];
    }

    // Prellenar contratos del usuario si hay
    if (_orders.length > 0 && $('#payContract')) {
      // Podríamos poner un datalist pero mejor mantenerlo simple
    }
  }

  /**
   * Enviar reporte de pago a Odoo / WhatsApp
   */
  async function handlePaymentSubmit(e) {
    e.preventDefault();
    const contract = $('#payContract').value.trim();
    const amount = $('#payAmount').value.trim();
    const reference = $('#payReference').value.trim();
    const method = $('#payMethod').value;
    const date = $('#payDate').value;
    const notes = $('#payNotes').value.trim();
    const btn = $('#payBtn');

    if (!contract || !amount || !reference) {
      showToast('Completa todos los campos obligatorios', 'warning');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Enviando…';

    try {
      // Construir mensaje para WhatsApp (método más confiable que API directa)
      const user = AUTH.getCurrentUser();
      const username = user?.name || user?.username || 'Cliente';
      const msg = encodeURIComponent(
        `📌 *REPORTE DE PAGO - LatinBien App*\n\n` +
        `👤 Cliente: ${username}\n` +
        `📄 Contrato: ${contract}\n` +
        `💰 Monto: $${amount}\n` +
        `🔢 Ref: ${reference}\n` +
        `🏦 Método: ${method || 'No especificado'}\n` +
        `📅 Fecha: ${date}\n` +
        `${notes ? `📝 Notas: ${notes}\n` : ''}\n` +
        `✅ Reportado desde la app`
      );

      // Abrir WhatsApp con el mensaje pre-llenado
      window.open(`https://wa.me/584147348785?text=${msg}`, '_blank');

      // Mostrar éxito
      const form = $('#paymentForm');
      const success = $('#paymentSuccess');
      if (form) form.style.display = 'none';
      if (success) success.style.display = 'block';

      showToast('✅ Reporte enviado por WhatsApp', 'success');
    } catch (err) {
      showToast('Error al enviar: ' + err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '📩 Enviar reporte de pago';
    }
  }

  // ========================================================================
  //  P U S H   N O T I F I C A T I O N S
  // ========================================================================

  async function setupPushNotifications(registration) {
    if (!registration || !registration.pushManager) return;

    // Verificar si ya hay suscripción
    try {
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        _pushSubscribed = true;
        return;
      }
    } catch (_) { /* no soportado */ }

    // No solicitamos permiso automáticamente para no molestar
    // La activación se hará cuando el usuario interactúe con la app
  }

  /**
   * Solicitar permiso y suscribir a notificaciones push
   */
  async function requestPushPermission() {
    if (_pushSubscribed) {
      showToast('Ya estás suscrito a notificaciones', 'info');
      return;
    }

    if (!('Notification' in window)) {
      showToast('Notificaciones no soportadas en este navegador', 'warning');
      return;
    }

    if (Notification.permission === 'denied') {
      showToast('Notificaciones bloqueadas. Actívalas desde la configuración.', 'warning');
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        showToast('🔔 Notificaciones activadas', 'success');
        _pushSubscribed = true;

        // Registrar en el SW (sin servidor, es local)
        const reg = await navigator.serviceWorker.ready;
        // En un entorno real aquí se enviaría la suscripción al servidor
        console.log('Push permission granted');
      } else {
        showToast('Permiso de notificaciones denegado', 'warning');
      }
    } catch (_) {
      showToast('Error al solicitar permiso de notificaciones', 'error');
    }
  }

  // ========================================================================
  //  E V E N T   L I S T E N E R S
  // ========================================================================
  function setupListeners() {
    $('#loginForm').addEventListener('submit', handleLogin);
    $('#btnLogout').addEventListener('click', handleLogout);

    // Search con debounce
    $('#searchBtn').addEventListener('click', handleSearch);
    $('#searchInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        clearTimeout(_searchTimeout);
        handleSearch();
      }
    });

    // Payment form
    $('#paymentForm').addEventListener('submit', handlePaymentSubmit);

    // Logo -> home
    $('#headerLogo').addEventListener('click', e => {
      e.preventDefault();
      navigate('home');
    });

    // Auth listener
    AUTH.onChange(user => {
      if (!user && $('#appShell').style.display !== 'none') {
        showLogin();
      }
    });
  }

  // ========================================================================
  //  P U B L I C   A P I
  // ========================================================================
  return {
    init,
    navigate,
    filterByCategory,
    filterCatalog,
    handleSearch,
    showToast,
    reportPayment: () => navigate('payment'),
    // Carrito
    addToCart,
    updateCartQty,
    removeFromCart,
    clearCart,
    getCartCount,
    getCartTotal,
    // Notificaciones
    requestPushPermission,
  };
})();

// ========================================================================
//  B O O T
// ========================================================================
document.addEventListener('DOMContentLoaded', () => APP.init());
