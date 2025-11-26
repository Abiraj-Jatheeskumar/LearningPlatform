/* eslint-disable no-restricted-globals */
/**
 * Push Notification Service Worker
 * Handles incoming push notifications and displays them
 */

// Listen for push events
self.addEventListener('push', function(event) {
  console.log('🔔🔔🔔 PUSH EVENT RECEIVED! 🔔🔔🔔');
  console.log('📨 Push notification received:', event);
  console.log('📨 Has data:', !!event.data);
  
  if (!event.data) {
    console.log('❌ Push event has no data - showing fallback notification');
    event.waitUntil(
      self.registration.showNotification('📝 New Quiz Question!', {
        body: 'A new quiz question is available',
        icon: '/favicon.ico',
        requireInteraction: true,
        tag: 'quiz-notification'
      })
    );
    return;
  }

  try {
    const data = event.data.json();
    console.log('📦 Push data:', data);
    
    const title = data.title || '📝 New Quiz Question';
    const options = {
      body: data.body || 'A new quiz question is available',
      icon: data.icon || '/favicon.ico',
      badge: data.badge || '/favicon.ico',
      vibrate: [200, 100, 200],
      tag: 'quiz-notification',
      requireInteraction: true,  // Keeps notification visible until user interacts
      data: {
        url: data.url || '/dashboard/student',
        questionId: data.data?.questionId,
        sessionId: data.data?.sessionId,
        timestamp: Date.now()
      },
      actions: [
        {
          action: 'answer',
          title: 'Answer Now'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ]
    };

    console.log('🔔 SHOWING NOTIFICATION NOW!');
    console.log('Title:', title);
    console.log('Options:', options);
    
    event.waitUntil(
      self.registration.showNotification(title, options).then(() => {
        console.log('✅ Notification shown successfully!');
      }).catch(error => {
        console.error('❌ Error showing notification:', error);
      })
    );
    
  } catch (error) {
    console.error('❌ Error parsing push data:', error);
    
    // Fallback notification
    event.waitUntil(
      self.registration.showNotification('New Quiz Question', {
        body: 'A new quiz question is available',
        icon: '/favicon.ico',
        data: {
          url: '/dashboard/student'
        }
      })
    );
  }
});

// Listen for notification click events
self.addEventListener('notificationclick', function(event) {
  console.log('🖱️ Notification clicked:', event);
  
  event.notification.close();
  
  const urlToOpen = event.notification.data?.url || '/dashboard/student';
  
  // Handle action buttons
  if (event.action === 'dismiss') {
    console.log('User dismissed notification');
    return;
  }
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(function(clientList) {
      // Check if there's already a window/tab open
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        const clientUrl = new URL(client.url);
        
        // If we find an existing tab, focus it and navigate to the quiz page
        if ('focus' in client) {
          console.log('✅ Focusing existing window');
          return client.focus().then(() => {
            // Navigate to the quiz page
            if (client.navigate) {
              return client.navigate(urlToOpen);
            }
          });
        }
      }
      
      // If no existing tab, open a new one
      if (clients.openWindow) {
        console.log('✅ Opening new window');
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Listen for notification close events
self.addEventListener('notificationclose', function(event) {
  console.log('🔕 Notification closed:', event);
});

// Service worker activation
self.addEventListener('activate', function(event) {
  console.log('✅ Push service worker activated');
  event.waitUntil(clients.claim());
});

// Service worker installation
self.addEventListener('install', function(event) {
  console.log('📥 Push service worker installed');
  self.skipWaiting();
});

