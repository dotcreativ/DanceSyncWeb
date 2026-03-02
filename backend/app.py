import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

# 1. Define 'app' first!
app = Flask(__name__)
CORS(app)

# 2. Then add your routes
@app.route('/', methods=['GET'])
def health_check():
    return "DanceSync Backend is Running", 200

@app.route('/upload', methods=['POST'])
def upload_video():
    # ... rest of your upload code ...