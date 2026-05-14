FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY docker/wsgi.py .

# Create non-root user for security and logs directory
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV OPENWEBUI_BASE_URL=http://openwebui:8080
ENV FLASK_DEBUG=false
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5001
ENV GUNICORN_WORKERS=4
ENV GUNICORN_TIMEOUT=300

EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${FLASK_PORT}/health')" || exit 1

# Run with Gunicorn for production
CMD ["sh", "-c", "gunicorn -w ${GUNICORN_WORKERS} -k gevent --timeout ${GUNICORN_TIMEOUT} --bind 0.0.0.0:${FLASK_PORT} wsgi:app"]
