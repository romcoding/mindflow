# Security Policy — MindFlow / Rovot

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.x     | Yes       |
| 1.x     | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue.
2. Email the repository owner with details.
3. Include steps to reproduce, potential impact, and any suggested fix.
4. We will acknowledge receipt within 48 hours and provide a timeline for resolution.

---

## Security Architecture

### Authentication and Authorization

| Layer | Mechanism | Details |
|-------|-----------|---------|
| Password hashing | bcrypt | Cost factor 12, salted |
| Session tokens | JWT (HS256) | 24-hour access, 30-day refresh |
| API authentication | Bearer tokens | Sent via `Authorization` header |
| Rate limiting | Flask-Limiter | Per-IP and per-user limits |
| Login/Register | Rate-limited | 5/hour/IP (register), 20/hour/IP (login) |

### Data Protection

| Data Type | Protection | Storage |
|-----------|-----------|---------|
| Passwords | bcrypt hash | Database |
| Email credentials | Fernet (AES-128-CBC) | Database (encrypted) |
| API keys | Fernet encryption | Database (encrypted) |
| JWT secrets | Environment variable | Never committed to VCS |

### Network Security

All production deployments enforce:

- **HTTPS only** — HSTS header with `max-age=31536000`
- **CORS** — Strict origin allowlist in production
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`
- **Request size limits** — 16 MB maximum
- **Webhook signature verification** — HMAC-SHA256 for WhatsApp, shared secret for Signal

### Input Validation

- All user input is sanitized before processing
- SQL injection prevented via SQLAlchemy parameterised queries
- XSS prevented via React's default escaping and CSP headers
- Path traversal prevented in file watcher (restricted to configured directories)
- Null bytes stripped from all input

---

## Production Deployment Checklist

Before deploying to production, verify the following:

### Required Environment Variables

```bash
# MUST be changed from defaults
JWT_SECRET_KEY=<random-64-char-string>
SECRET_KEY=<random-64-char-string>
POSTGRES_PASSWORD=<strong-password>

# Generate secure values with:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Configuration

- [ ] `FLASK_ENV=production` is set
- [ ] `JWT_SECRET_KEY` is a cryptographically random string (min 32 bytes)
- [ ] `SECRET_KEY` is a cryptographically random string (min 32 bytes)
- [ ] `CORS_ORIGINS` is set to your frontend domain(s) only
- [ ] `DATABASE_URL` uses SSL (`sslmode=require`)
- [ ] Debug endpoints are disabled (automatic when `FLASK_ENV=production`)
- [ ] Default passwords are changed
- [ ] API keys are stored as environment variables, never in code
- [ ] Never deploy with Flask `debug=True` in production

### Docker Security

- [ ] Container runs as non-root user (`rovot`)
- [ ] Multi-stage build (no build tools in runtime image)
- [ ] Health checks configured
- [ ] Resource limits set in `docker-compose.prod.yml`
- [ ] No `.env` files in Docker image (`.dockerignore`)

### Messaging Channels

- [ ] WhatsApp: `WHATSAPP_APP_SECRET` set for webhook signature verification
- [ ] Signal: `SIGNAL_WEBHOOK_SECRET` set for webhook authentication
- [ ] Telegram: Bot token stored as environment variable only
- [ ] All webhook URLs use HTTPS

### Multi-Tenancy

- All user-owned data is restricted on API to the requesting user
- To further isolate user data, implement teams/organizations (each user/resource has a `tenant_id`) and check every query for ownership/tenant matching

### Monitoring

- [ ] Health check endpoint (`/api/health`) is monitored
- [ ] Error logging is configured (stdout for containers)
- [ ] Log rotation is configured (Docker JSON driver with size limits)
- [ ] Sensitive data is redacted from logs
- [ ] All login/register attempts are logged

---

## Known Limitations

1. **Base64 fallback**: If the `cryptography` package is not installed, credential encryption falls back to base64 encoding, which is NOT secure. Always install `cryptography` in production.

2. **In-memory state**: Channel links and pending tokens are stored in memory. In a multi-worker deployment, use Redis or database-backed sessions.

3. **File watcher**: Only available in desktop/local deployments. Cloud deployments should use the email checker and messaging channels instead.

4. **Rate limiting**: Uses in-memory storage by default. For multi-worker deployments, configure `REDIS_URL` for distributed rate limiting.

---

## Recommendations

- Consider enabling Multi-Factor Authentication (MFA/2FA) for increased security
- Rotate JWT secret keys periodically
- Back up audit logs securely
- Monitor for suspicious access patterns (excessive logins, failed attempts, etc.)

## Dependencies

All dependencies are pinned to specific versions in `requirements.txt` to prevent supply-chain attacks. Regular dependency audits should be performed:

```bash
pip audit
npm audit  # for frontend
```
