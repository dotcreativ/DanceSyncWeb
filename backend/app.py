import os
import subprocess
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Replace with your actual GitHub URL
CORS(app, resources={r"/*": {"origins": "https://dotcreativ.github.io"}})

# --- PASTE YOUR AUDD KEY HERE ---
AUDD_API_TOKEN = "YOUR_ACTUAL_AUDD_KEY_HERE" 

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
        print("File saved. Extracting audio...")
        
        # 1. Extract Audio
        subprocess.run(['ffmpeg', '-i', input_path, '-vn', '-acodec', 'libmp3lame', '-y', output_path], check=True)
        
        # 2. Identify Song via AudD
        print("Identifying song via AudD...")
        with open(output_path, 'rb') as f:
            data = {'api_token': AUDD_API_TOKEN, 'return': 'apple_music,spotify'}
            files = {'file': f}
            response = requests.post('https://api.audd.io/', data=data, files=files)
            result = response.json()

        if result.get('status') == 'success' and result.get('result'):
            song = result['result']
            # Get the Apple Music preview URL for the HQ audio
            preview = song.get('apple_music', {}).get('previews', [{}])[0].get('url')
            
            return jsonify({
                'status': 'success',
                'title': song.get('title'),
                'artist': song.get('artist'),
                'offset': song.get('offset'), # e.g. "00:12"
                'preview_url': preview,
                'album_art': song.get('spotify', {}).get('album', {}).get('images', [{}])[0].get('url')
            })
        else:
            return jsonify({'status': 'error', 'message': 'Song not recognized'}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)