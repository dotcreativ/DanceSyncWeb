import os
import subprocess
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://dotcreativ.github.io"}})

AUDD_API_TOKEN = "YOUR_ACTUAL_AUDD_KEY_HERE"

@app.route('/', methods=['GET'])
def health(): return "Ready", 200

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video'}), 400
    
    file = request.files['video']
    # Use absolute paths to avoid confusion
    video_path = os.path.join(os.getcwd(), "input_video.mp4")
    raw_audio = os.path.join(os.getcwd(), "raw_audio.mp3")
    
    try:
        file.save(video_path)
        
        # 1. Faster extraction for recognition
        subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-ar', '22050', '-ac', '1', '-y', raw_audio], check=True)
        
        # 2. Identify (Using raw_audio directly to save RAM)
        with open(raw_audio, 'rb') as f:
            res = requests.post('https://api.audd.io/', data={'api_token': AUDD_API_TOKEN, 'return': 'apple_music'}, files={'file': f})
            result = res.json()

        if result.get('status') == 'success' and result.get('result'):
            song = result['result']
            return jsonify({
                'status': 'success',
                'title': song.get('title'),
                'artist': song.get('artist'),
                'offset': song.get('offset'),
                'preview_url': song.get('apple_music', {}).get('previews', [{}])[0].get('url'),
                'album_art': song.get('apple_music', {}).get('artwork', {}).get('url', '').replace('{w}x{h}', '200x200')
            })
        return jsonify({'status': 'error', 'message': 'No match'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(raw_audio): os.remove(raw_audio)

@app.route('/merge', methods=['POST'])
def merge_video():
    data = request.json
    preview_url = data.get('preview_url')
    offset = data.get('offset', '00:00')
    
    video_input = os.path.join(os.getcwd(), "input_video.mp4")
    audio_hq = os.path.join(os.getcwd(), "hq_audio.mp3")
    final_output = os.path.join(os.getcwd(), "synced_dance.mp4")

    try:
        # 1. Stream download to save memory
        r = requests.get(preview_url, stream=True)
        with open(audio_hq, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Ultra-fast Merge: copy video codec, only re-encode audio
        # We use -preset ultrafast to finish before Render times out
        command = [
            'ffmpeg', '-i', video_input, '-ss', offset, '-i', audio_hq,
            '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
            '-shortest', '-preset', 'ultrafast', '-y', final_output
        ]
        subprocess.run(command, check=True)

        return send_file(final_output, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500