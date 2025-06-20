FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles logs cache

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (Railway will set PORT dynamically)
EXPOSE 8000

# Command that Railway will run - fixed port binding
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn taskforge.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"] 