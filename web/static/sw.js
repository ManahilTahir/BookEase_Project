/**
 * BookEase Service Worker — PWA Offline Support
 * Strategy: Network-first for API/HTML, Cache-first for static assets.
 */

const CACHE_NAME    = 'bookease-v1';
const STATIC_ASSETS = [
  '/',
  '/static/css/bookease.css',
  '/static/js/main.js',
  '/static/js/booking.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/services',
  '/specialists',
];

/* ── Install: pre-cache static assets ─────────────────────────────────────── */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS.filter(url => !url.startsWith('/static/icons') || true));
    }).catch(err => {
      console.warn('[SW] Pre-cache failed (non-fatal):', err);
    })
  );
  self.skipWaiting();
});

/* ── Activate: clean old caches ───────────────────────────────────────────── */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

/* ── Fetch strategy ───────────────────────────────────────────────────────── */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  // API calls: network-only (never cache booking data)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(request));
    return;
  }

  // Internal routes: network-only
  if (url.pathname.startsWith('/internal/')) {
    event.respondWith(fetch(request));
    return;
  }

  // Static assets: cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // HTML pages: network-first, fallback to cache
  event.respondWith(
    fetch(request).then(response => {
      if (response.ok) {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
      }
      return response;
    }).catch(() => {
      return caches.match(request).then(cached => {
        if (cached) return cached;
        return caches.match('/');
      });
    })
  );
});

