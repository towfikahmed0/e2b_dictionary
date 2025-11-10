const CACHE_NAME = 'e2b-dictionary-v1.0.1';
const urlsToCache = [
  '/',
  './index.html',
  './img/logo.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://raw.githubusercontent.com/towfikahmed0/e2b_dictionary/main/dictionary.json'
];

// Install event - cache initial resources
self.addEventListener('install', event => {
  console.log('Service Worker installing.');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating.');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin) && 
      !event.request.url.includes('raw.githubusercontent.com') &&
      !event.request.url.includes('cdnjs.cloudflare.com')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }

        return fetch(event.request).then(response => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              // Don't cache API calls to dictionary API to get fresh data
              if (!event.request.url.includes('api.dictionaryapi.dev')) {
                cache.put(event.request, responseToCache);
              }
            });

          return response;
        });
      }).catch(() => {
        // If both cache and network fail, show offline page
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      })
  );
});

// Background sync for dictionary updates
self.addEventListener('sync', event => {
  if (event.tag === 'dictionary-update') {
    console.log('Background sync for dictionary data');
    event.waitUntil(updateDictionaryData());
  }
});

async function updateDictionaryData() {
  try {
    const response = await fetch('https://raw.githubusercontent.com/towfikahmed0/e2b_dictionary/main/dictionary.json');
    const data = await response.json();
    
    const cache = await caches.open(CACHE_NAME);
    await cache.put('https://raw.githubusercontent.com/towfikahmed0/e2b_dictionary/main/dictionary.json', new Response(JSON.stringify(data)));
    
    console.log('Dictionary data updated in background');
  } catch (error) {
    console.error('Failed to update dictionary data:', error);
  }

}
