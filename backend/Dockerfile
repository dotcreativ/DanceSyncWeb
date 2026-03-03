FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render uses 10000 by default)
EXPOSE 10000

# Start Gunicorn and bind to the PORT environment variable
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120 app:app