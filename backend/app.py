import os
import subprocess
import threading
import requests
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- OPTIONAL KEEP-ALIVE MECHANISM ---
# (Render already pings your service; this thread is mainly useful
#  during local development or on platforms without their own health
#  checker.  It will only be started when running the script directly.)
def keep_alive():
    """Sends a request to the server every 5 minutes to keep it awake."""
    while True:
        try:
            # Replace with your actual deployed URL if different
            requests.get("https://dancesync-backend.onrender.com")
            print("Pinged server to keep alive.")
        except Exception as e:
            print(f"Keep-alive error: {e}")
        time.sleep(300)  # Sleep for 5 minutes

@app.route('/', methods=['GET'])
def health_check():
    # return JSON makes it easier for automated health checks to parse
    return jsonify(status="ok", service="DanceSync Backend"), 200

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        print("Processing started...")

        # Save input file
        input_path = "input_video.mp4"
        output_path = "output_audio.mp3"
        file.save(input_path)

        # FFmpeg command to extract audio
        command = [
            'ffmpeg', '-i', input_path,
            '-vn', '-acodec', 'libmp3lame',
            '-y', output_path
        ]

        try:
            # Run FFmpeg
            subprocess.run(command, check=True)
            print("FFmpeg finished successfully.")

            result = "Audio extracted! (Song recognition coming next)"

            # Clean up files to save space on Render
            if os.path.exists(input_path):
                os.remove(input_path)

            return jsonify({'message': result})

        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            return jsonify({'error': 'Failed to process video'}), 500


@app.route('/sync', methods=['POST'])
def sync_file():
    """Accepts either an audio or video file and returns a simple acknowledgement.
    The frontend currently sends an `audio` field containing an MP3 blob; the
    legacy `/upload` endpoint expected a `video` file and performed server-side
    audio extraction with ffmpeg.  To keep the API flexible both are supported.
    """
    # determine which field is present
    file_field = None
    if 'audio' in request.files:
        file_field = 'audio'
    elif 'video' in request.files:
        file_field = 'video'

    if not file_field:
        return jsonify({'error': 'No file provided (expected "audio" or "video" field)'}), 400

    uploaded = request.files[file_field]
    if uploaded.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    print(f"Received {file_field} file '{uploaded.filename}'")

    save_path = f"received_{file_field}_{uploaded.filename}"
    uploaded.save(save_path)

    response = {'message': 'File received', 'filename': save_path}
    try:
        os.remove(save_path)
    except Exception:
        pass
    return jsonify(response)


if __name__ == '__main__':
    # when run directly start the optional keep-alive thread
    threading.Thread(target=keep_alive, daemon=True).start()

    # pick up PORT env var or fall back to 10000
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
