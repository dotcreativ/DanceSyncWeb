import os
import subprocess
import requests
import uuid
import time
import hashlib
import hmac
import base64
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- ACRCLOUD CONFIG ---
ACR_CONFIG = {
    'access_key': 'YOUR_ACR_ACCESS_KEY',
    'access_secret': 'YOUR_ACR_ACCESS_SECRET',
    'host': 'identify-eu-west-1.acrcloud.com', 
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_acr_signature(data_type, http_method, http_uri, access_key, access_secret, timestamp):
    string_to_sign = '\n'.join([http_method, http_uri, access_key, data_type, "1", timestamp])
    sign = base64.b64encode(hmac.new(access_secret.encode('ascii'), string_to_sign.encode('ascii'), hashlib.sha1).digest()).decode('ascii')
    return sign

def get_youtube_hq(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"{query} official audio", download=False)
            video = info['entries'][0]
            return {'url': video.get('url'), 'thumb': video.get('thumbnail')}
        except: return None

@app.route('/')
def health():
    return "Server is Live", 200

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video'}), 400
    
    unique_id = str(uuid.uuid4())[:8]
    video_path = os.path.join(BASE_DIR, f"vid_{unique_id}.mp4")
    audio_path = os.path.join(BASE_DIR, f"aud_{unique_id}.mp3")
    
    try:
        file = request.files['video']
        file.save(video_path)
        
        # 1. Extraction for ACRCloud
        subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-ar', '8000', '-ac', '1', '-t', '15', '-y', audio_path], check=True)
        
        # 2. ACRCloud Identify
        timestamp = str(int(time.time()))
        signature = get_acr_signature("audio", "POST", "/v1/identify", ACR_CONFIG['access_key'], ACR_CONFIG['access_secret'], timestamp)
        
        with open(audio_path, 'rb') as f:
            files = {'sample': f}
            data = {
                'access_key': ACR_CONFIG['access_key'],
                'sample_bytes': os.path.getsize(audio_path),
                'timestamp': timestamp,
                'signature': signature,
                'data_type': 'audio',
                "signature_version": "1"
            }
            res = requests.post(f"http://{ACR_CONFIG['host']}/v1/identify", files=files, data=data, timeout=20)
            acr_res = res.json()

        if acr_res.get('status', {}).get('code') == 0:
            music = acr_res['metadata']['music'][0]
            title, artist = music.get('title'), music['artists'][0]['name']
            offset_sec = music.get('play_offset_ms', 0) / 1000.0
            yt_data = get_youtube_hq(f"{title} {artist}")

            return jsonify({
                'status': 'success',
                'title': title, 'artist': artist, 'offset': str(offset_sec),
                'preview_url': yt_data['url'] if yt_data else "",
                'album_art': yt_data['thumb'] if yt_data else "",
                'video_file': f"vid_{unique_id}.mp4"
            })
        
        return jsonify({'status': 'error', 'message': 'Song not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(audio_path): os.remove(audio_path)

@app.route('/merge', methods=['POST'])
def merge_video():
    data = request.json
    preview_url, offset, video_file = data.get('preview_url'), data.get('offset', '0'), data.get('video_file')
    
    video_input = os.path.join(BASE_DIR, video_file)
    audio_hq = os.path.join(BASE_DIR, f"hq_{video_file}.mp3")
    final_output = os.path.join(BASE_DIR, f"synced_{video_file}")

    try:
        r = requests.get(preview_url, stream=True)
        with open(audio_hq, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

        command = [
            'ffmpeg', '-i', video_input, '-ss', offset, '-i', audio_hq,
            '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
            '-shortest', '-preset', 'ultrafast', '-y', final_output
        ]
        subprocess.run(command, check=True)
        return send_file(final_output, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)