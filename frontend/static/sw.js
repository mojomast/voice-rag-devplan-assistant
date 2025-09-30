// Voice RAG PWA Service Worker
const CACHE_NAME = 'voice-rag-v1.0.0';
const STATIC_CACHE_NAME = 'voice-rag-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'voice-rag-dynamic-v1.0.0';

// Define what to cache
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png',
  // Add other static assets as needed
];

const CACHE_STRATEGIES = {
  // Cache first, then network for static assets
  CACHE_FIRST: 'cache-first',
  // Network first, then cache for dynamic content
  NETWORK_FIRST: 'network-first',
  // Cache only for offline-first content
  CACHE_ONLY: 'cache-only',
  // Network only for always-fresh content
  NETWORK_ONLY: 'network-only'
};

// Install event - cache static assets
self.addEventListener('install', function(event) {
  console.log('[ServiceWorker] Installing...');

  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(function(cache) {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(function() {
        console.log('[ServiceWorker] Installation complete');
        return self.skipWaiting(); // Activate immediately
      })
      .catch(function(error) {
        console.error('[ServiceWorker] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  console.log('[ServiceWorker] Activating...');

  event.waitUntil(
    caches.keys()
      .then(function(cacheNames) {
        return Promise.all(
          cacheNames.map(function(cacheName) {
            // Delete old caches
            if (cacheName !== STATIC_CACHE_NAME &&
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName.startsWith('voice-rag-')) {
              console.log('[ServiceWorker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(function() {
        console.log('[ServiceWorker] Activation complete');
        return self.clients.claim(); // Take control immediately
      })
  );
});

// Fetch event - handle all network requests
self.addEventListener('fetch', function(event) {
  const requestURL = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension requests
  if (requestURL.protocol === 'chrome-extension:') {
    return;
  }

  event.respondWith(
    handleFetchRequest(event.request)
  );
});

async function handleFetchRequest(request) {
  const requestURL = new URL(request.url);

  try {
    // Determine caching strategy based on request
    if (isStaticAsset(requestURL)) {
      return await cacheFirstStrategy(request);
    } else if (isAPIRequest(requestURL)) {
      return await networkFirstStrategy(request);
    } else if (isStreamlitAsset(requestURL)) {
      return await cacheFirstStrategy(request);
    } else {
      return await networkFirstStrategy(request);
    }
  } catch (error) {
    console.error('[ServiceWorker] Fetch error:', error);
    return await getOfflineFallback(request);
  }
}

// Cache-first strategy for static assets
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    console.log('[ServiceWorker] Serving from cache:', request.url);
    return cachedResponse;
  }

  console.log('[ServiceWorker] Fetching and caching:', request.url);
  const response = await fetch(request);

  if (response.status === 200) {
    const cache = await caches.open(STATIC_CACHE_NAME);
    cache.put(request, response.clone());
  }

  return response;
}

// Network-first strategy for dynamic content
async function networkFirstStrategy(request) {
  try {
    console.log('[ServiceWorker] Fetching from network:', request.url);
    const response = await fetch(request);

    // Cache successful responses
    if (response.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    console.log('[ServiceWorker] Network failed, trying cache:', request.url);
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      return cachedResponse;
    }

    throw error;
  }
}

// Check if request is for static assets
function isStaticAsset(url) {
  return url.pathname.startsWith('/static/') ||
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.jpg') ||
         url.pathname.endsWith('.jpeg') ||
         url.pathname.endsWith('.gif') ||
         url.pathname.endsWith('.svg') ||
         url.pathname.endsWith('.ico') ||
         url.pathname.endsWith('.woff') ||
         url.pathname.endsWith('.woff2');
}

// Check if request is API call
function isAPIRequest(url) {
  return url.pathname.startsWith('/api/') ||
         url.pathname.startsWith('/documents/') ||
         url.pathname.startsWith('/query/') ||
         url.pathname.startsWith('/voice/') ||
         url.pathname.startsWith('/chat/') ||
         url.pathname.startsWith('/usage/');
}

// Check if request is Streamlit asset
function isStreamlitAsset(url) {
  return url.pathname.startsWith('/_stcore/') ||
         url.pathname.startsWith('/healthz') ||
         url.pathname.includes('streamlit');
}

// Get offline fallback response
async function getOfflineFallback(request) {
  const url = new URL(request.url);

  // For navigation requests, return cached main page
  if (request.mode === 'navigate') {
    const cachedPage = await caches.match('/');
    if (cachedPage) {
      return cachedPage;
    }
  }

  // For API requests, return offline message
  if (isAPIRequest(url)) {
    return new Response(
      JSON.stringify({
        status: 'error',
        message: 'Offline - please check your internet connection',
        offline: true
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }

  // For other requests, return a generic offline page
  return new Response(
    `
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice RAG - Offline</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background-color: #f5f5f5;
            }
            .offline-container {
                max-width: 400px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .offline-icon {
                font-size: 64px;
                margin-bottom: 20px;
            }
            .offline-title {
                color: #333;
                margin-bottom: 10px;
            }
            .offline-message {
                color: #666;
                margin-bottom: 20px;
            }
            .retry-button {
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="offline-container">
            <div class="offline-icon">📱</div>
            <h1 class="offline-title">You're Offline</h1>
            <p class="offline-message">
                Voice RAG is not available right now.
                Please check your internet connection and try again.
            </p>
            <button class="retry-button" onclick="window.location.reload()">
                Try Again
            </button>
        </div>
    </body>
    </html>
    `,
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'text/html' }
    }
  );
}

// Handle background sync for offline actions
self.addEventListener('sync', function(event) {
  console.log('[ServiceWorker] Background sync:', event.tag);

  if (event.tag === 'background-upload') {
    event.waitUntil(syncPendingUploads());
  } else if (event.tag === 'background-query') {
    event.waitUntil(syncPendingQueries());
  }
});

// Sync pending uploads when back online
async function syncPendingUploads() {
  try {
    const pendingUploads = await getPendingUploads();

    for (const upload of pendingUploads) {
      try {
        await fetch('/documents/upload', {
          method: 'POST',
          body: upload.formData
        });

        // Remove from pending after successful upload
        await removePendingUpload(upload.id);

        // Notify user of successful sync
        self.registration.showNotification('Upload Synced', {
          body: `Document "${upload.filename}" uploaded successfully`,
          icon: '/static/icon-192.png',
          badge: '/static/icon-72.png'
        });
      } catch (error) {
        console.error('[ServiceWorker] Upload sync failed:', error);
      }
    }
  } catch (error) {
    console.error('[ServiceWorker] Sync uploads error:', error);
  }
}

// Sync pending queries when back online
async function syncPendingQueries() {
  try {
    const pendingQueries = await getPendingQueries();

    for (const query of pendingQueries) {
      try {
        const response = await fetch('/query/text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query.text })
        });

        if (response.ok) {
          await removePendingQuery(query.id);
        }
      } catch (error) {
        console.error('[ServiceWorker] Query sync failed:', error);
      }
    }
  } catch (error) {
    console.error('[ServiceWorker] Sync queries error:', error);
  }
}

// IndexedDB helpers for offline storage
async function getPendingUploads() {
  // Implementation would use IndexedDB to store pending uploads
  return [];
}

async function removePendingUpload(id) {
  // Implementation would remove upload from IndexedDB
}

async function getPendingQueries() {
  // Implementation would use IndexedDB to store pending queries
  return [];
}

async function removePendingQuery(id) {
  // Implementation would remove query from IndexedDB
}

// Handle push notifications
self.addEventListener('push', function(event) {
  console.log('[ServiceWorker] Push received');

  const options = {
    body: 'Voice RAG has new updates available',
    icon: '/static/icon-192.png',
    badge: '/static/icon-72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Updates',
        icon: '/static/icon-72.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icon-72.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Voice RAG', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', function(event) {
  console.log('[ServiceWorker] Notification click received');

  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Handle share target
self.addEventListener('fetch', function(event) {
  const url = new URL(event.request.url);

  if (url.pathname === '/share' && event.request.method === 'POST') {
    event.respondWith(handleShareTarget(event.request));
  }
});

async function handleShareTarget(request) {
  const formData = await request.formData();
  const title = formData.get('title') || '';
  const text = formData.get('text') || '';
  const url = formData.get('url') || '';
  const files = formData.getAll('documents');

  // Store shared content for processing when app opens
  await storeSharedContent({ title, text, url, files });

  // Return response that redirects to main app
  return Response.redirect('/', 303);
}

async function storeSharedContent(content) {
  // Implementation would store in IndexedDB for app to process
  console.log('[ServiceWorker] Storing shared content:', content);
}

console.log('[ServiceWorker] Service Worker loaded successfully');