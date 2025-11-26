# 🔧 Debug Push Notifications - Step by Step

## Step 1: Check Browser Console (MOST IMPORTANT!)

1. Open your website (localhost or production)
2. Press **F12** to open DevTools
3. Go to **Console** tab
4. Look for these messages:

### ✅ GOOD Messages (What you SHOULD see):
```
🔔 Initializing push notifications...
✅ Notification permission: granted
✅ Service worker registered
✅ Push subscription created
✅ Subscription saved to backend
✅ Push notifications enabled
```

### ❌ BAD Messages (Problems):
```
❌ Push notifications not supported
❌ Notification permission: denied
❌ Service worker registration failed
❌ Push subscription failed
❌ Failed to save subscription to backend
```

**What do YOU see in console?** This tells us exactly what's wrong.

---

## Step 2: Check Notification Permission

### In Browser:
1. Click the **🔒 lock icon** next to URL
2. Look for **Notifications**
3. Should say **"Allow"** or **"Allowed"**

### If it says "Block" or "Denied":
1. Click on it → Select **"Allow"**
2. Refresh the page
3. Login again as student

### In Windows Settings:
1. Press **Windows + I**
2. Go to **System** → **Notifications**
3. Make sure notifications are **ON**
4. Scroll down → Find your browser (Chrome/Edge)
5. Make sure browser notifications are **ON**

---

## Step 3: Check Service Worker

### In Browser DevTools:
1. Press **F12**
2. Go to **Application** tab
3. Click **Service Workers** (left sidebar)
4. Should see: `/push-sw.js` with status **"activated and running"**

### If NOT there:
- Check if file exists: Go to `http://localhost:5173/push-sw.js`
- Should show the service worker code
- If 404 error → File is missing!

---

## Step 4: Check Login Role

**IMPORTANT:** Only **STUDENTS** get notifications!

1. Login as **STUDENT** (not instructor)
2. Wait for permission prompt
3. Click **"Allow"**
4. Check console for `✅ Push notifications enabled`

---

## Step 5: Check Backend Logs

When instructor triggers question, backend should show:

```
✅ Question broadcast via WebSocket to X students
✅ Push notifications sent to X students
```

If you see:
```
❌ Cannot send push: VAPID keys not configured
No push subscriptions found
```
→ VAPID keys not set or student not subscribed!

---

## Step 6: Manual Test Commands

### Test 1: Check if VAPID keys are loaded (Backend)
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Public:', os.getenv('VAPID_PUBLIC_KEY')); print('Private:', os.getenv('VAPID_PRIVATE_KEY'))"
```

Should show your keys. If "None" → Keys not in .env!

### Test 2: Check if frontend has VAPID key
Open browser console and type:
```javascript
console.log(import.meta.env.VITE_VAPID_PUBLIC_KEY)
```

Should show your public key. If "undefined" → Not in frontend .env!

### Test 3: Check MongoDB for subscriptions
```bash
# Check if student subscription was saved
# In MongoDB, look for collection: push_subscriptions
# Should have at least 1 document with studentId
```

---

## Step 7: Test Notification Manually

### In Browser Console, paste this:
```javascript
if ('Notification' in window) {
  Notification.requestPermission().then(permission => {
    if (permission === 'granted') {
      new Notification('Test', { body: 'If you see this, notifications work!' });
    }
  });
}
```

If you see notification → System works, problem is in our code!
If NO notification → System/browser blocking!

---

## Common Problems & Solutions

### Problem 1: "Notification permission: denied"
**Solution:**
- Click lock icon → Allow notifications
- Or go to browser settings → Site settings → Notifications → Allow

### Problem 2: "Service worker not registered"
**Solution:**
- Check `/push-sw.js` exists in `frontend/public/`
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh (Ctrl+F5)

### Problem 3: "Failed to save subscription to backend"
**Solution:**
- Check backend is running
- Check JWT token exists (login again)
- Check backend logs for errors
- Verify API URL is correct in .env

### Problem 4: "VAPID keys not configured"
**Solution:**
- Verify backend/.env has all 3 VAPID variables
- Verify frontend/.env has VITE_VAPID_PUBLIC_KEY
- Restart both servers after adding keys

### Problem 5: "No push subscriptions found"
**Solution:**
- Student never subscribed
- Login as student → Accept permission
- Check console for "✅ Subscription saved to backend"

### Problem 6: Notifications work on localhost but not production
**Solution:**
- Add VAPID keys to Railway environment variables
- Add VITE_VAPID_PUBLIC_KEY to Vercel environment variables
- Redeploy both services
- Clear browser cache on production site

---

## Quick Checklist

- [ ] Logged in as STUDENT (not instructor)
- [ ] Browser asked for notification permission
- [ ] Clicked "Allow" on permission prompt
- [ ] Console shows "✅ Push notifications enabled"
- [ ] Service worker shows as "activated" in DevTools
- [ ] Backend .env has all 3 VAPID variables
- [ ] Frontend .env has VITE_VAPID_PUBLIC_KEY
- [ ] Both servers restarted after adding keys
- [ ] Windows notifications are enabled
- [ ] Browser notifications are enabled for site
- [ ] MongoDB has push_subscriptions collection with data

---

## Still Not Working?

**Send me:**
1. Screenshot of browser console (F12 → Console tab)
2. Screenshot of Service Workers tab (F12 → Application → Service Workers)
3. Screenshot of notification permission (click lock icon)
4. Are you testing on localhost or production?
5. What browser are you using?

This will help me find the exact problem! 🔍

