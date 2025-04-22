FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a directory for GCS credentials
RUN mkdir -p /app/credentials

# Set environment variables
ENV PYTHONPATH=/app
ENV HUGGINGFACE_ENDPOINT_URL=${HUGGINGFACE_ENDPOINT_URL}
ENV HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}
ENV GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
ENV REDIS_HOST=${REDIS_HOST:-redis}
ENV REDIS_PORT=${REDIS_PORT:-6379}
ENV REDIS_PASSWORD=${REDIS_PASSWORD:-""}
ENV CACHE_TTL=${CACHE_TTL:-3600}

# Write GCS credentials to file if provided
RUN if [ -n "$GCS_CREDENTIALS" ]; then \
    echo "$GCS_CREDENTIALS" > /app/credentials/gcs_credentials.json; \
    fi

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 