# 🔔 Web Push Notifications Setup Guide

This guide explains how to set up Web Push Notifications for the Learning App.

## 📋 Prerequisites

- Python 3.8+ with `pywebpush` installed
- Node.js for frontend
- HTTPS domain (or localhost for development)

## 🔐 Step 1: Generate VAPID Keys

VAPID keys are required for Web Push authentication. Generate them using:

### Using Python:
```bash
cd backend
pip install pywebpush
python -c "from pywebpush import vapid; print(vapid.Vapid().generate_keys().save_public_key()); print(vapid.Vapid().generate_keys().save_private_key())"
```

### Using npx (alternative):
```bash
npx web-push generate-vapid-keys
```

You'll get output like:
```
Public Key: BCwZXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Private Key: YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
```

## ⚙️ Step 2: Configure Environment Variables

### Backend (.env):
```env
# VAPID Keys for Web Push
VAPID_PUBLIC_KEY=BCwZXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
VAPID_PRIVATE_KEY=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
VAPID_SUBJECT=mailto:admin@learningapp.com
```

### Frontend (.env):
```env
VITE_API_URL=https://learningapp-production.up.railway.app
VITE_WS_URL=wss://learningapp-production.up.railway.app
VITE_VAPID_PUBLIC_KEY=BCwZXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Important:** Use the SAME public key in both backend and frontend!

## 📦 Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs `pywebpush==1.14.0` which is required for sending push notifications.

## 🚀 Step 4: Deploy & Test

### Development (localhost):
1. Start backend: `cd backend && uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Login as a student
4. Accept notification permission when prompted
5. As instructor, trigger a question
6. Student should see a Windows notification!

### Production (HTTPS):
1. Deploy backend with VAPID keys in environment variables
2. Deploy frontend with VAPID_PUBLIC_KEY in environment
3. Ensure service worker is accessible at `/push-sw.js`
4. Test notification flow

## 🔧 How It Works

### Flow Diagram:
```
1. Student logs in
   ↓
2. Frontend requests notification permission
   ↓
3. Service worker registers at /push-sw.js
   ↓
4. Frontend subscribes using VAPID public key
   ↓
5. Subscription sent to backend API
   ↓
6. Backend saves subscription to MongoDB
   ↓
7. Instructor triggers question
   ↓
8. Backend sends push notification using VAPID private key
   ↓
9. Service worker receives push event
   ↓
10. Windows notification appears!
    ↓
11. Student clicks notification
    ↓
12. Tab opens/focuses on quiz page
```

## 📂 Files Created/Modified

### Backend:
- ✅ `backend/requirements.txt` - Added `pywebpush==1.14.0`
- ✅ `backend/src/routers/push_notification.py` - Subscribe/unsubscribe endpoints
- ✅ `backend/src/services/push_service.py` - Push notification helper
- ✅ `backend/src/routers/live.py` - Integrated push notifications
- ✅ `backend/src/main.py` - Registered push notification router

### Frontend:
- ✅ `frontend/public/push-sw.js` - Service worker
- ✅ `frontend/src/services/pushNotificationService.ts` - Push notification service
- ✅ `frontend/src/context/AuthContext.tsx` - Auto-init on student login

### Database:
- ✅ MongoDB collection: `push_subscriptions`
  - Fields: `studentId`, `endpoint`, `keys`, `createdAt`, `updatedAt`

## 🧪 Testing

### Test Push Notifications:
1. Open browser DevTools (F12)
2. Go to "Application" tab → "Service Workers"
3. Verify `/push-sw.js` is registered
4. Login as student → Accept permission
5. Check Console for: `✅ Push notifications enabled`
6. As instructor, click "Trigger Question"
7. Windows notification should appear!

### Troubleshooting:

**No notification permission prompt?**
- Check if permission is already denied in browser settings
- Try in incognito mode
- Verify HTTPS or localhost

**Service worker not registering?**
- Check `/push-sw.js` is accessible
- Clear browser cache
- Check console for errors

**Push not sending?**
- Verify VAPID keys are correct
- Check backend logs for errors
- Verify subscription was saved to MongoDB

**Notification not appearing?**
- Check Windows notification settings
- Verify browser notification permission
- Check service worker console logs

## 🔒 Security Notes

- ✅ VAPID private key is server-side only
- ✅ Subscriptions require JWT authentication
- ✅ Only students can subscribe
- ✅ Expired subscriptions auto-removed (410 status)
- ✅ Works on HTTPS + localhost only

## 📱 Browser Support

| Browser | Support |
|---------|---------|
| Chrome | ✅ Full |
| Edge | ✅ Full |
| Firefox | ✅ Full |
| Safari | ⚠️ Limited |
| Opera | ✅ Full |

## 🎯 Features

- ✅ System-style Windows notifications
- ✅ Works when browser is closed
- ✅ Click notification opens quiz page
- ✅ Auto-subscribes after student login
- ✅ Handles expired subscriptions
- ✅ Action buttons (Answer/Dismiss)
- ✅ Vibration on mobile
- ✅ Custom icon and badge

## 📚 API Endpoints

### Subscribe to Push:
```
POST /api/notifications/subscribe
Headers: Authorization: Bearer <token>
Body: {
  "endpoint": "https://...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

### Unsubscribe:
```
DELETE /api/notifications/unsubscribe?endpoint=<encoded_endpoint>
Headers: Authorization: Bearer <token>
```

### Trigger Question (sends push):
```
POST /api/live/trigger/{meeting_id}
```

## ✅ Verification Checklist

- [ ] VAPID keys generated
- [ ] Environment variables configured (backend & frontend)
- [ ] pywebpush installed
- [ ] Service worker accessible at `/push-sw.js`
- [ ] Student can login and see permission prompt
- [ ] Subscription saved to MongoDB
- [ ] Instructor can trigger question
- [ ] Windows notification appears
- [ ] Clicking notification opens quiz page
- [ ] Works on both development and production

## 🆘 Support

If you encounter issues:
1. Check browser console for errors
2. Check backend logs for push sending errors
3. Verify VAPID keys match
4. Test in different browser
5. Clear browser cache and try again

---

**Created by:** AI Assistant
**Date:** 2025-11-25
**Version:** 1.0.0

