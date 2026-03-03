import os
import subprocess
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://dotcreativ.github.io"}})

AUDD_API_TOKEN = "YOUR_ACTUAL_AUDD_KEY_HERE"

@app.route('/upload', methods=['POST'])
def upload_video():
    # ... (Keep your existing upload/clean/identify logic here)
    # Ensure your JSON response includes 'video_id' to track the file
    # For simplicity in this step, we'll use a static name or UUID
    pass 

@app.route('/merge', methods=['POST'])
def merge_video():
    data = request.json
    preview_url = data.get('preview_url')
    offset = data.get('offset', '00:00')
    
    # Files
    video_input = "input_video.mp4" # This needs to persist from the upload step
    audio_hq = "hq_audio.mp3"
    final_output = "synced_dance.mp4"

    try:
        # 1. Download HQ Audio
        audio_data = requests.get(preview_url).content
        with open(audio_hq, 'wb') as f:
            f.write(audio_data)

        # 2. FFmpeg Magic: Replace audio and sync
        # -itsoffset shifts the audio to match the dance
        command = [
            'ffmpeg', '-i', video_input, '-itsoffset', offset, '-i', audio_hq,
            '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
            '-shortest', '-y', final_output
        ]
        subprocess.run(command, check=True)

        return send_file(final_output, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500