# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        wget \
        gnupg \
        lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-minimal.txt .

# Install essential Python dependencies first
RUN pip install --upgrade pip
RUN pip install --timeout=1000 --retries=5 --no-cache-dir -r requirements-minimal.txt

# Copy application code
COPY . .

# Install remaining dependencies (can be done at runtime if build fails)
COPY requirements.txt .
RUN pip install --timeout=1000 --retries=3 --no-cache-dir -r requirements.txt || echo "Full requirements installation failed, will install at runtime"

# Create necessary directories
RUN mkdir -p instance uploads vector_db

# Set permissions
RUN chmod -R 755 /app

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "run.py"]
