# 🔔 How Push Notifications Work - Complete Explanation

## 📖 Table of Contents
1. [Overview](#overview)
2. [Phase 1: Student Subscription](#phase-1-student-subscription)
3. [Phase 2: Instructor Triggers Question](#phase-2-instructor-triggers-question)
4. [Phase 3: Backend Sends Push](#phase-3-backend-sends-push)
5. [Phase 4: Student Receives Notification](#phase-4-student-receives-notification)
6. [Technical Details](#technical-details)

---

## Overview

Push notifications work through **4 main phases**:
1. **Subscription** - Student registers to receive notifications
2. **Trigger** - Instructor triggers a question
3. **Send** - Backend sends push to browser push service
4. **Receive** - Student's service worker shows notification

---

## Phase 1: Student Subscription

### What Happens When Student Logs In:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Student Logs In                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. AuthContext.tsx (Frontend)                                │
│    - Detects role = "student"                                │
│    - Calls initPushNotifications()                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Browser Asks Permission                                   │
│    "Allow notifications from this site?"                     │
│    [Block] [Allow]  ← Student clicks "Allow"                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Service Worker Registers                                  │
│    - Loads /push-sw.js                                       │
│    - Registers with browser                                  │
│    - Status: "Activated"                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Create Push Subscription                                  │
│    - Uses VAPID Public Key                                   │
│    - Browser generates unique subscription:                  │
│      {                                                        │
│        endpoint: "https://fcm.googleapis.com/...",          │
│        keys: {                                               │
│          p256dh: "encryption key",                          │
│          auth: "authentication key"                         │
│        }                                                     │
│      }                                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Send Subscription to Backend                              │
│    POST /api/notifications/subscribe                         │
│    Headers: { Authorization: "Bearer JWT_TOKEN" }           │
│    Body: { endpoint, keys }                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Backend Saves to MongoDB                                  │
│    Collection: push_subscriptions                            │
│    {                                                         │
│      studentId: "6920830dd3dc339d785449f2",                 │
│      endpoint: "https://fcm.googleapis.com/...",            │
│      keys: { p256dh: "...", auth: "..." },                  │
│      createdAt: "2025-11-26T..."                            │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
                 ✅ STUDENT SUBSCRIBED!
```

### Code Flow:

**1. AuthContext.tsx** (Lines 91-104):
```typescript
toast.success("Login successful");

// Initialize push notifications for students
if (response.user.role === "student") {
  setTimeout(() => {
    initPushNotifications().then((success) => {
      if (success) {
        console.log("✅ Push notifications enabled");
      }
    });
  }, 1000);
}
```

**2. pushNotificationService.ts** - `initPushNotifications()`:
```typescript
// Request permission
const permission = await Notification.requestPermission();

// Register service worker
const registration = await navigator.serviceWorker.register('/push-sw.js');

// Subscribe to push
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: VAPID_PUBLIC_KEY
});

// Send to backend
await sendSubscriptionToBackend(subscription);
```

**3. Backend - push_notification.py** - `/api/notifications/subscribe`:
```python
# Save subscription to MongoDB
doc = {
    "studentId": student_id,
    "endpoint": subscription.endpoint,
    "keys": subscription.keys,
    "createdAt": datetime.utcnow()
}
await db.database.push_subscriptions.insert_one(doc)
```

---

## Phase 2: Instructor Triggers Question

### What Happens When Instructor Clicks "Trigger Question":

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Instructor Clicks "Trigger Question" Button              │
│    (InstructorDashboard.tsx)                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Frontend Sends Request                                    │
│    POST /api/live/trigger/123456789                         │
│    Headers: { Authorization: "Bearer JWT_TOKEN" }           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Backend Receives Request                                  │
│    (live.py - trigger_question endpoint)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Backend Picks Random Question                             │
│    - Queries MongoDB "questions" collection                  │
│    - Selects random question                                 │
│    - Prepares message with question data                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────┐
│ 5a. WebSocket    │                  │ 5b. Push Service │
│     Broadcast    │                  │     (NEW!)       │
│                  │                  │                  │
│ Send via WS to   │                  │ Send via Push    │
│ connected        │                  │ to subscribed    │
│ students         │                  │ students         │
└──────────────────┘                  └──────────────────┘
```

### Code Flow:

**1. InstructorDashboard.tsx** - Button Click:
```typescript
const handleTriggerQuestion = async () => {
  const res = await axios.post(
    `${apiUrl}/api/live/trigger/123456789`
  );
  alert("🎯 Question sent to all students!");
};
```

**2. Backend - live.py** - `trigger_question()`:
```python
# Pick random question
questions = await db.database.questions.find({}).to_list(length=None)
q = random.choice(questions)

# Prepare message
message = {
    "type": "quiz",
    "questionId": str(q["_id"]),
    "question": q["question"],
    "options": q["options"],
    "timeLimit": q.get("timeLimit", 30),
    "sessionId": meeting_id
}

# Send via WebSocket
ws_sent_count = await ws_manager.broadcast_global(message)

# Send via Push Notifications (NEW!)
push_sent_count = await push_service.send_quiz_notification(message)
```

---

## Phase 3: Backend Sends Push

### How Backend Sends Push Notification:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. push_service.send_quiz_notification(quiz_data)           │
│    (push_service.py)                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Load All Student Subscriptions from MongoDB              │
│    Collection: push_subscriptions                            │
│    [{studentId, endpoint, keys}, ...]                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. For Each Student Subscription:                            │
│    Loop through all subscriptions                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Prepare Notification Payload                              │
│    {                                                         │
│      title: "📝 New Quiz Question!",                        │
│      body: "What is the capital of France?",                │
│      url: "/dashboard/student",                             │
│      icon: "/favicon.ico",                                  │
│      data: {                                                │
│        questionId: "...",                                   │
│        sessionId: "...",                                    │
│        timeLimit: 30                                        │
│      }                                                      │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Sign with VAPID Private Key                              │
│    - Proves request is from authorized server                │
│    - Creates cryptographic signature                         │
│    - Uses VAPID_PRIVATE_KEY from .env                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Send to Browser Push Service                              │
│    Using pywebpush library:                                  │
│                                                              │
│    webpush(                                                  │
│      subscription_info={endpoint, keys},                     │
│      data=json.dumps(payload),                              │
│      vapid_private_key=VAPID_PRIVATE_KEY,                   │
│      vapid_claims={"sub": "mailto:admin@..."}              │
│    )                                                         │
│                                                              │
│    Sends HTTPS POST to:                                      │
│    https://fcm.googleapis.com/fcm/send/... (Google)         │
│    or                                                        │
│    https://updates.push.services.mozilla.com/... (Firefox)  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Push Service Forwards to Student's Device                │
│    - Google FCM / Mozilla Push Service                      │
│    - Maintains persistent connection to browser              │
│    - Delivers message even if page is closed                 │
└─────────────────────────────────────────────────────────────┘
```

### Code Flow:

**push_service.py** - Complete Process:
```python
async def send_quiz_notification(self, quiz_data: dict) -> int:
    # 1. Prepare payload
    payload = {
        "title": "📝 New Quiz Question!",
        "body": quiz_data.get("question"),
        "url": "/dashboard/student",
        "data": {
            "questionId": quiz_data.get("questionId"),
            "sessionId": quiz_data.get("sessionId")
        }
    }
    
    # 2. Load all subscriptions
    subscriptions = await db.database.push_subscriptions.find({}).to_list(length=None)
    
    # 3. Send to each subscription
    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub["endpoint"],
            "keys": sub["keys"]
        }
        
        # 4. Send via pywebpush
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=self.vapid_private_key,
            vapid_claims=self.vapid_claims
        )
```

---

## Phase 4: Student Receives Notification

### What Happens on Student's Computer:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Push Service Delivers to Browser                         │
│    - Even if browser is minimized                            │
│    - Even if tab is closed (service worker runs in background) │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Service Worker Receives "push" Event                     │
│    (push-sw.js)                                              │
│                                                              │
│    self.addEventListener('push', function(event) {           │
│      const data = event.data.json();                        │
│      // Data contains: title, body, url, etc.               │
│    });                                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Service Worker Shows Notification                        │
│                                                              │
│    self.registration.showNotification(title, {               │
│      body: "What is the capital of France?",                │
│      icon: "/favicon.ico",                                  │
│      badge: "/favicon.ico",                                 │
│      vibrate: [200, 100, 200],                              │
│      actions: [                                             │
│        { action: 'answer', title: 'Answer Now' },          │
│        { action: 'dismiss', title: 'Dismiss' }             │
│      ]                                                      │
│    });                                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Windows Shows Notification                                │
│                                                              │
│    ┌─────────────────────────────────────────┐             │
│    │  🔔 Chrome                              │             │
│    │  ─────────────────────────────────────  │             │
│    │  📝 New Quiz Question!                  │             │
│    │  What is the capital of France?         │             │
│    │                                          │             │
│    │  [Answer Now]  [Dismiss]                │             │
│    └─────────────────────────────────────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Student Clicks Notification                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Service Worker Handles Click                             │
│    (push-sw.js - notificationclick event)                   │
│                                                              │
│    - Looks for existing open tab                            │
│    - If found: Focus that tab                               │
│    - If not found: Open new tab                             │
│    - Navigate to: /dashboard/student                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Quiz Popup Appears                                        │
│    (StudentDashboard.tsx receives via WebSocket too)        │
│                                                              │
│    Student sees quiz and can answer!                        │
└─────────────────────────────────────────────────────────────┘
```

### Code Flow:

**push-sw.js** - Service Worker:
```javascript
// Receive push
self.addEventListener('push', function(event) {
  const data = event.data.json();
  
  const title = data.title || '📝 New Quiz Question';
  const options = {
    body: data.body,
    icon: '/favicon.ico',
    data: {
      url: data.url || '/dashboard/student'
    },
    actions: [
      { action: 'answer', title: 'Answer Now' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle click
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  
  const urlToOpen = event.notification.data.url;
  
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(function(clientList) {
      // Focus existing tab or open new one
      for (let client of clientList) {
        if ('focus' in client) {
          return client.focus().then(() => {
            return client.navigate(urlToOpen);
          });
        }
      }
      return clients.openWindow(urlToOpen);
    })
  );
});
```

---

## Technical Details

### Architecture Diagram:

```
┌──────────────────────────────────────────────────────────────────┐
│                         PUSH NOTIFICATION SYSTEM                  │
└──────────────────────────────────────────────────────────────────┘

┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  STUDENT    │         │  INSTRUCTOR │         │   BACKEND   │
│  Browser    │         │  Browser    │         │   Server    │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                        │
       │ 1. Login (Student)    │                        │
       ├───────────────────────┼───────────────────────>│
       │                       │                        │
       │ 2. Request Permission │                        │
       │<──────────────────────┤                        │
       │                       │                        │
       │ 3. Allow              │                        │
       ├──────────────────────>│                        │
       │                       │                        │
       │ 4. Subscribe (VAPID)  │                        │
       ├───────────────────────┼───────────────────────>│
       │                       │                        │
       │                       │ 5. Trigger Question    │
       │                       ├───────────────────────>│
       │                       │                        │
       │                       │                        ├──┐
       │                       │                        │  │ 6. Query
       │                       │                        │<─┘ Questions
       │                       │                        │
       │                       │                        ├──┐
       │                       │                        │  │ 7. Load
       │                       │                        │<─┘ Subscriptions
       │                       │                        │
       │                       │                        ├──┐
       │                       │                        │  │ 8. Send to
       │                       │                        │  │ Push Service
       │                       │                        │<─┘ (FCM/Mozilla)
       │                       │                        │
       ┌──────────────────────────────────────────────────┐
       │           Push Service (Google FCM)              │
       │           or Mozilla Push Service                │
       └──────────────────────┬───────────────────────────┘
                              │
       │ 9. Deliver Push       │                        │
       │<──────────────────────┤                        │
       │                       │                        │
       ┌──────────┐            │                        │
       │ Service  │            │                        │
       │ Worker   │            │                        │
       │(push-sw) │            │                        │
       └────┬─────┘            │                        │
            │                  │                        │
       │    │ 10. Show         │                        │
       │    │ Notification     │                        │
       │<───┘                  │                        │
       │                       │                        │
       │ 🔔 WINDOWS            │                        │
       │ NOTIFICATION          │                        │
       │ APPEARS!              │                        │
       │                       │                        │
```

### Components Involved:

1. **Frontend (React)**
   - AuthContext.tsx - Triggers init after login
   - pushNotificationService.ts - Handles subscription
   - push-sw.js - Service worker

2. **Backend (FastAPI)**
   - push_notification.py - Subscription endpoints
   - push_service.py - Push sending logic
   - live.py - Trigger integration

3. **Database (MongoDB)**
   - push_subscriptions collection

4. **External Services**
   - Google FCM (Chrome/Edge)
   - Mozilla Push Service (Firefox)

5. **Browser APIs**
   - Notification API
   - Service Worker API
   - Push API

---

## Summary Flow in 10 Steps:

1. **Student logs in** → Frontend detects role = "student"
2. **Browser asks permission** → Student clicks "Allow"
3. **Service worker registers** → /push-sw.js activated
4. **Push subscription created** → Using VAPID public key
5. **Subscription sent to backend** → Saved in MongoDB
6. **Instructor triggers question** → Backend receives request
7. **Backend loads subscriptions** → From MongoDB
8. **Backend sends to push service** → Using pywebpush + VAPID private key
9. **Push service delivers** → To student's browser
10. **Service worker shows notification** → Student sees Windows notification!

---

## Why It Works Even When Browser is Closed:

- **Service Worker** runs independently of web page
- Registered with browser, not just the tab
- Browser maintains connection to push service
- Push service can wake up service worker
- Service worker can show notifications without page open

---

## Security:

- **VAPID Keys** prove backend is authorized
- **HTTPS Required** for security
- **Permission Required** from user
- **JWT Token** required to subscribe
- **Subscriptions** tied to specific student

---

This is a modern web standard used by:
- Gmail notifications
- WhatsApp Web
- Facebook notifications
- Twitter notifications
- And now... your Learning App! 🎓

