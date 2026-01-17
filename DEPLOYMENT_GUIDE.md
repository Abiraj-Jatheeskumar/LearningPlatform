# 🚀 Deployment Guide: Vercel + Heroku

## Part 1: Deploy Backend to Heroku

### Step 1: Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Login to Heroku
```bash
heroku login
```

### Step 3: Create Heroku App
```bash
cd backend
heroku create your-app-name-backend
```

### Step 4: Set Environment Variables on Heroku
```bash
heroku config:set PORT=3001
heroku config:set MONGODB_URL="mongodb+srv://admin:yCYlwlhrczrY4AJS@cluster0.grwtqbc.mongodb.net/?appName=Cluster0"
heroku config:set DATABASE_NAME=learning_platform
heroku config:set JWT_SECRET=dWSTzj8wEZRcgNHQxKmBtiuO2sXGUIFYa69yhDe7n4pC1fv53oqlJVrMkP0LbA
heroku config:set JWT_ALGORITHM=HS256
heroku config:set JWT_EXPIRATION_HOURS=24
heroku config:set VAPID_PUBLIC_KEY=BKoDWpX6VZ2DkyknDDAPlamzGLiGhPnF6nvN3wnsAygtmy3KUQ0lnelWqmzaYGadMO7024RtRjWMxeAqL6yQVcE
heroku config:set VAPID_PRIVATE_KEY=JZGSn-nC3cVu1A7Zpr1XCOnMc9dEiSCdE--mnavJMbY
heroku config:set VAPID_SUBJECT=mailto:admin@learningapp.com
heroku config:set ZOOM_WEBHOOK_SECRET_TOKEN=sRJPFHq7SXmfSoRyWdJLww
```

### Step 5: Deploy to Heroku
```bash
cd c:\Users\aabir\OneDrive\Desktop\project_fyp-main
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a your-app-name-backend
git push heroku main
```

### Step 6: Get Your Backend URL
After deployment, your backend URL will be: `https://your-app-name-backend.herokuapp.com`

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Update Frontend .env
Before deploying, update `frontend/.env`:
```
VITE_API_URL=https://your-app-name-backend.herokuapp.com
VITE_VAPID_PUBLIC_KEY=BKoDWpX6VZ2DkyknDDAPlamzGLiGhPnF6nvN3wnsAygtmy3KUQ0lnelWqmzaYGadMO7024RtRjWMxeAqL6yQVcE
```

### Step 2: Install Vercel CLI (Optional)
```bash
npm install -g vercel
```

### Step 3: Deploy to Vercel (Method 1 - Using Vercel Dashboard)
1. Go to https://vercel.com/
2. Sign up/Login with GitHub
3. Click "Add New Project"
4. Import your GitHub repository (or upload folder)
5. Select the `frontend` folder as root directory
6. Set **Environment Variables** in Vercel dashboard:
   - `VITE_API_URL` = `https://your-app-name-backend.herokuapp.com`
   - `VITE_VAPID_PUBLIC_KEY` = `BKoDWpX6VZ2DkyknDDAPlamzGLiGhPnF6nvN3wnsAygtmy3KUQ0lnelWqmzaYGadMO7024RtRjWMxeAqL6yQVcE`
7. Build Settings:
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
8. Click "Deploy"

### Step 3: Deploy to Vercel (Method 2 - Using CLI)
```bash
cd frontend
vercel
```
Follow the prompts and add environment variables when asked.

---

## Part 3: Update Backend CORS for Vercel

After you get your Vercel URL (e.g., `https://your-app.vercel.app`), update backend to allow it.

Your backend already has `allow_origins=["*"]` in `src/main.py`, so it should work immediately.

---

## Testing Deployment

1. **Test Backend**: Visit `https://your-app-name-backend.herokuapp.com/health`
   - Should return: `{"status":"ok","time":"..."}`

2. **Test Frontend**: Visit `https://your-app.vercel.app`
   - Try to login with: `student@example.com` / `password123`

---

## Troubleshooting

### Backend Issues:
- Check logs: `heroku logs --tail`
- Restart: `heroku restart`

### Frontend Issues:
- Check Vercel deployment logs in dashboard
- Ensure environment variables are set correctly
- Clear build cache and redeploy

---

## Important Notes

✅ **Files Created:**
- `backend/Procfile` - Tells Heroku how to run the app
- `backend/runtime.txt` - Specifies Python version
- Frontend already has `vercel.json` configured

✅ **Security:**
- Never commit `.env` files to Git
- Use environment variables in deployment platforms
- Consider changing JWT_SECRET for production

✅ **Database:**
- MongoDB Atlas is already cloud-based, no changes needed
- Make sure MongoDB Atlas allows connections from anywhere (0.0.0.0/0)
