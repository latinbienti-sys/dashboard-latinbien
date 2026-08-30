/* ============================================================
   LatinBien App — Service Worker v1.0
   ============================================================ */

const CACHE_NAME = 'latinbien-v1';
const STATIC_ASSETS = [
  '/latinbien-app/',
  '/latinbien-app/index.html',
  '/latinbien-app/manifest.json',
  '/latinbien-app/css/app.css',
  '/latinbien-app/js/app.js',
  '/latinbien-app/js/api.js',
  '/latinbien-app/js/auth.js',
  '/latinbien-app/icons/icon-192.svg',
  '/latinbien-app/icons/icon-512.svg',
];

// Al instalar, cachear assets estáticos
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activar: limpiar caches viejos
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Estrategia: Network First con fallback a cache
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Siempre ir a la red para API de Odoo (no cachear datos dinámicos)
  if (url.hostname === 'latinbien.com' && url.pathname.startsWith('/web/session')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Para recursos de Odoo (imágenes, web), priorizar red con timeout
  if (url.hostname === 'latinbien.com') {
    event.respondWith(networkFirstWithTimeout(request, 3000));
    return;
  }

  // Para assets locales de la app, cache first
  if (url.pathname.startsWith('/latinbien-app/')) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Para Google Fonts y otros CDN, network first
  event.respondWith(networkFirst(request));
});

/* ---- Estrategias ---- */

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return new Response(
      JSON.stringify({ error: 'Sin conexión', offline: true }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ error: 'Sin conexión', offline: true }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

async function networkFirstWithTimeout(request, timeoutMs) {
  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('timeout')), timeoutMs)
  );
  try {
    const response = await Promise.race([fetch(request), timeoutPromise]);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ error: 'Sin conexión', offline: true }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

// Escuchar mensajes desde la app (para borrar cache, etc.)
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.delete(CACHE_NAME).then(() => {
      event.ports[0]?.postMessage({ success: true });
    });
  }
});

// ===== PUSH NOTIFICATIONS =====
self.addEventListener('push', event => {
  let data = { title: 'LatinBien', body: 'Tienes una nueva notificación', icon: '/latinbien-app/icons/icon-192.svg' };
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (_) {
      data.body = event.data.text() || data.body;
    }
  }
  const options = {
    body: data.body,
    icon: data.icon,
    badge: '/latinbien-app/icons/icon-72.svg',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' },
    actions: [
      { action: 'open', title: 'Abrir' },
      { action: 'close', title: 'Cerrar' },
    ],
  };
  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'open' || !event.action) {
    const url = event.notification.data?.url || '/latinbien-app/';
    event.waitUntil(clients.openWindow(url));
  }
});
