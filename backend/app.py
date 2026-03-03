import os
import subprocess
import requests
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://dotcreativ.github.io"}})

AUDD_API_TOKEN = "YOUR_ACTUAL_AUDD_KEY_HERE"

# Helper to ensure unique filenames if multiple people use the app
def get_temp_path(ext):
    return f"{uuid.uuid4()}.{ext}"

def clean_audio(input_file, output_file):
    filter_chain = "highpass=f=200,lowpass=f=3000,afftdn,loudnorm"
    subprocess.run(['ffmpeg', '-i', input_file, '-af', filter_chain, '-y', output_file], check=True)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video'}), 400
    
    file = request.files['video']
    video_path = "input_video.mp4" # We'll keep this simple for now
    raw_audio = "raw_audio.mp3"
    clean_audio_path = "clean_audio.mp3"
    
    try:
        file.save(video_path)
        # 1. Extract & Clean
        subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-acodec', 'libmp3lame', '-y', raw_audio], check=True)
        clean_audio(raw_audio, clean_audio_path)
        
        # 2. Identify
        with open(clean_audio_path, 'rb') as f:
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
        return jsonify({'status': 'error', 'message': 'Song not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # We keep the video_path for the merge step, but clean up audio
        if os.path.exists(raw_audio): os.remove(raw_audio)
        if os.path.exists(clean_audio_path): os.remove(clean_audio_path)

@app.route('/merge', methods=['POST'])
def merge_video():
    data = request.json
    preview_url = data.get('preview_url')
    # Convert MM:SS to seconds for FFmpeg -ss (seek)
    offset = data.get('offset', '00:00')
    
    video_input = "input_video.mp4"
    audio_hq = "hq_audio.mp3"
    final_output = "synced_dance.mp4"

    try:
        # Download HQ Audio
        audio_content = requests.get(preview_url).content
        with open(audio_hq, 'wb') as f:
            f.write(audio_content)

        # FFmpeg: Mute original, add HQ audio starting at offset, sync to video
        # -ss seeks in the audio to the match point
        command = [
            'ffmpeg', '-i', video_input, '-ss', offset, '-i', audio_hq,
            '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
            '-shortest', '-y', final_output
        ]
        subprocess.run(command, check=True)

        return send_file(final_output, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))