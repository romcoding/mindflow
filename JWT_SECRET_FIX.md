# JWT Secret Key Configuration Fix

## Problem
Tokens are being created successfully but immediately rejected as "Invalid token" when used in API requests.

## Root Cause
The `JWT_SECRET_KEY` environment variable in Render might not be set, or it might be different from what was used to create previous tokens. Flask-JWT-Extended requires the same secret key to both create and validate tokens.

## Solution

### Option 1: Set JWT_SECRET_KEY in Render (Recommended)
1. Go to your Render backend service dashboard
2. Navigate to **Environment** tab
3. Add or update `JWT_SECRET_KEY`:
   - If you already have `SECRET_KEY` set, you can use the same value
   - Or generate a new secure random string (at least 32 characters)
4. **Important**: Once set, all existing tokens will be invalidated
5. Users will need to log in again

### Option 2: Use SECRET_KEY as Fallback (Current Implementation)
The code now automatically uses `SECRET_KEY` if `JWT_SECRET_KEY` is not set. This ensures consistency.

**However**, if `SECRET_KEY` changes, all tokens become invalid.

## Verification

After setting the environment variable:
1. Check Render logs for: `JWT configured: algorithm=HS256, secret_key_set=True`
2. Users should log out and log back in
3. New tokens should work correctly

## Best Practice

For production:
- Set both `SECRET_KEY` and `JWT_SECRET_KEY` to the same value
- Or set `JWT_SECRET_KEY` to a different secure value (but keep it stable)
- Never change these values without warning users (they'll need to re-login)

## Current Status

The code now:
- Uses `SECRET_KEY` as fallback if `JWT_SECRET_KEY` is not set
- Logs JWT configuration on startup
- Provides detailed error messages for invalid tokens

