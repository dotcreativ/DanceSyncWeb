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

app = Flask(__name__)
CORS(app)

# --- ACRCLOUD CONFIG ---
ACR_CONFIG = {
    'access_key': 'd3c49529e1aff6b118376ea20df1f56e',
    'access_secret': 'zeTVsyKXimOE8jLAo0gCJc7D3v37s4PT9fdCFylC',
    'host': 'identify-us-west-2.acrcloud.com',
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_acr_signature(data_type, http_method, http_uri, access_key, access_secret, timestamp):
    string_to_sign = '\n'.join([http_method, http_uri, access_key, data_type, "1", timestamp])
    sign = base64.b64encode(hmac.new(access_secret.encode('ascii'), string_to_sign.encode('ascii'), hashlib.sha1).digest()).decode('ascii')
    return sign

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video'}), 400
    
    unique_id = str(uuid.uuid4())[:8]
    temp_video = os.path.join(BASE_DIR, f"temp_{unique_id}.mp4")
    audio_snippet = os.path.join(BASE_DIR, f"snippet_{unique_id}.mp3")
    
    try:
        # Save file to disk (not memory)
        request.files['video'].save(temp_video)
        
        # 1. Extract a tiny 15s snippet (Low bitrate to save RAM)
        subprocess.run([
            'ffmpeg', '-i', temp_video, '-vn', '-ar', '8000', '-ac', '1', '-t', '15', '-y', audio_snippet
        ], check=True)

        # CRITICAL: Delete the heavy video IMMEDIATELY to free up RAM
        if os.path.exists(temp_video):
            os.remove(temp_video)

        # 2. ACRCloud Identification
        timestamp = str(int(time.time()))
        signature = get_acr_signature("audio", "POST", "/v1/identify", ACR_CONFIG['access_key'], ACR_CONFIG['access_secret'], timestamp)
        
        with open(audio_snippet, 'rb') as f:
            files = {'sample': f}
            data = {
                'access_key': ACR_CONFIG['access_key'],
                'sample_bytes': os.path.getsize(audio_snippet),
                'timestamp': timestamp,
                'signature': signature,
                'data_type': 'audio',
                "signature_version": "1"
            }
            res = requests.post(f"http://{ACR_CONFIG['host']}/v1/identify", files=files, data=data, timeout=15)
            acr_res = res.json()

        if acr_res.get('status', {}).get('code') == 0:
            music = acr_res['metadata']['music'][0]
            # Success logic...
            return jsonify({
                'status': 'success',
                'title': music.get('title'),
                'artist': music['artists'][0]['name'],
                'offset': music.get('play_offset_ms', 0) / 1000.0
            })
        
        return jsonify({'status': 'error', 'message': 'No match found'}), 404

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({'error': 'Process timed out or out of memory'}), 500
    finally:
        # Final cleanup
        if os.path.exists(temp_video): os.remove(temp_video)
        if os.path.exists(audio_snippet): os.remove(audio_snippet)