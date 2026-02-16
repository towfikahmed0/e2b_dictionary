const CACHE_NAME = 'e2b-dictionary-v1.4.0';
const urlsToCache = [
  '/',
  './index.html',
  './img/logo.png',
  './manifest.json'
];

const DICTIONARY_URL = 'https://raw.githubusercontent.com/towfikahmed0/e2b_dictionary/main/dictionary.json';

// Install event - cache initial resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  const url = event.request.url;

  // Handle dictionary data with stale-while-revalidate
  if (url === DICTIONARY_URL) {
    event.respondWith(
      caches.open(CACHE_NAME).then(cache => {
        return cache.match(event.request).then(cachedResponse => {
          const fetchedResponse = fetch(event.request).then(networkResponse => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
          return cachedResponse || fetchedResponse;
        });
      })
    );
    return;
  }

  // Skip cross-origin requests except for allowed ones
  if (!url.startsWith(self.location.origin) &&
      !url.includes('api.dictionaryapi.dev')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }

        return fetch(event.request).then(response => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            // Don't cache API calls to dictionary API to keep fresh
            if (!url.includes('api.dictionaryapi.dev')) {
              cache.put(event.request, responseToCache);
            }
          });

          return response;
        });
      }).catch(() => {
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      })
  );
});

// Background sync for dictionary updates
self.addEventListener('sync', event => {
  if (event.tag === 'dictionary-update') {
    event.waitUntil(updateDictionaryData());
  }
});

async function updateDictionaryData() {
  try {
    const response = await fetch(DICTIONARY_URL);
    const cache = await caches.open(CACHE_NAME);
    await cache.put(DICTIONARY_URL, response);
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}
