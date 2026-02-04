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
    console.log('📦 Raw push data received:', data);
    console.log('📦 data.data:', data.data);
    
    // Extract the quiz data - it's in data.data from the backend
    const quizData = data.data || {};
    console.log('🎯 Quiz data extracted:', quizData);
    console.log('   - question:', quizData.question);
    console.log('   - options:', quizData.options);
    console.log('   - questionId:', quizData.questionId);
    
    const title = data.title || '📝 New Quiz Question';
    const options = {
      body: data.body || 'A new quiz question is available',
      icon: data.icon || '/favicon.ico',
      badge: data.badge || '/favicon.ico',
      vibrate: [200, 100, 200],
      tag: 'quiz-notification',
      requireInteraction: true,  // Keeps notification visible until user interacts
      data: quizData,  // Store the quiz data (already extracted from data.data)
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
    console.log('Notification data will be:', options.data);
    
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
  
  // Handle action buttons
  if (event.action === 'dismiss') {
    console.log('User dismissed notification');
    return;
  }
  
  // Get quiz data from notification
  const quizData = event.notification.data;
  console.log('📦 Quiz data from notification:', quizData);
  
  // Build URL with quiz data as query parameter (for new window case)
  let urlToOpen = '/dashboard/student';
  if (quizData && quizData.questionId) {
    const encodedQuizData = btoa(JSON.stringify(quizData));
    urlToOpen = `/dashboard/student?showQuiz=${encodedQuizData}`;
    console.log('🔗 Opening URL with quiz:', urlToOpen);
  }
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(function(clientList) {
      console.log('🔍 Found', clientList.length, 'client windows');
      
      // Check if there's already a window/tab open
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        
        // If we find an existing tab, focus it and send quiz data
        if ('focus' in client) {
          console.log('✅ Focusing existing window and sending quiz data');
          return client.focus().then(() => {
            // Send message to client to show quiz immediately
            if (quizData && quizData.questionId) {
              console.log('📤 Posting SHOW_QUIZ message to client');
              client.postMessage({
                type: 'SHOW_QUIZ',
                quiz: quizData
              });
            }
          });
        }
      }
      
      // If no existing tab, open a new one with quiz data in URL
      if (clients.openWindow) {
        console.log('✅ Opening new window with quiz in URL');
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

