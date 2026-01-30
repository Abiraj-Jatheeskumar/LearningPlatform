# 🚀 Deploy Quiz Fix to Heroku - Quick Guide

## Current Status
- ✅ Code committed and pushed to GitHub (main branch)
- ✅ Heroku app: `learning-platform-backend-2026`
- ✅ Heroku remote configured

## Option 1: Check if Auto-Deploy is Enabled (Recommended)

### Check Heroku Dashboard
1. Go to: https://dashboard.heroku.com/apps/learning-platform-backend-2026/deploy/github
2. Check if:
   - ✅ GitHub is connected
   - ✅ "Wait for CI to pass before deploy" is OFF (or your CI passes)
   - ✅ "Automatic deploys" is ENABLED for `main` branch

**If Auto-Deploy is ENABLED:**
- ✅ **You're done!** The changes will deploy automatically within 1-2 minutes
- Just wait and check: https://learning-platform-backend-2026-21c17163e87a.herokuapp.com/health

**If Auto-Deploy is NOT enabled:**
- Follow Option 2 below

---

## Option 2: Manual Deploy (If Auto-Deploy is OFF)

### Method A: Deploy via Heroku Dashboard (Easiest)
1. Go to: https://dashboard.heroku.com/apps/learning-platform-backend-2026/deploy/github
2. Under "Manual Deploy":
   - Select branch: `main`
   - Click **"Deploy Branch"**
3. Wait for build to complete (2-3 minutes)
4. Check deployment status

### Method B: Deploy via Git Subtree (Command Line)
```powershell
# Navigate to project root
cd c:\Users\aabir\OneDrive\Desktop\project_fyp-main

# Deploy backend folder to Heroku
git subtree push --prefix backend heroku main
```

**Note:** This pushes only the `backend/` folder to Heroku, which is correct since your Procfile is in the backend folder.

---

## Option 3: Deploy via Heroku CLI (Alternative)
```powershell
# Navigate to backend folder
cd c:\Users\aabir\OneDrive\Desktop\project_fyp-main\backend

# Push to Heroku
git push heroku main
```

**Note:** This requires the backend folder to be a git repository or you need to use subtree method.

---

## ✅ Verify Deployment

### 1. Check Deployment Status
```powershell
heroku logs --tail -a learning-platform-backend-2026
```
Look for:
- ✅ "Build succeeded"
- ✅ "State changed from starting to up"
- ✅ No errors

### 2. Test Health Endpoint
```powershell
curl https://learning-platform-backend-2026-21c17163e87a.herokuapp.com/health
```
Should return: `{"status":"ok","time":"...","database":{...}}`

Or visit in browser:
https://learning-platform-backend-2026-21c17163e87a.herokuapp.com/health

### 3. Test the Fix
1. Create a session
2. Have students join the session
3. Instructor triggers quiz
4. ✅ Students should receive quiz questions

---

## 🔍 Troubleshooting

### If Build Fails:
```powershell
heroku logs --tail -a learning-platform-backend-2026
```
Check for:
- Missing dependencies in `requirements.txt`
- Environment variables not set
- Python version mismatch

### If App Crashes:
```powershell
# Check recent logs
heroku logs --tail -a learning-platform-backend-2026

# Restart the app
heroku restart -a learning-platform-backend-2026
```

### If Changes Don't Appear:
1. Clear Heroku build cache:
   ```powershell
   heroku builds:cache:purge -a learning-platform-backend-2026
   ```
2. Redeploy

---

## 📝 Quick Reference

**Heroku App Name:** `learning-platform-backend-2026`  
**Heroku URL:** https://learning-platform-backend-2026-21c17163e87a.herokuapp.com/  
**GitHub Repo:** https://github.com/Abiraj-Jatheeskumar/LearningPlatform  
**Branch:** `main`

---

## ⚡ Fastest Method

**If you're not sure about auto-deploy:**
1. Go to Heroku Dashboard: https://dashboard.heroku.com/apps/learning-platform-backend-2026/deploy/github
2. Click "Deploy Branch" (manual deploy)
3. Wait 2-3 minutes
4. Done! ✅

