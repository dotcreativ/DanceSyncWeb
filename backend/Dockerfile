FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the app directly using flask, not gunicorn
CMD ["flask", "run", "--host=0.0.0.0", "--port=10000"]