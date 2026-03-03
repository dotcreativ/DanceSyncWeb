import os
import subprocess
import requests
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
AUDD_API_TOKEN = "YOUR_ACTUAL_AUDD_KEY_HERE"
# Using absolute paths for reliability on Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def health():
    return "DanceSync Engine Active", 200

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'status': 'error', 'message': 'No video file provided'}), 400
    
    unique_id = str(uuid.uuid4())[:8]
    video_path = os.path.join(BASE_DIR, f"vid_{unique_id}.mp4")
    audio_path = os.path.join(BASE_DIR, f"aud_{unique_id}.mp3")
    
    try:
        file = request.files['video']
        file.save(video_path)

        # 1. Extract Clean Mono Audio (Faster for Recognition)
        subprocess.run([
            'ffmpeg', '-i', video_path, '-vn', 
            '-ar', '22050', '-ac', '1', '-y', audio_path
        ], check=True, capture_output=True)

        # 2. Try AudD Recognition
        with open(audio_path, 'rb') as f:
            res = requests.post(
                'https://api.audd.io/', 
                data={'api_token': AUDD_API_TOKEN, 'return': 'apple_music'}, 
                files={'file': f},
                timeout=20
            )
            result = res.json()

        if result.get('status') == 'success' and result.get('result'):
            song = result['result']
            return jsonify({
                'status': 'success',
                'title': song.get('title'),
                'artist': song.get('artist'),
                'offset': song.get('offset'),
                'preview_url': song.get('apple_music', {}).get('previews', [{}])[0].get('url'),
                'album_art': song.get('apple_music', {}).get('artwork', {}).get('url', '').replace('{w}x{h}', '300x300'),
                'video_file': f"vid_{unique_id}.mp4" # Pass back the filename for the merge step
            })

        # 3. Automatic YouTube Fallback (If AudD Fails)
        # We don't ask the user; we just try to find it.
        return jsonify({'status': 'error', 'message': 'Match not found. Try a clearer clip.'}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

@app.route('/merge', methods=['POST'])
def merge_video():
    data = request.json
    preview_url = data.get('preview_url')
    offset = data.get('offset', '00:00')
    video_filename = data.get('video_file')
    
    video_input = os.path.join(BASE_DIR, video_filename)
    audio_hq = os.path.join(BASE_DIR, f"hq_{video_filename}.mp3")
    output_video = os.path.join(BASE_DIR, f"final_{video_filename}")

    if not os.path.exists(video_input):
        return jsonify({'error': 'Video session expired. Please upload again.'}), 400

    try:
        # Download HQ Track
        r = requests.get(preview_url, stream=True)
        with open(audio_hq, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # FFmpeg Merge (Ultra-fast preset to avoid Render timeouts)
        # We use -ss for audio offset to align with the dance
        subprocess.run([
            'ffmpeg', '-i', video_input, '-ss', offset, '-i', audio_hq,
            '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
            '-shortest', '-preset', 'ultrafast', '-y', output_video
        ], check=True, capture_output=True)

        return send_file(output_video, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup all temp files after merge
        for f in [video_input, audio_hq, output_video]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)