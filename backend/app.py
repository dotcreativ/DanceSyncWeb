import os
import subprocess
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://dotcreativ.github.io"}})

AUDD_API_TOKEN = "YOUR_ACTUAL_AUDD_KEY_HERE"

def search_youtube(query):
    """Searches YouTube for a song and returns the best audio link."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1', # Take the first result
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            video = info['entries'][0]
            return {
                'title': video.get('title'),
                'preview_url': video.get('url'),
                'album_art': video.get('thumbnail'),
                'artist': video.get('uploader')
            }
        except Exception:
            return None

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video provided'}), 400
    
    file = request.files['video']
    input_path = "input_video.mp4"
    output_audio = "output_audio.mp3"
    
    try:
        file.save(input_path)
        
        # 1. Extract Audio
        subprocess.run(['ffmpeg', '-i', input_path, '-vn', '-acodec', 'libmp3lame', '-y', output_audio], check=True)
        
        # 2. Try AudD first (for exact Sync Offset)
        with open(output_audio, 'rb') as f:
            response = requests.post('https://api.audd.io/', data={'api_token': AUDD_API_TOKEN}, files={'file': f})
            result = response.json()

        if result.get('status') == 'success' and result.get('result'):
            song = result['result']
            return jsonify({
                'status': 'success',
                'source': 'audd',
                'title': song.get('title'),
                'artist': song.get('artist'),
                'offset': song.get('offset'),
                'preview_url': song.get('apple_music', {}).get('previews', [{}])[0].get('url') if 'apple_music' in song else None,
                'album_art': song.get('spotify', {}).get('album', {}).get('images', [{}])[0].get('url') if 'spotify' in song else None
            })
        
        # 3. FALLBACK: Search YouTube if AudD fails
        print("AudD failed. Searching YouTube...")
        # (For this to work well, we'd ideally use ACRCloud or similar for a query string, 
        # but for now, we'll return a 'Manual Search' status)
        return jsonify({
            'status': 'fallback',
            'message': 'Song not in database. Use YouTube search?'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for p in [input_path, output_audio]:
            if os.path.exists(p): os.remove(p)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))