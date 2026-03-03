import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Allow only your GitHub frontend to talk to this backend
CORS(app, resources={r"/*": {"origins": "https://dotcreativ.github.io"}})

@app.route('/', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    input_path = "input_video.mp4"
    output_path = "output_audio.mp3"
    
    try:
        file.save(input_path)
        print("File saved. Starting FFmpeg...")
        
        # Standard FFmpeg extraction
        subprocess.run([
            'ffmpeg', '-i', input_path, 
            '-vn', '-acodec', 'libmp3lame', 
            '-y', output_path
        ], check=True)
        
        return jsonify({'message': 'Audio extracted successfully!'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up files immediately
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)