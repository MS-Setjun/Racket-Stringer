# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    APP_DATA_DIR=/app/data

WORKDIR /app

# Install dependencies first so they're cached separately from app code
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the repo (app.py, pages_/, and any optional assets
# like logo.png/favicon.png). .dockerignore keeps data files and local
# clutter out of the image.
COPY . .

# Data directory for stringing.db — mount this as a volume so data
# survives container rebuilds/upgrades.
RUN mkdir -p /app/data && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
VOLUME ["/app/data"]

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "app.py"]
