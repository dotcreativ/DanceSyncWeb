import os
import subprocess
import threading
import requests
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- KEEP-ALIVE MECHANISM ---
# Prevents Render from shutting down the service due to inactivity
def keep_alive():
    """Sends a request to the server every 5 minutes to keep it awake."""
    while True:
        try:
            # Replace with your actual Render service URL
            requests.get("https://dancesync-backend.onrender.com")
            print("Pinged server to keep alive.")
        except Exception as e:
            print(f"Keep-alive error: {e}")
        time.sleep(300) # Sleep for 5 minutes

# Start the keep-alive thread
threading.Thread(target=keep_alive, daemon=True).start()
# -----------------------------------

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
        
        # Save input file
        input_path = "input_video.mp4"
        output_path = "output_audio.mp3"
        file.save(input_path)
        
        # FFmpeg command to extract audio
        command = [
            'ffmpeg', '-i', input_path, 
            '-vn', '-acodec', 'libmp3lame', 
            '-y', output_path
        ]
        
        try:
            # Run FFmpeg
            subprocess.run(command, check=True)
            print("FFmpeg finished successfully.")
            
            result = "Audio extracted! (Song recognition coming next)"
            
            # Clean up files to save space on Render
            if os.path.exists(input_path):
                os.remove(input_path)
            
            return jsonify({'message': result})
            
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            return jsonify({'error': 'Failed to process video'}), 500

if __name__ == '__main__':
    # Use 0.0.0.0 and port 10000 for Docker
    app.run(host='0.0.0.0', port=10000)