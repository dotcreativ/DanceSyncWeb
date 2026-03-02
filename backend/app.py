import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route('/', methods=['GET'])
    def health_check():
        return "DanceSync Backend is Running", 200

    @app.route('/upload', methods=['POST'])
    def upload_video():
        if 'video' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            print("Processing started...") 
            input_path = "input_video.mp4"
            output_path = "output_audio.mp3"
            file.save(input_path)
            
            command = [
                'ffmpeg', '-i', input_path, 
                '-vn', '-acodec', 'libmp3lame', 
                '-y', output_path
            ]
            
            try:
                subprocess.run(command, check=True)
                print("FFmpeg finished successfully.")
                result = "Audio extracted! (Song recognition coming next)"
                
                if os.path.exists(input_path):
                    os.remove(input_path)
                
                return jsonify({'message': result})
                
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg error: {e}")
                return jsonify({'error': 'Failed to process video'}), 500
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)