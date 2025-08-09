# Name Card Reader App

A Python application that uses EasyOCR and Ollama to extract text from name card images and structure the information intelligently.

## Features

- 📷 Extract text from name card images using EasyOCR
- 🤖 Process extracted text with Ollama to structure information
- 🌐 Web interface for easy image uploads
- 📱 Command-line interface for batch processing
- 📊 JSON output with structured contact information

## Prerequisites

1. **Python 3.8+**
2. **Ollama installed and running** - [Install Ollama](https://ollama.ai/)
3. **At least one language model downloaded** (e.g., `llama3.2`)

### Install Ollama and Models

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai/

# Start Ollama service
ollama serve

# Download a model (in another terminal)
ollama pull llama3.2
```

## Installation

1. **Clone or download this repository**
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Interface (Recommended)

1. **Start the web application**:
   ```bash
   python web_app.py
   ```

2. **Open your browser** and go to `http://localhost:5000`

3. **Upload a name card image** and select your preferred Ollama model

4. **View the extracted and structured results**

### Command Line Interface

```bash
# Basic usage
python app.py path/to/namecard.jpg

# Specify a different model
python app.py path/to/namecard.jpg --model llama3

# Save results to file
python app.py path/to/namecard.jpg --output results.json

# Use different Ollama host
python app.py path/to/namecard.jpg --ollama-host http://remote-host:11434
```

### Example Output

```json
{
  "image_path": "namecard.jpg",
  "extracted_text": [
    {
      "text": "John Smith",
      "confidence": 0.95,
      "bbox": [[100, 50], [200, 50], [200, 80], [100, 80]]
    },
    {
      "text": "Senior Developer",
      "confidence": 0.92,
      "bbox": [[100, 90], [220, 90], [220, 110], [100, 110]]
    }
  ],
  "structured_data": {
    "name": "John Smith",
    "title": "Senior Developer",
    "company": "Tech Corp",
    "email": "john.smith@techcorp.com",
    "phone": "+1-555-0123",
    "address": "123 Main St, City, State 12345",
    "website": "www.techcorp.com"
  }
}
```

## Supported Image Formats

- PNG
- JPG/JPEG
- GIF
- BMP
- TIFF

## Configuration

### Environment Variables

- `OLLAMA_HOST`: Ollama server URL (default: `http://localhost:11434`)

### Adjusting OCR Confidence

Edit `app.py` and modify the confidence threshold:

```python
if confidence > 0.5:  # Change this value (0.0 to 1.0)
```

## Troubleshooting

### Common Issues

1. **"Failed to connect to Ollama"**
   - Ensure Ollama is running: `ollama serve`
   - Check if the model is available: `ollama list`
   - Verify the host URL is correct

2. **"No text could be extracted"**
   - Ensure image is clear and well-lit
   - Try different image formats
   - Check if text is in English (or modify language settings)

3. **EasyOCR installation issues**
   - On macOS with Apple Silicon: ensure you have the correct PyTorch version
   - May require additional system dependencies

### Performance Notes

- First run may be slower as EasyOCR downloads models
- Large images will take longer to process
- GPU acceleration will improve performance if available

## Advanced Usage

### Custom Prompt Engineering

Modify the prompt in `app.py` to customize how Ollama processes the extracted text:

```python
prompt = f"""
Your custom prompt here...
Text from business card: {text_content}
"""
```

### Batch Processing

```bash
# Process multiple images
for img in *.jpg; do
    python app.py "$img" --output "results_$(basename $img .jpg).json"
done
```

## License

MIT License - feel free to modify and use as needed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request