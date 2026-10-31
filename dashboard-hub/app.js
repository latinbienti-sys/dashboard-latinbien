const dashboards = [
  { id: 'latinbien-ventas', name: 'Ventas', category: 'LATINBIEN', icon: '↗', color: '#ef7d68', description: 'Ventas, ingresos y cuota comercial.', keywords: 'latinbien ventas revenue ingresos comercial', url: 'https://latinbienti-sys.github.io/dashboard-latinbien/' },
  { id: 'latinbien-finanzas', name: 'Finanzas', category: 'LATINBIEN', icon: '$', color: '#6e9e42', description: 'Flujo de caja y control presupuestal.', keywords: 'latinbien finanzas caja presupuesto gastos', url: 'https://latinbienti-sys.github.io/dashboard-latinbien/' },
  { id: 'latinbien-soporte', name: 'Soporte', category: 'LATINBIEN', icon: '◌', color: '#59a884', description: 'Tickets, tiempos y satisfacción.', keywords: 'latinbien soporte tickets atención satisfacción', url: 'https://latinbienti-sys.github.io/dashboard-latinbien/' },
  { id: 'latinbien-inventario', name: 'Inventario', category: 'LATINBIEN', icon: '▦', color: '#4b87c5', description: 'Stock, rotación y quiebres.', keywords: 'latinbien inventario stock logística rotación', url: 'https://latinbienti-sys.github.io/dashboard-latinbien/' },
  { id: 'latinbien-crm', name: 'CRM', category: 'LATINBIEN', icon: '◎', color: '#705fe8', description: 'Clientes, oportunidades y seguimiento comercial.', keywords: 'latinbien crm clientes oportunidades ventas', url: 'https://latinbienti-sys.github.io/dashboard-latinbien/' },
  { id: 'latinbien-clientes', name: 'Clientes', category: 'LATINBIEN', icon: '♙', color: '#c77cc9', description: 'Cartera, segmentos, clientes activos y VIP.', keywords: 'latinbien clientes cartera segmentos vip', url: 'https://latinbienti-sys.github.io/dashboard-latinbien/' },
  { id: 'latinbien-cobranza', name: 'Cobranza', category: 'LATINBIEN', icon: '₡', color: '#d58b36', description: 'Cuotas, vencidos, ciclos y gestión de cobros.', keywords: 'latinbien cobranza cobros cuotas vencidos ciclos pagos', url: 'https://latinbienti-sys.github.io/dashboard-latinbien/' },
  { id: 'honda-inventario', name: 'Inventario', category: 'HONDA', icon: '▦', color: '#d33f55', description: 'Stock, rotación y disponibilidad.', keywords: 'honda inventario stock logística rotación', url: '#', example: true },
  { id: 'honda-crm', name: 'CRM', category: 'HONDA', icon: '◎', color: '#1f75b9', description: 'Clientes, oportunidades y seguimiento comercial.', keywords: 'honda crm clientes oportunidades ventas', url: '#', example: true }
];

const state = { category: 'Todos', query: '', favoritesOnly: false, sort: 'popular' };
const favoriteKey = 'dashboard-hub-favorites';
const favorites = new Set(JSON.parse(localStorage.getItem(favoriteKey) || '[]'));
const grid = document.querySelector('#dashboard-grid');
const emptyState = document.querySelector('#empty-state');
const count = document.querySelector('#result-count');
const searchInput = document.querySelector('#dashboard-search');
const toast = document.querySelector('#toast');
let toastTimeout;

function getCategories() {
  return ['Todos', ...new Set(dashboards.map((dashboard) => dashboard.category))];
}

function renderCategories() {
  document.querySelector('#category-filters').innerHTML = getCategories().map((category) => `
    <button class="category-button ${state.category === category ? 'is-active' : ''}" type="button" role="tab" aria-selected="${state.category === category}" data-category="${category}">${category}</button>
  `).join('');
}

function filteredDashboards() {
  const query = state.query.trim().toLowerCase();
  const results = dashboards.filter((dashboard) => {
    const matchesCategory = state.category === 'Todos' || dashboard.category === state.category;
    const searchable = `${dashboard.name} ${dashboard.category} ${dashboard.description} ${dashboard.keywords}`.toLowerCase();
    const matchesQuery = !query || searchable.includes(query);
    const matchesFavorite = !state.favoritesOnly || favorites.has(dashboard.id);
    return matchesCategory && matchesQuery && matchesFavorite;
  });
  if (state.sort === 'favorites') return results.sort((a, b) => Number(favorites.has(b.id)) - Number(favorites.has(a.id)));
  return results.sort((a, b) => Number(favorites.has(b.id)) - Number(favorites.has(a.id)) || dashboards.indexOf(a) - dashboards.indexOf(b));
}

function cardTemplate(dashboard) {
  const isFavorite = favorites.has(dashboard.id);
  return `
    <article class="dashboard-card" style="--card-color: ${dashboard.color}; --icon-ink: ${dashboard.icon === '$' ? '#fff' : '#fff'}">
      <div class="card-top">
        <div class="app-icon" aria-hidden="true">${dashboard.icon}</div>
        <button class="favorite-button ${isFavorite ? 'is-favorite' : ''}" type="button" aria-label="${isFavorite ? 'Quitar' : 'Agregar'} ${dashboard.name} ${isFavorite ? 'de favoritos' : 'a favoritos'}" aria-pressed="${isFavorite}" data-favorite="${dashboard.id}">${isFavorite ? '★' : '☆'}</button>
      </div>
      <div class="card-content">
        <h3 class="card-title">${dashboard.name}</h3>
        <p class="card-description">${dashboard.description}</p>
      </div>
      <div class="card-footer">
        <span class="card-tag">${dashboard.category}</span>
        ${dashboard.example ? `<button class="open-link open-example" type="button" data-open="${dashboard.id}">Abrir <span>↗</span></button>` : `<a class="open-link" href="${dashboard.url}" target="_blank" rel="noopener">Abrir <span>↗</span></a>`}
      </div>
    </article>
  `;
}

function render() {
  renderCategories();
  const results = filteredDashboards();
  grid.innerHTML = results.map(cardTemplate).join('');
  grid.hidden = results.length === 0;
  emptyState.hidden = results.length !== 0;
  count.textContent = results.length;
  document.querySelector('#favorites-only').setAttribute('aria-pressed', String(state.favoritesOnly));
  document.querySelector('#favorites-only').classList.toggle('is-active', state.favoritesOnly);
}

function saveFavorites() {
  localStorage.setItem(favoriteKey, JSON.stringify([...favorites]));
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('is-visible');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove('is-visible'), 3200);
}

document.addEventListener('click', (event) => {
  const categoryButton = event.target.closest('[data-category]');
  if (categoryButton) {
    state.category = categoryButton.dataset.category;
    render();
    return;
  }
  const favoriteButton = event.target.closest('[data-favorite]');
  if (favoriteButton) {
    const id = favoriteButton.dataset.favorite;
    favorites.has(id) ? favorites.delete(id) : favorites.add(id);
    saveFavorites();
    render();
    showToast(favorites.has(id) ? 'Dashboard agregado a favoritos' : 'Dashboard retirado de favoritos');
    return;
  }
  const exampleButton = event.target.closest('[data-open]');
  if (exampleButton) {
    const dashboard = dashboards.find((item) => item.id === exampleButton.dataset.open);
    showToast(`${dashboard?.name || 'Dashboard'}: reemplaza el enlace de ejemplo en app.js`);
    return;
  }
  const openCard = event.target.closest('.dashboard-card');
  if (openCard && !event.target.closest('button, a')) {
    const title = openCard.querySelector('.card-title')?.textContent || 'Dashboard';
    showToast(`${title}: reemplaza el enlace de ejemplo en app.js`);
  }
});

document.querySelector('#favorites-only').addEventListener('click', () => { state.favoritesOnly = !state.favoritesOnly; render(); });
document.querySelector('#sort-button').addEventListener('click', () => {
  state.sort = state.sort === 'popular' ? 'favorites' : 'popular';
  document.querySelector('#sort-button').innerHTML = `<span class="sort-icon">↕</span> ${state.sort === 'favorites' ? 'Favoritos primero' : 'Más usados'} <span class="chevron">⌄</span>`;
  render();
});
document.querySelector('#clear-filters').addEventListener('click', () => { state.category = 'Todos'; state.query = ''; state.favoritesOnly = false; render(); });

render();
