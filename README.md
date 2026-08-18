# Bastion

A task management REST API built with Django REST Framework, designed around
a security-first engineering approach. The task management functionality
itself is intentionally simple — the focus of this project is on identifying,
testing, and fixing real security issues throughout development.

## Tech Stack

- **Backend:** Python, Django, Django REST Framework
- **Auth:** JWT (djangorestframework-simplejwt) with refresh token rotation
- **CI/CD:** GitHub Actions
- **Security:** Bandit (SAST), custom rate limiting, audit logging
- **Containerization:** Docker (multi-stage build, non-root user)
- **Config:** python-dotenv for environment-based secrets management

## Setup

\`\`\`bash
git clone https://github.com/Miki-Zn/Bastion.git
cd Bastion
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your own SECRET_KEY
python manage.py migrate
python manage.py runserver
\`\`\`

## Running with Docker

\`\`\`bash
docker build -t bastion:latest .
docker run --rm -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e DEBUG=False \
  -e ALLOWED_HOSTS=127.0.0.1,localhost \
  bastion:latest
\`\`\`

## Running Tests

\`\`\`bash
python manage.py test
\`\`\`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/token/ | Obtain JWT access/refresh token pair |
| POST | /api/token/refresh/ | Refresh access token (rotates + blacklists old one) |
| GET | /api/tasks/ | List authenticated user's own tasks |
| POST | /api/tasks/ | Create a new task |
| GET/PUT/DELETE | /api/tasks/{id}/ | Retrieve, update, or delete a task |

---

## Security Considerations

This project was built to practice identifying and fixing real API security
issues, not just implementing features. Below is a breakdown of what was
addressed and why.

### 1. JWT Authentication with Refresh Token Rotation

Access tokens are short-lived (15 minutes) to limit the exposure window if
a token is leaked. Refresh tokens rotate on every use and are blacklisted
after rotation — reusing an old refresh token is rejected with a `401` and
`"Token is blacklisted"`. This was manually verified by capturing a refresh
token, using it once, then attempting to reuse the same token.

### 2. Broken Object Level Authorization (OWASP API Security Top 10 #1)

The initial implementation used a static `queryset = Task.objects.all()`,
which meant any authenticated user could potentially access another user's
tasks. This was fixed by overriding `get_queryset()` to filter by the
authenticated user, and `perform_create()` to assign ownership server-side
instead of trusting client-supplied data. Covered by automated tests.

### 3. Input Validation

Custom serializer-level validation rejects empty and whitespace-only titles,
and restricts status values to a defined set. This required explicitly
setting `allow_blank=True` and `trim_whitespace=False` on the serializer
field so that custom validation logic — rather than DRF's default blank-field
rejection — produces the error message.

### 4. Rate Limiting on Login

The login endpoint is throttled to 5 requests per minute per IP address,
using a custom DRF throttle class scoped specifically to authentication
(not applied globally, so it doesn't affect authenticated endpoints).
Throttling is IP-based rather than username-based, since an attacker
attempting credential stuffing would rotate usernames, not IPs.

### 5. Security Audit Logging

Both successful and failed login attempts are logged with username and
client IP (extracted with `X-Forwarded-For` awareness for proxy/load
balancer environments). Logs are written to a local file excluded from
version control, since they contain data that shouldn't be public.

During implementation, failed login attempts initially weren't being logged
at all — `TokenObtainPairView` raises an exception on authentication
failure rather than returning a response, so logging logic placed after
`super().post()` never executed. Fixed with a try/except that logs on
exception and re-raises.

### 6. Secrets Management

`SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` are loaded from environment
variables via `python-dotenv`, never hardcoded. `.env` is gitignored;
`.env.example` documents required variables without exposing real values.

### 7. Static Application Security Testing (SAST)

Bandit runs on every push via GitHub Actions. One finding (hardcoded
password in test fixtures) was triaged and suppressed with an inline
`# nosec` comment and justification, rather than excluding the file
entirely — keeping future findings in that file visible.

### 8. Docker Hardening

- Multi-stage build: build tools and intermediate artifacts never reach
  the final image.
- Runs as a dedicated non-root user (`bastion`), limiting blast radius
  if the application were ever compromised.
- `.dockerignore` excludes `.env`, `.git`, and other files that shouldn't
  be in the build context.

## What I'd Do With More Time

- Add refresh token reuse detection with automatic session revocation
  (not just rejection of the reused token)
- Add per-user rate limiting on task creation, not just login
- Integrate dependency vulnerability scanning (e.g. `pip-audit`) into CI
- Add HTTPS enforcement and HSTS headers for production deployment
