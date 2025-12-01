# Debugging Authentication Issues

## Current Issue
Login/Registration showing "Request failed. Please try again." error with no backend logs.

## Debugging Steps Added

### Frontend Changes
1. **Enhanced API Logging** (`mindflow-frontend/src/lib/api.js`):
   - Logs all API requests with method, URL, and data
   - Better error logging for network issues
   - Shows request configuration on errors

2. **Enhanced Auth Logging** (`mindflow-frontend/src/hooks/useAuth.jsx`):
   - Logs login/registration attempts with data (without passwords)
   - Logs full error objects for debugging
   - Better error message extraction

### Backend Changes
1. **Better Error Handling** (`mindflow-backend/src/routes/auth.py`):
   - Checks for null JSON data
   - Logs registration/login attempts
   - More descriptive error messages

2. **CORS Improvements** (`mindflow-backend/src/main.py`):
   - Explicitly sets `supports_credentials=False`
   - Adds `X-Requested-With` to allowed headers

## How to Debug

### 1. Check Browser Console
After deploying, check the browser console for:
- `🔗 API Base URL:` - Should show the correct backend URL
- `🚀 API Request:` - Shows each request being made
- `🔐 Attempting login with:` or `📝 Registering with:` - Shows the data being sent
- Any CORS errors or network errors

### 2. Verify Backend URL
Check that `VITE_API_URL` in Vercel matches your Render backend URL:
- Should be: `https://mindflow-backend-9ec8.onrender.com/api`
- Or your custom Render URL

### 3. Test Backend Directly
Test the backend endpoint directly:
```bash
curl -X POST https://mindflow-backend-9ec8.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### 4. Check Render Logs
- Go to Render dashboard
- Check service logs for any errors
- Look for the logging.info messages we added

### 5. Check CORS
If you see CORS errors in browser console:
- Verify `ALLOWED_ORIGINS` in Render environment variables
- Should include your Vercel frontend URL
- Or leave unset to allow all origins (current default)

## Common Issues

### Issue: "Request failed. Please try again."
**Possible causes:**
1. Backend URL is incorrect
2. Backend is not responding
3. CORS is blocking the request
4. Network/firewall issue

**Solution:**
- Check browser console for actual error
- Verify backend URL in Vercel environment variables
- Test backend health endpoint: `https://mindflow-backend-9ec8.onrender.com/health`

### Issue: No logs in Render
**Possible causes:**
1. Request never reaches backend (CORS/network issue)
2. Logs are not being displayed
3. Backend is not deployed

**Solution:**
- Check Render service status
- Check if backend is accessible via curl
- Check Render logs tab (not just service logs)

### Issue: CORS errors
**Solution:**
- Add frontend URL to `ALLOWED_ORIGINS` in Render
- Or ensure CORS allows all origins (current default)

## Next Steps
1. Deploy these changes
2. Check browser console for detailed logs
3. Share the console output if issue persists

