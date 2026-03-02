from flask import Flask, request, send_file, jsonify
import os
import werkzeug

app = Flask(__name__)

# Create a folder to store uploads temporarily
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return "DanceSync Backend is Running."

@app.route('/sync', methods=['POST'])
def sync_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    file = request.files['audio']
    filename = werkzeug.utils.secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    # ---------------------------------------------------------
    # PLACEHOLDER: This is where the magic will happen later
    # ---------------------------------------------------------
    print(f"Received file: {input_path}")
    
    # For now, we just send the same file back to test the connection
    output_path = input_path
    # ---------------------------------------------------------

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    # Render will use gunicorn, this is just for testing locally
    app.run(host='0.0.0.0', port=5000)