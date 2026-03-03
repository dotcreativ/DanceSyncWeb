FROM python:3.11-slim

# Install FFmpeg
# ... (rest of dockerfile)
# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# EXPOSE the port Render uses
EXPOSE 10000

# --- THE RELENTLESS RESTART LOOP ---
CMD while true; do gunicorn -b 0.0.0.0:$PORT --timeout 600 app:app; sleep 1; done