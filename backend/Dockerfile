# syntax=docker/dockerfile:1.7

# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Build deps for psycopg (binary wheel usually avoids this, but keep safe)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install production dependencies into a venv we can copy
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade build tooling to close known CVEs in setuptools/pip.
# This must run before installing requirements so the constraints
# can resolve against the patched versions.
RUN python -m pip install --upgrade "pip>=26.0" "setuptools>=78.1.1" "wheel>=0.45"

COPY requirements.txt constraints.txt ./
# NOTE: `msgpack 1.1.2` may appear in vulnerability scans. It is NOT
# a dependency of the application; it is vendored inside `pip` itself
# (see `pip/_vendor/bom.cdx.json`). Verified with:
#   docker compose exec api python -c "import msgpack"  # ModuleNotFoundError
# Tracked as a known false positive until pip ships a newer vendored copy.
RUN pip install -r requirements.txt -c constraints.txt \
    && pip install --upgrade "msgpack>=1.2.3" "urllib3>=2.8.0" "setuptools>=78.1.1"

# Download spaCy model (needed by sanitizer_service)
RUN python -m spacy download es_core_news_md


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Runtime deps: libpq for psycopg, curl for healthcheck, tini for signal handling
# Also apply the latest Debian security patches available in the base image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from builder (contains patched setuptools/msgpack/urllib3)
COPY --from=builder /opt/venv /opt/venv

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini ./alembic.ini

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]