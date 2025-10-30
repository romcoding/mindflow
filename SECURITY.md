# Security Policy for MindFlow

## Production HTTPS
- Always serve MindFlow (frontend and backend) via HTTPS in production.
- Use a managed platform (Render/Vercel/Railway) or deploy behind a reverse proxy with SSL (e.g. NGINX, Caddy).
- Never deploy with Flask debug=True in production!

## Authentication
- JWT (with access/refresh tokens)
- Bcrypt password hashing
- Strong password policy enforced on register/change-password
- Rate-limited /auth/register (5/hour/IP) and /auth/login (20/hour/IP)
- All login/register attempts are logged (see `auth_audit.log` in backend root)
- All user-owned data is always restricted on API to the requesting user

## Multi-Tenancy
- To further isolate user data, implement teams/organizations (each user/resource has a tenant_id) and check every query for ownership/tenant matching.
- See backend models for recommended pattern.

## Recommendations
- Consider enabling Multi-Factor Authentication (MFA/2FA) for increased security.
- Rotate JWT secret keys periodically.
- Back up audit logs securely.
- Monitor for suspicious access patterns (excessive logins, failed attempts, etc.)

## Contact
For vulnerabilities or incidents, contact the developer/maintainer.
