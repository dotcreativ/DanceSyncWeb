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
CORS(app)

# --- CONFIGURATION ---
ACR_CONFIG = {
    'access_key': 'd3c49529e1aff6b118376ea20df1f56e',
    'access_secret': 'zeTVsyKXimOE8jLAo0gCJc7D3v37s4PT9fdCFylC',
    'host': 'identify-us-west-2.acrcloud.com', # Check your ACR dashboard for your specific host
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_acr_signature(data_type, http_method, http_uri, access_key, access_secret, timestamp):
    string_to_sign = '\n'.join([http_method, http_uri, access_key, data_type, "1", timestamp])
    sign = base64.b64encode(hmac.new(access_secret.encode('ascii'), string_to_sign.encode('ascii'), hashlib.sha1).digest()).decode('ascii')
    return sign

def get_youtube_hq(query):
    """Automatically finds the best HQ audio stream for the matched song."""
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
            return {
                'url': video.get('url'),
                'thumb': video.get('thumbnail')
            }
        except:
            return None

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'status': 'error', 'message': 'No video'}), 400
    
    unique_id = str(uuid.uuid4())[:8]
    video_path = os.path.join(BASE_DIR, f"vid_{unique_id}.mp4")
    audio_path = os.path.join(BASE_DIR, f"aud_{unique_id}.mp3")
    
    try:
        file = request.files['video']
        file.save(video_path)

        # 1. Extract 15s of audio for ACRCloud Identification
        subprocess.run(['ffmpeg', '-i', video_path, '-ss', '0', '-t', '15', '-vn', '-ar', '8000', '-ac', '1', '-y', audio_path], check=True)

        # 2. ACRCloud Identify
        timestamp = str(int(time.time()))
        signature = get_acr_signature("audio", "POST", "/v1/identify", ACR_CONFIG['access_key'], ACR_CONFIG['access_secret'], timestamp)
        
        files = {'sample': open(audio_path, 'rb')}
        data = {
            'access_key': ACR_CONFIG['access_key'],
            'sample_bytes': os.path.getsize(audio_path),
            'timestamp': timestamp,
            'signature': signature,
            'data_type': 'audio',
            "signature_version": "1"
        }

        acr_res = requests.post(f"http://{ACR_CONFIG['host']}/v1/identify", files=files, data=data, timeout=20).json()

        if acr_res.get('status', {}).get('code') == 0:
            music = acr_res['metadata']['music'][0]
            title = music.get('title')
            artist = music['artists'][0]['name']
            # Convert offset ms to seconds (ACR is very precise)
            offset_sec = music.get('play_offset_ms', 0) / 1000.0

            # 3. Automatic YouTube Search for HQ Audio
            yt_data = get_youtube_hq(f"{title} {artist}")
            
            return jsonify({
                'status': 'success',
                'title': title,
                'artist': artist,
                'offset': str(offset_sec),
                'preview_url': yt_data['url'] if yt_data else "",
                'album_art': yt_data['thumb'] if yt_data else "",
                'video_file': f"vid_{unique_id}.mp4"
            })

        return jsonify({'status': 'error', 'message': 'ACRCloud could not identify song'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if os.path.exists(audio_path): os.remove(audio_path)

@app.route('/merge', methods=['POST'])
def merge_video():
    # ... (Keep your existing /merge route code here)
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))