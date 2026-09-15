// FindIt Campus — Service Worker for Push Notifications
// Handles incoming push events and shows browser notifications

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', event => {
  let data = {};
  if (event.data) {
    try { data = event.data.json(); } catch { data = { title: 'FindIt Campus', body: event.data.text() }; }
  }

  const options = {
    body: data.body || 'You have a new notification',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/badge-72.png',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/dashboard' },
    actions: [
      { action: 'view', title: '👀 View', icon: '/static/icons/view.png' },
      { action: 'dismiss', title: '✖️ Dismiss' }
    ],
    tag: 'findit-notification',
    renotify: true
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'FindIt Campus', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'dismiss') return;

  const url = event.notification.data?.url || '/dashboard';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clients => {
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(url);
    })
  );
});
