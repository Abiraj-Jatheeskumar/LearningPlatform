# 🚀 Setup Instructions - JWT Authentication & Bug Fixes

## ✅ What Was Done

### 1. **JWT Authentication Implementation**
- ✅ Added JWT token generation in backend (`backend/src/routers/auth.py`)
- ✅ Updated frontend to receive and store JWT tokens
- ✅ Fixed API endpoint paths (now using `/api/auth` correctly)
- ✅ Implemented secure token storage in localStorage

### 2. **Fixed 404 Error on Page Refresh**
- ✅ Added `historyApiFallback` configuration to Vite
- ✅ Now page refresh works on any route without 404 errors

### 3. **Files Modified**
- `backend/src/routers/auth.py` - Added JWT token generation
- `frontend/src/services/authService.ts` - Fixed API endpoints and added token handling
- `frontend/src/context/AuthContext.tsx` - Store/retrieve/clear JWT tokens
- `frontend/vite.config.ts` - Added history API fallback for routing

---

## 🔧 Setup Required

### **IMPORTANT: Create `.env` File in Backend**

You need to create a `.env` file in the `backend` folder with the following content:

```bash
# JWT Configuration
JWT_SECRET=your-secret-key-change-this-in-production-make-it-long-and-random-jwt-secret-2024
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=learning_platform

# Server Configuration
PORT=3001
HOST=0.0.0.0
```

**⚠️ Security Note:** 
- The `.env` file is NOT tracked by Git (it's in `.gitignore`)
- Change `JWT_SECRET` to a secure random string in production
- Never commit the `.env` file to GitHub

---

## 🏃 How to Run

### **1. Start Backend**

```bash
cd backend
python src/main.py
```

Backend will start on: `http://localhost:3001`

### **2. Start Frontend**

```bash
cd frontend
npm run dev
```

Frontend will start on: `http://localhost:5173`

---

## 🧪 Testing the Changes

### **Test JWT Token:**
1. Open browser and go to `http://localhost:5173`
2. Login with your credentials
3. Open DevTools → Application → Local Storage
4. You should see:
   - `access_token` - Your JWT token
   - `token_type` - "bearer"
   - `user` - User information

### **Test Page Refresh Fix:**
1. Login to the application
2. Navigate to any route (e.g., `/dashboard/student`)
3. Press F5 or click browser refresh
4. ✅ Should stay on the same page (no 404 error)

---

## 📡 API Endpoints

All auth endpoints now properly return JWT tokens:

### **Register:**
```
POST http://localhost:3001/api/auth/register
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "firstName": "...",
    "lastName": "...",
    "email": "...",
    "role": "student"
  }
}
```

### **Login:**
```
POST http://localhost:3001/api/auth/login
```

**Response:** Same as register

---

## 🔐 Using JWT Token in API Calls

The token is automatically included in authenticated requests:

```typescript
// Example: Making an authenticated API call
const response = await fetch(`${API_BASE_URL}/api/some-endpoint`, {
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});
```

Or use the helper function:
```typescript
import { authService } from './services/authService';
// The getAuthHeaders() function automatically adds the token
```

---

## 🎉 What's Fixed

### ✅ **Issue 1: Missing JWT Token**
- **Before:** Login/Register didn't return any token
- **After:** Both endpoints return JWT token that expires in 24 hours

### ✅ **Issue 2: 404 on Refresh**
- **Before:** Refreshing on `/dashboard/student` showed 404 error
- **After:** Page refresh works perfectly on any route

---

## 📝 Git Commit

**Commit Hash:** `e0ccc4c`

**Commit Message:**
```
Add JWT authentication and fix 404 on page refresh

- Implemented JWT token generation in backend auth endpoints
- Added JWT token storage in frontend localStorage
- Updated authService to use correct API endpoints (/api/auth)
- Fixed 404 error on page refresh by adding historyApiFallback to Vite config
- Updated AuthContext to handle token storage and cleanup on logout
```

**Pushed to:** `origin/master`

---

## 🔗 GitHub Repository

Your changes have been successfully pushed to:
- Repository: `https://github.com/Arunpragash22/learningApp.git`
- Branch: `master`

---

## 🚨 Important Notes

1. **Create `.env` file** - The app won't work without it
2. **MongoDB Required** - Make sure MongoDB is running on `localhost:27017`
3. **JWT Secret** - Use a strong, random secret in production
4. **Token Expiration** - Tokens expire after 24 hours (configurable in `.env`)

---

## 🆘 Troubleshooting

### Backend won't start:
- Check if `.env` file exists in `backend/` folder
- Check if MongoDB is running: `mongod --version`
- Check if port 3001 is available

### Frontend shows 404:
- Make sure you restarted the Vite dev server after changes
- Clear browser cache
- Try incognito mode

### Token not working:
- Check if `JWT_SECRET` is set in `.env`
- Clear localStorage and login again
- Check browser console for errors

---

**Status:** ✅ Ready for Testing & Deployment

**Last Updated:** November 21, 2025
