// Custom Service Worker for Buckezz
const staticCacheName = "buckezz-pwa-v1";
const filesToCache = [
    '/offline/',
    '/static/css/style.css',
    '/static/images/icon-160.png',
    '/static/images/icon-512.png'
];

// Cache on install
self.addEventListener("install", event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(staticCacheName)
            .then(cache => {
                // Try to cache all initial files
                // If some fail, log it but don't crash the entire SW installation
                return Promise.allSettled(
                    filesToCache.map(url => {
                        return cache.add(url).catch(err => {
                            console.warn(`[ServiceWorker] Could not cache: ${url}`, err);
                        });
                    })
                );
            })
    );
});

// Clear cache on activate
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => (cacheName.startsWith("buckezz-pwa-") || cacheName.startsWith("django-pwa-")))
                    .filter(cacheName => (cacheName !== staticCacheName))
                    .map(cacheName => caches.delete(cacheName))
            );
        }).then(() => self.clients.claim())
    );
});

// Serve from Cache / Network
self.addEventListener("fetch", event => {
    // Only handle GET requests with http/https schemes
    if (event.request.method !== 'GET' || !event.request.url.startsWith('http')) {
        return;
    }

    const url = new URL(event.request.url);

    // Static assets: Cache First
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request)
                .then(cachedResponse => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return fetch(event.request).then(networkResponse => {
                        if (networkResponse && networkResponse.status === 200) {
                            return caches.open(staticCacheName).then(cache => {
                                cache.put(event.request, networkResponse.clone());
                                return networkResponse;
                            });
                        }
                        return networkResponse;
                    });
                }).catch(() => {
                    return fetch(event.request);
                })
        );
    } else {
        // Dynamic pages & paths: Network First
        event.respondWith(
            fetch(event.request)
                .then(networkResponse => {
                    // Update cache with the latest version of the page
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(staticCacheName).then(cache => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return networkResponse;
                })
                .catch(() => {
                    return caches.match(event.request)
                        .then(cachedResponse => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // Fallback to offline page or raw response
                            return caches.match('/offline/')
                                .then(offlineResponse => {
                                    return offlineResponse || new Response(
                                        '<h1>Offline</h1><p>Du bist offline und diese Seite ist nicht im Cache.</p>',
                                        {
                                            status: 503,
                                            statusText: 'Service Unavailable',
                                            headers: new Headers({ 'Content-Type': 'text/html; charset=utf-8' })
                                        }
                                    );
                                });
                        });
                })
        );
    }
});
