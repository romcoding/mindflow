# OAuth Setup Guide

This guide explains how to configure OAuth authentication (Google and GitHub) for MindFlow.

## Prerequisites

- Backend deployed on Render (or similar)
- Frontend deployed on Vercel (or similar)
- Access to Google Cloud Console and GitHub Developer Settings

## Google OAuth Setup

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Configure the OAuth consent screen if prompted:
   - Choose **External** user type
   - Fill in app information
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if needed
6. Create OAuth client ID:
   - Application type: **Web application**
   - Name: MindFlow
   - Authorized redirect URIs:
     - `https://your-backend-url.onrender.com/api/auth/oauth/google/callback`
     - For local development: `http://localhost:5000/api/auth/oauth/google/callback`
7. Copy the **Client ID** and **Client Secret**

### 2. Configure Backend Environment Variables

Add these to your Render backend environment variables:

```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FRONTEND_URL=https://your-frontend-url.vercel.app
```

## GitHub OAuth Setup

### 1. Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in the form:
   - **Application name**: MindFlow
   - **Homepage URL**: `https://your-frontend-url.vercel.app`
   - **Authorization callback URL**: 
     - `https://your-backend-url.onrender.com/api/auth/oauth/github/callback`
     - For local development: `http://localhost:5000/api/auth/oauth/github/callback`
4. Click **Register application**
5. Copy the **Client ID**
6. Click **Generate a new client secret** and copy it

### 2. Configure Backend Environment Variables

Add these to your Render backend environment variables:

```
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
FRONTEND_URL=https://your-frontend-url.vercel.app
```

## Security Best Practices

1. **Never commit secrets to version control**
   - Use environment variables for all OAuth credentials
   - Use `.env` files locally (and add them to `.gitignore`)

2. **Use HTTPS in production**
   - OAuth requires HTTPS for production
   - Set `SESSION_COOKIE_SECURE=true` in production

3. **Rotate secrets regularly**
   - Update OAuth secrets periodically
   - Revoke old secrets when rotating

4. **Monitor OAuth usage**
   - Check OAuth logs in your backend
   - Monitor for suspicious activity

## Testing OAuth Locally

1. Set up local environment variables:
   ```bash
   export GOOGLE_CLIENT_ID=your-client-id
   export GOOGLE_CLIENT_SECRET=your-client-secret
   export GITHUB_CLIENT_ID=your-client-id
   export GITHUB_CLIENT_SECRET=your-client-secret
   export FRONTEND_URL=http://localhost:5173
   ```

2. Make sure your OAuth apps have localhost redirect URIs configured

3. Start your backend and frontend

4. Test the OAuth flow by clicking the Google/GitHub buttons

## Troubleshooting

### "OAuth not configured" error
- Check that environment variables are set correctly
- Verify variable names match exactly (case-sensitive)

### "Invalid redirect URI" error
- Ensure the redirect URI in your OAuth app matches exactly
- Check for trailing slashes or protocol mismatches (http vs https)

### "State mismatch" error
- This is a security feature - ensure sessions are working
- Check that `SECRET_KEY` is set in backend

### OAuth buttons don't work
- Check browser console for errors
- Verify backend is accessible
- Check CORS settings

## Database Migration

After deploying, you may need to run a database migration to add OAuth fields:

```python
# The User model now includes:
# - oauth_provider (nullable)
# - oauth_provider_id (nullable)
# - avatar_url (nullable)
# - password_hash (now nullable for OAuth users)
```

The application will automatically create these columns on first run if using SQLAlchemy's `create_all()`.

