# ─────────────────────────────────────────────────────────────────────
# MindFlow / Rovot Backend — Production Docker Image
# Multi-stage build for a lean, secure container.
# ─────────────────────────────────────────────────────────────────────

# Stage 1: Builder — install Python dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime — minimal image
FROM python:3.11-slim AS runtime

# Security: run as non-root user
RUN groupadd -r rovot && useradd -r -g rovot -d /app -s /sbin/nologin rovot

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY . .

# Remove unnecessary files
RUN rm -rf tests/ .env* __pycache__ *.pyc .git

# Set ownership
RUN chown -R rovot:rovot /app

# Switch to non-root user
USER rovot

# Environment defaults
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Expose port
EXPOSE ${PORT}

# Start with gunicorn for production
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "src.main:app"]
