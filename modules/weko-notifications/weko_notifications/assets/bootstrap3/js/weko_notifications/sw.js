// Handle push event received from the backend
window.self.addEventListener('push', function (event) {
  const data = event.data.json(); // Parse the message from the server as JSON

  // Display the push notification using the showNotification method
  event.waitUntil(
    window.self.registration.showNotification(data.title, data.options)
      .catch(err => console.error('Notification display error:', err))
  );
});

// Handle notification click event
window.self.addEventListener('notificationclick', function (event) {
  event.notification.close(); // Close the notification
  event.waitUntil(
    window.clients.matchAll({ type: 'window' }).then(windowClients => {
      for (let client of windowClients) {
        if (client.url === event.notification.data.url && 'focus' in client) {
          return client.focus();
        }
      }
      if (window.clients.openWindow) {
        return window.clients.openWindow(event.notification.data.url);
      }
    })
  );
});

// Execute when Service Worker is installed
window.self.addEventListener('install', (event) => {
  window.self.skipWaiting(); // Force the active service worker to switch
});

// Execute when Service Worker is activated
window.self.addEventListener('activate', (event) => {
  event.waitUntil(window.self.clients.claim()); // Immediately start controlling the clients
});

// Listen for messages from the client
window.self.addEventListener('message', (event) => {
  if (event.data.action === 'skipWaiting') {
    window.self.skipWaiting();
  }
});
