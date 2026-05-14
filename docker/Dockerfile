FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY logs/ ./logs/
COPY docker/wsgi.py .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV OPENWEBUI_BASE_URL=http://openwebui:8080
ENV FLASK_DEBUG=false
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5001

EXPOSE 5001

# Run with Gunicorn for production
CMD ["gunicorn", "-w", "4", "-k", "gevent", "--timeout", "300", "--bind", "0.0.0.0:5001", "wsgi:app"]
