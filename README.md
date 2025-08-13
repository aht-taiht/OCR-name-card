# OCR Name Card Reader

A sophisticated OCR (Optical Character Recognition) system designed to extract and structure information from business cards using PaddleOCR and HuggingFace models, with Google Drive integration for batch processing.

## Features

- **Multi-language OCR**: Supports Japanese, English, and Vietnamese text recognition using PaddleOCR
- **Google Drive Integration**: Process images directly from Google Drive folders
- **Advanced Text Processing**: Uses HuggingFace models to structure extracted text into JSON format
- **Web Interface**: Modern web UI with drag-and-drop upload and Google Drive folder selection
- **Batch Processing**: Process multiple images from local folders or Google Drive
- **High Accuracy**: Combines multiple OCR approaches and language models for optimal results
- **Structured Output**: Automatically organizes extracted information into categories

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Google Drive API credentials (for Google Drive features)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd OCR-name-card
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. For Google Drive integration, set up Google Drive API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Drive API
   - Create OAuth 2.0 credentials
   - Download credentials as `credentials.json` and place in project directory

## Usage

### Command Line Interface

#### Process a single image:
```bash
python app.py path/to/namecard.jpg
```

#### Process local folder:
```bash
python app.py /path/to/images --folder --output batch_results.json
```

#### Process Google Drive folder:
```bash
python app.py "NameCards" --google-drive --output drive_results.json
```

#### Process Google Drive folder by ID:
```bash
python app.py "1XxXxXxXxXxXxXxXxXxXxX" --google-drive
```

#### Custom credentials file:
```bash
python app.py "NameCards" --google-drive --credentials my_credentials.json
```

### Web Interface

1. Start the web server:
```bash
python web_app.py
```

2. Open your browser and navigate to:
```
http://localhost:6001
```

3. Choose processing mode:
   - **📷 Single Image**: Upload single image via drag-and-drop
   - **☁️ Google Drive Folder**: Process entire Google Drive folder

#### Google Drive Web Usage:
1. Click "☁️ Google Drive Folder" tab
2. Click "🔐 Check Google Drive Connection" to authenticate
3. Select folder from dropdown list
4. Click "☁️ Process Google Drive Folder"
5. View batch results with expandable individual results

## Configuration

### Google Drive Setup

1. **Create Google Cloud Project**:
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing

2. **Enable Google Drive API**:
   - Go to "APIs & Services" → "Library"
   - Search and enable "Google Drive API"

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download JSON file as `credentials.json`

4. **Place credentials file** in project root directory

### HuggingFace Configuration

```bash
python app.py image.jpg --hf-token your_token_here --model openai/gpt-oss-20b
```

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tif, .tiff)
- GIF (.gif)

## Output Format

The system extracts and structures the following information:

```json
{
  "name": "Full name of the person",
  "title": "Job title/position", 
  "company": "Company name",
  "email": "Email address",
  "phone": "Phone number",
  "address": "Physical address",
  "website": "Website URL",
  "university": "Educational institution",
  "department": "Department/division",
  "language": "Detected language",
  "social_media": "Social media links",
  "notes": "Additional notes",
  "other": "Other relevant information"
}
```

### Batch Processing Output

```json
{
  "source": "google_drive",
  "folder_name": "NameCards",
  "total_images": 25,
  "processed_images": 25,
  "summary": {
    "successful": 23,
    "failed": 2
  },
  "results": [
    {
      "filename": "card1.jpg",
      "drive_file_id": "1ABC...",
      "structured_data": { "name": "...", "title": "..." }
    }
  ]
}
```

## Technical Architecture

### OCR Processing Pipeline

1. **Multi-language Recognition**: 
   - English OCR using PaddleOCR
   - Japanese OCR using PaddleOCR
   - Vietnamese OCR using PaddleOCR

2. **Result Combination**: Merges and deduplicates results from all languages

3. **Text Structuring**: Uses HuggingFace models to organize text into structured JSON

4. **Google Drive Integration**: Downloads images to temporary files, processes, then cleans up

### Models and Libraries

- **OCR Engine**: PaddleOCR (supports 80+ languages)
- **Text Processing**: HuggingFace Transformers
- **Image Processing**: OpenCV for preprocessing
- **Google Drive**: Google Drive API v3
- **Web Framework**: Flask

## API Endpoints

### Web Application Endpoints

- `GET /` - Main web interface
- `POST /upload` - Single image upload processing
- `GET /google-drive/auth-status` - Check Google Drive authentication
- `GET /google-drive/folders` - List Google Drive folders
- `POST /google-drive/process` - Process Google Drive folder

## Performance and Optimization

### Language Processing Strategy

The system processes images with all three language models (English, Japanese, Vietnamese) and combines results for maximum accuracy:

```python
# Processes with multiple languages
results_en = ocr_en.ocr(image_path)
results_jp = ocr_japan.ocr(image_path) 
results_vi = ocr_vi.ocr(image_path)

# Combines and deduplicates
combined_results = combine_all_language_results([
    ('en', results_en),
    ('japan', results_jp), 
    ('vi', results_vi)
])
```

### Google Drive Optimization

- **Temporary Files**: Downloads to temp files, auto-cleanup after processing
- **Batch Processing**: Processes multiple images sequentially
- **Error Handling**: Continues processing other images if individual files fail
- **Progress Tracking**: Real-time progress updates in web interface

## Troubleshooting

### Google Drive Issues

1. **Authentication Failed**:
   ```bash
   # Check credentials file exists
   ls -la credentials.json
   
   # Re-download from Google Cloud Console if needed
   ```

2. **Folder Not Found**:
   - Verify folder exists in Google Drive
   - Check folder permissions (must be accessible by your account)
   - Try using folder ID instead of name

3. **API Quota Exceeded**:
   - Check Google Cloud Console quotas
   - Enable billing if needed for higher quotas

### OCR Issues

1. **PaddleOCR Installation**:
   ```bash
   pip install paddlepaddle paddleocr
   ```

2. **Memory Issues**:
   - Process images in smaller batches
   - Use CPU-only mode if GPU memory is limited

3. **Language Detection**:
   - Ensure image quality is good
   - Try preprocessing images for better contrast

### Web Interface Issues

1. **Port Already in Use**:
   ```bash
   python web_app.py --port 6002
   ```

2. **Large File Uploads**:
   - Check Flask MAX_CONTENT_LENGTH setting
   - Current limit: 16MB per file

## Development

### Project Structure

```
OCR-name-card/
├── app.py                 # Command line interface
├── web_app.py            # Web interface
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html       # Web UI template
├── uploads/             # Temporary upload directory
├── credentials.json     # Google Drive credentials
├── token.json          # Google Drive auth token
└── README.md           # This file
```

### Adding New Features

1. **New Language Support**: Add language code to PaddleOCR initialization
2. **New Cloud Providers**: Extend GoogleDriveHandler pattern
3. **New OCR Engines**: Implement similar to PaddleOCR integration
4. **Enhanced UI**: Modify templates/index.html and add CSS/JS

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Test your changes with both CLI and web interface
4. Update documentation if needed
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **PaddleOCR** team for the excellent multi-language OCR capabilities
- **HuggingFace** for transformer models and APIs
- **Google** for Drive API integration
- **Flask** community for the web framework
- **OpenCV** community for image processing tools