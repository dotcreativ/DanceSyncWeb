FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Use Gunicorn as the primary process. 
# --timeout 0 disables worker timeouts entirely to stop the 'term' signal.
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 0 app:app