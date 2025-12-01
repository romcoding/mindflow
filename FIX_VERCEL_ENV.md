# Fix Vercel Environment Variable

## Issue Found
The `VITE_API_URL` environment variable in Vercel is incorrectly set to the **database connection string** instead of the **backend API URL**.

## Current (Wrong) Value
```
postgresql://mindflow_db_user:...@dpg-d3iia7ali9vc73es3nj0-a.frankfurt-postgres.render.com/mindflow_db
```

## Correct Value
```
https://mindflow-backend-9ec8.onrender.com/api
```

## How to Fix

### Option 1: Fix in Vercel Dashboard (Recommended)
1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Find `VITE_API_URL`
4. Update it to: `https://mindflow-backend-9ec8.onrender.com/api`
5. **Important**: Make sure to select the correct environment (Production, Preview, Development)
6. Click **Save**
7. **Redeploy** your application (go to Deployments → click the three dots → Redeploy)

### Option 2: Check Your Backend URL
If your Render backend has a different URL, use that instead. You can find it:
- In your Render dashboard
- It should look like: `https://your-service-name.onrender.com`
- Then append `/api` to it

## Verification
After fixing and redeploying:
1. Open your frontend in the browser
2. Open browser console (F12)
3. Look for: `🔗 API Base URL:`
4. It should show: `https://mindflow-backend-9ec8.onrender.com/api`
5. It should **NOT** show a `postgresql://` URL

## Code Protection
I've also added code validation that will:
- Detect if `VITE_API_URL` is set to a database connection string
- Log an error message
- Automatically fallback to the correct backend URL

However, you should still fix the environment variable in Vercel to avoid confusion.

