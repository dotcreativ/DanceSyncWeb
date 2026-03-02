import os
import subprocess
@app.route('/', methods=['GET'])
def health_check():
    return "DanceSync Backend is Running", 200
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        print("Processing started...") # This will show in Render logs
        
        # Save input file
        input_path = "input_video.mp4"
        output_path = "output_audio.mp3"
        file.save(input_path)
        
        # FFmpeg command to extract audio (faster method)
        command = [
            'ffmpeg', '-i', input_path, 
            '-vn', '-acodec', 'libmp3lame', 
            '-y', output_path
        ]
        
        try:
            # Run FFmpeg
            subprocess.run(command, check=True)
            print("FFmpeg finished successfully.") # Logs progress
            
            # Here we would normally add song recognition
            result = "Audio extracted! (Song recognition coming next)"
            
            # Clean up
            os.remove(input_path)
            # os.remove(output_path) # Keep this if you want to analyze it later
            
            return jsonify({'message': result})
            
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            return jsonify({'error': 'Failed to process video'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)