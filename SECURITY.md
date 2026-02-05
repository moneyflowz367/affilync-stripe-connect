# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing:
**security@affilync.com**

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Measures

### Authentication & Authorization
- OAuth 2.0 (Stripe Connect) for account authorization
- JWT tokens with short expiration for session management
- Stripe webhook signature verification using stripe-signature header

### Data Protection
- Fernet encryption (AES-128-CBC) for sensitive data at rest
- PBKDF2 key derivation with 100,000 iterations
- TLS 1.3 for all data in transit
- No PII stored beyond what's necessary for operation
- Connected account tokens stored encrypted

### API Security
- Rate limiting on all endpoints
- Input validation via Pydantic schemas
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via React's automatic escaping
- CORS restricted to Affilync domains

### Infrastructure
- Render.com managed infrastructure
- Automatic security patches
- Environment variables for secrets (never in code)
- Secrets detection in pre-commit hooks

### Webhook Security
- Stripe signature verification using `stripe.Webhook.construct_event()`
- Timestamp validation (300 second tolerance)
- Idempotency via event ID deduplication
- Webhook logging for audit trail

### Stripe-Specific Security
- Uses Stripe's official Python SDK
- API keys never exposed to frontend
- Connected account tokens scoped to required permissions only
- Webhook endpoint secret for signature verification

## Security Best Practices for Contributors

1. Never commit secrets, API keys, or credentials
2. Use environment variables for all sensitive configuration
3. Validate all user input
4. Use parameterized queries (handled by SQLAlchemy)
5. Keep dependencies updated
6. Run security scans before merging (bandit, detect-secrets)
7. Never log sensitive Stripe data (card numbers, account tokens)
