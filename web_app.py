#!/usr/bin/env python3
"""
Web interface for Name Card Reader App
Provides a simple web UI for uploading and processing name card images.
"""

from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import json
from werkzeug.utils import secure_filename
from pathlib import Path
from app import NameCardReader, GoogleDriveHandler
import tempfile
import traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize name card reader
reader = NameCardReader()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main page with upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process name card."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Get model from form
        model = request.form.get('model', 'llama3.2')
        
        # Process the uploaded image
        result = reader.process_name_card(file_path)
        return jsonify(result)
    else:
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/google-drive/folders')
def list_google_drive_folders():
    """List available Google Drive folders."""
    try:
        credentials_file = request.args.get('credentials', 'credentials.json')
        drive_handler = GoogleDriveHandler(credentials_file)
        drive_handler.authenticate()
        
        # Get folders from root directory
        query = "mimeType='application/vnd.google-apps.folder' and parents in 'root'"
        results = drive_handler.service.files().list(
            q=query,
            fields="files(id, name, modifiedTime)",
            orderBy="name"
        ).execute()
        
        folders = results.get('files', [])
        return jsonify({'folders': folders})
        
    except Exception as e:
        return jsonify({'error': f'Failed to list folders: {str(e)}'}), 500


@app.route('/google-drive/process', methods=['POST'])
def process_google_drive_folder():
    """Process all images in a Google Drive folder."""
    try:
        data = request.get_json()
        folder_id = data.get('folder_id')
        folder_name = data.get('folder_name', folder_id)
        credentials_file = data.get('credentials', 'credentials.json')
        
        if not folder_id:
            return jsonify({'error': 'Folder ID is required'}), 400
        
        # Process the Google Drive folder
        result = reader.process_google_drive_folder(
            folder_id, 
            output_file=None, 
            credentials_file=credentials_file
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/google-drive/auth-status')
def google_drive_auth_status():
    """Check Google Drive authentication status."""
    try:
        credentials_file = request.args.get('credentials', 'credentials.json')
        
        # Check if credentials file exists
        if not os.path.exists(credentials_file):
            return jsonify({
                'authenticated': False,
                'error': f'Credentials file not found: {credentials_file}',
                'setup_required': True
            })
        
        # Try to authenticate
        drive_handler = GoogleDriveHandler(credentials_file)
        drive_handler.authenticate()
        
        return jsonify({
            'authenticated': True,
            'message': 'Google Drive API authenticated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': str(e),
            'setup_required': 'credentials' in str(e).lower()
        })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6001)