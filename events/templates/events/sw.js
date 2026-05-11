// Service Worker for ZOZAPRIME PWA - v3 (Production-safe)
const CACHE_NAME = 'zozaprime-v3';

// ONLY cache static assets that don't change
const urlsToCache = [
  '/static/img/logo.png',
  '/static/img/favicon.png',
];

// ─────────────────────────────────────────────────────────
// INSTALL
// ─────────────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Opened cache v3');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting();
});

// ─────────────────────────────────────────────────────────
// FETCH — Strict guards, never touch dynamic routes
// ─────────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // RULE 1: NEVER intercept non-GET requests
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  if (request.method !== 'GET') {
    return; // Browser handles natively
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // RULE 2: NEVER intercept dynamic / sensitive routes
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const dynamicPaths = [
    '/admin/',
    '/payments/',
    '/checkout/',
    '/accounts/',
    '/api/',
    '/profile/',
    '/dashboard/',
    '/login/',
    '/logout/',
    '/signup/',
    '/register/',
    '/manifest.json',
    '/csrf/',
  ];

  const isDynamic = dynamicPaths.some(path => url.pathname.startsWith(path));
  if (isDynamic) {
    return; // Browser handles natively
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // RULE 3: NEVER intercept cross-origin requests
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  if (url.origin !== self.location.origin) {
    return; // External requests pass through
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // RULE 4: HTML pages → Network-first, fallback to cache
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .catch(() => caches.match(request))
    );
    return;
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // RULE 5: Static assets → Cache-first, fallback to network
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  event.respondWith(
    caches.match(request)
      .then((cached) => cached || fetch(request))
      .catch(() => fetch(request)) // Always fall back to network
  );
});

// ─────────────────────────────────────────────────────────
// ACTIVATE — Clean up old caches
// ─────────────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// ─────────────────────────────────────────────────────────
// PUSH NOTIFICATIONS (future-ready)
// ─────────────────────────────────────────────────────────
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New update available',
    icon: '/static/img/logo.png',
    badge: '/static/img/favicon.png',
    vibrate: [200, 100, 200],
    tag: 'zozaprime-notification',
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification('ZOZAPRIME', options)
  );
});