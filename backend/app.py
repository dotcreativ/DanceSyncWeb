import os
import subprocess
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://dotcreativ.github.io"}})

# --- PASTE YOUR KEY HERE ---
AUDD_API_TOKEN = "11449de62267e2b6295874c27e3f0eb7" 

@app.route('/', methods=['GET'])
def health_check():
    return "DanceSync Engine Active", 200

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video provided'}), 400
    
    file = request.files['video']
    input_path = "input_video.mp4"
    output_path = "output_audio.mp3"
    
    try:
        file.save(input_path)
        
        # 1. Extract Audio from Video
        subprocess.run([
            'ffmpeg', '-i', input_path, 
            '-vn', '-acodec', 'libmp3lame', 
            '-y', output_path
        ], check=True)
        
        # 2. Send to AudD for Recognition
        with open(output_path, 'rb') as f:
            data = {
                'api_token': AUDD_API_TOKEN,
                'return': 'apple_music,spotify',
            }
            files = {'file': f}
            response = requests.post('https://api.audd.io/', data=data, files=files)
            result = response.json()

        # 3. Handle Results
        if result.get('status') == 'success' and result.get('result'):
            song = result['result']
            return jsonify({
                'status': 'success',
                'title': song.get('title'),
                'artist': song.get('artist'),
                'offset': song.get('offset'), # e.g., "00:12"
                'album_art': song.get('spotify', {}).get('album', {}).get('images', [{}])[0].get('url') or \
                            song.get('apple_music', {}).get('artwork', {}).get('url', '').replace('{w}x{h}', '200x200')
            })
        else:
            return jsonify({'status': 'error', 'message': 'No match found in our database'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up files
        for path in [input_path, output_path]:
            if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))