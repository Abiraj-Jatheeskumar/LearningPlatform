# 🚀 Heroku Backend Deployment - Complete Guide

## Prerequisites Check
✅ Heroku CLI installed (download from https://devcenter.heroku.com/articles/heroku-cli)
✅ Git installed
✅ Code pushed to GitHub

---

## Step-by-Step Deployment

### 1️⃣ Open PowerShell and Login to Heroku
```powershell
heroku login
```
(This will open browser - login with your Heroku account)

---

### 2️⃣ Navigate to Backend Folder
```powershell
cd c:\Users\aabir\OneDrive\Desktop\project_fyp-main\backend
```

---

### 3️⃣ Create Heroku App
```powershell
heroku create learning-platform-backend-2026
```
(Change the name if taken. Note the URL: https://learning-platform-backend-2026.herokuapp.com)

---

### 4️⃣ Set ALL Environment Variables (IMPORTANT!)

**MongoDB Configuration:**
```powershell
heroku config:set MONGODB_URL="mongodb+srv://admin:yCYlwlhrczrY4AJS@cluster0.grwtqbc.mongodb.net/?appName=Cluster0" -a learning-platform-backend-2026
heroku config:set DATABASE_NAME=learning_platform -a learning-platform-backend-2026
```

**JWT Configuration:**
```powershell
heroku config:set JWT_SECRET=dWSTzj8wEZRcgNHQxKmBtiuO2sXGUIFYa69yhDe7n4pC1fv53oqlJVrMkP0LbA -a learning-platform-backend-2026
heroku config:set JWT_ALGORITHM=HS256 -a learning-platform-backend-2026
heroku config:set JWT_EXPIRATION_HOURS=24 -a learning-platform-backend-2026
```

**Web Push Notifications:**
```powershell
heroku config:set VAPID_PUBLIC_KEY=BKoDWpX6VZ2DkyknDDAPlamzGLiGhPnF6nvN3wnsAygtmy3KUQ0lnelWqmzaYGadMO7024RtRjWMxeAqL6yQVcE -a learning-platform-backend-2026
heroku config:set VAPID_PRIVATE_KEY=JZGSn-nC3cVu1A7Zpr1XCOnMc9dEiSCdE--mnavJMbY -a learning-platform-backend-2026
heroku config:set VAPID_SUBJECT=mailto:admin@learningapp.com -a learning-platform-backend-2026
```

**Zoom Configuration:**
```powershell
heroku config:set ZOOM_WEBHOOK_SECRET_TOKEN=sRJPFHq7SXmfSoRyWdJLww -a learning-platform-backend-2026
```

**Email Configuration (Optional):**
```powershell
heroku config:set SMTP_HOST=smtp.gmail.com -a learning-platform-backend-2026
heroku config:set SMTP_PORT=587 -a learning-platform-backend-2026
heroku config:set SMTP_USER=zoomlearningapp@gmail.com -a learning-platform-backend-2026
heroku config:set SMTP_PASSWORD="nxhq dfsq eyax ahny" -a learning-platform-backend-2026
heroku config:set FROM_EMAIL=zoomlearningapp@gmail.com -a learning-platform-backend-2026
```

---

### 5️⃣ Verify Environment Variables
```powershell
heroku config -a learning-platform-backend-2026
```
(Check all variables are set correctly)

---

### 6️⃣ Deploy to Heroku

**Option A: Deploy from GitHub (Recommended)**
1. Go to: https://dashboard.heroku.com/apps/learning-platform-backend-2026/deploy/github
2. Connect your GitHub account
3. Search for: `LearningPlatform`
4. Click "Connect"
5. Under "Manual Deploy":
   - Select branch: `main`
   - Click "Deploy Branch"
6. Wait for build to complete

**Option B: Deploy using Git subtree**
```powershell
cd c:\Users\aabir\OneDrive\Desktop\project_fyp-main
git subtree push --prefix backend heroku main
```

---

### 7️⃣ Check Deployment Status
```powershell
heroku logs --tail -a learning-platform-backend-2026
```
(Press Ctrl+C to exit logs)

---

### 8️⃣ Test Backend
```powershell
curl https://learning-platform-backend-2026.herokuapp.com/health
```
Should return: `{"status":"ok","time":"..."}`

Or visit in browser: https://learning-platform-backend-2026.herokuapp.com/docs

---

### 9️⃣ Seed the Database (After First Deploy)
```powershell
heroku run python src/database/seed.py -a learning-platform-backend-2026
```

---

### 🔟 Enable CORS for Frontend
The backend is already configured to allow all origins (`allow_origins=["*"]`), so it will work with any frontend URL.

---

## ✅ Success Checklist

- [ ] Heroku app created
- [ ] All environment variables set
- [ ] Code deployed successfully
- [ ] `/health` endpoint returns 200 OK
- [ ] Database seeded with default users
- [ ] API docs accessible at `/docs`

---

## 🆘 Troubleshooting

**Build Failed:**
```powershell
heroku logs --tail -a learning-platform-backend-2026
```

**Application Error (H10):**
- Check if all environment variables are set: `heroku config`
- Check buildpack: `heroku buildpacks -a learning-platform-backend-2026`
- Should be: `heroku/python`

**Database Connection Error:**
- Verify MongoDB Atlas allows connections from anywhere (0.0.0.0/0)
- Check MONGODB_URL is correct

**Restart App:**
```powershell
heroku restart -a learning-platform-backend-2026
```

---

## 📝 Your Backend URL
After successful deployment, your backend will be at:
**https://learning-platform-backend-2026.herokuapp.com**

Save this URL - you'll need it for the frontend!

---

## Next Step: Update Frontend
After backend is deployed, update frontend `.env`:
```
VITE_API_URL=https://learning-platform-backend-2026.herokuapp.com
```
Then redeploy frontend to Vercel.
