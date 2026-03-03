FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the app with gunicorn so that production logs (and Render) match
# expectations and the PORT env var is respected by the config file.
CMD gunicorn -b 0.0.0.0:$PORT --timeout 600 app:app