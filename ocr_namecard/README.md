# OCR Name Card Reader - Odoo Module

Odoo 18 module for extracting and processing contact information from name card images using OCR and AI.

## Features

- 📷 Upload name card images via Odoo interface
- 🤖 Extract text using Tesseract OCR
- 🧠 Process with HuggingFace AI models to structure data
- 📊 Store and manage contact information
- 👥 Create Odoo contacts from name cards
- 📤 Export to JSON/vCard formats
- 🔄 Bulk upload support
- 📋 Kanban/Tree/Form views

## Installation

1. **Install system dependencies**:

   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install tesseract-ocr libtesseract-dev
   sudo apt install tesseract-ocr-jpn  # Optional: for Japanese support
   ```

   **macOS:**
   ```bash
   brew install tesseract
   ```

   **Windows:**
   - Download from [Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add to PATH or configure in Odoo settings

2. **Install Python dependencies**:
   ```bash
   pip install pytesseract huggingface_hub pillow numpy opencv-python-headless
   ```

3. **Copy module to Odoo addons directory**:
   ```bash
   cp -r ocr_namecard /path/to/odoo/addons/
   ```

4. **Update apps list** in Odoo and **Install** the module

5. **Configure HuggingFace settings** (optional):
   - Go to Settings → OCR Settings
   - Set HuggingFace API token for private models
   - Configure default model

## Usage

### Web Interface

1. **Go to Name Card OCR → Name Cards**
2. **Click Create** to upload a new name card
3. **Upload image** and wait for processing
4. **Review extracted information**
5. **Click "Create Contact"** to add to Odoo contacts

### API Endpoints

#### Upload Single Image
```bash
curl -X POST -F "image=@namecard.jpg" \
  -H "Authorization: Bearer your_session_token" \
  http://your-odoo-url/namecard/upload
```

#### Bulk Upload
```bash
curl -X POST -F "images=@card1.jpg" -F "images=@card2.jpg" \
  -H "Authorization: Bearer your_session_token" \
  http://your-odoo-url/namecard/bulk_upload
```

#### Export Data
```bash
# JSON format
curl "http://your-odoo-url/namecard/export/123?format=json"

# vCard format  
curl "http://your-odoo-url/namecard/export/123?format=vcard"
```

## Configuration

### System Parameters

Set these in Settings → Technical → System Parameters:

- `ocr_namecard.hf_token`: HuggingFace API token
- `ocr_namecard.hf_model`: Default AI model (default: microsoft/DialoGPT-medium)

### Recommended Models

- `microsoft/DialoGPT-medium` (default, good balance)
- `microsoft/DialoGPT-large` (better accuracy, slower)
- `facebook/blenderbot-400M-distill` (alternative)
- `gpt2` (simple text generation)

## Model Structure

### ocr.namecard

| Field | Type | Description |
|-------|------|-------------|
| `image` | Binary | Name card image |
| `contact_name` | Char | Extracted full name |
| `job_title` | Char | Job title/position |
| `company_name` | Char | Company name |
| `email` | Char | Email address |
| `phone` | Char | Phone number |
| `mobile` | Char | Mobile number |
| `website` | Char | Website URL |
| `address` | Text | Physical address |
| `processing_status` | Selection | draft/processing/done/error |
| `partner_id` | Many2one | Linked Odoo contact |

## API Response Format

```json
{
  "success": true,
  "namecard_id": 123,
  "status": "done",
  "contact_name": "John Smith",
  "company_name": "Tech Corp",
  "email": "john@techcorp.com",
  "phone": "+1-555-0123",
  "confidence": 0.92
}
```

## Security

- **Users**: Read/Write/Create/Delete access to name cards
- **System Admins**: Full access + configuration settings

## Troubleshooting

### Common Issues

1. **"Missing dependencies"**
   - Install required system packages: `sudo apt install tesseract-ocr libtesseract-dev`
   - Install required Python packages: `pip install pytesseract huggingface_hub pillow numpy opencv-python-headless`

2. **"Processing failed"**
   - Check internet connection
   - Verify HuggingFace model name
   - Check image quality and format
   - Verify Tesseract installation: `tesseract --version`

3. **"Permission denied"**
   - Ensure user has proper access rights
   - Check security groups

4. **"Tesseract not found"**
   - Ensure Tesseract is installed and in PATH
   - On Windows: Add Tesseract installation directory to system PATH
   - Configure `pytesseract.pytesseract.tesseract_cmd` if needed

### Performance Tips

- Use smaller images for faster processing
- Configure appropriate HuggingFace model based on accuracy vs speed needs
- Monitor API usage if using paid HuggingFace models

## Development

### Extending the Module

1. **Add new fields** to `models/namecard.py`
2. **Update views** in `views/namecard_views.xml`  
3. **Modify AI processing** in `_process_with_ai()` method
4. **Add custom export formats** in `controllers/main.py`

### Testing

The module includes a comprehensive test suite covering:

#### Test Categories

1. **Unit Tests** (`test_namecard_model.py`) - 25 tests
   - Model creation and validation
   - OCR processing with mocked Tesseract
   - AI processing with mocked HuggingFace API
   - Partner creation workflows
   - Error handling and fallback mechanisms

2. **Controller Tests** (`test_namecard_controller.py`) - 15 tests
   - HTTP upload endpoints
   - JSON/vCard export functionality
   - Bulk upload capabilities
   - File validation and error responses

3. **Integration Tests** (`test_namecard_integration.py`) - 12 tests
   - End-to-end processing workflows
   - Partner integration with Odoo contacts
   - Mail/activity tracking
   - Search and filtering capabilities
   - Access rights and security

4. **Performance Tests** (`test_performance.py`) - 6 tests
   - Processing speed benchmarks
   - Bulk operations performance
   - Memory usage testing
   - Concurrent processing simulation

#### Running Tests

**Run all tests:**
```bash
odoo-bin -d test_db -i ocr_namecard --test-enable --stop-after-init
```

**Run specific test file:**
```bash
# Model tests only
odoo-bin -d test_db --test-tags ocr_namecard.test_namecard_model --test-enable --stop-after-init

# Controller tests only
odoo-bin -d test_db --test-tags ocr_namecard.test_namecard_controller --test-enable --stop-after-init

# Integration tests only  
odoo-bin -d test_db --test-tags ocr_namecard.test_namecard_integration --test-enable --stop-after-init

# Performance tests only
odoo-bin -d test_db --test-tags ocr_namecard.test_performance --test-enable --stop-after-init
```

**Run with verbose output:**
```bash
odoo-bin -d test_db -i ocr_namecard --test-enable --log-level=test --stop-after-init
```

**Generate test coverage report:**
```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run --source=ocr_namecard odoo-bin -d test_db -i ocr_namecard --test-enable --stop-after-init

# Generate reports
coverage report -m              # Terminal report
coverage html                   # HTML report in htmlcov/
```

#### CI/CD Integration

Example GitHub Actions workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        sudo apt install tesseract-ocr libtesseract-dev
        pip install odoo
        pip install pytesseract huggingface_hub pillow numpy opencv-python-headless coverage
    - name: Run tests
      run: |
        createdb -h localhost -U postgres test_db
        coverage run --source=ocr_namecard odoo-bin -d test_db -i ocr_namecard --test-enable --stop-after-init
        coverage xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

#### Manual Testing

Test the module with various name card formats:
- Different languages (English, Vietnamese, etc.)
- Various layouts (vertical, horizontal, minimalist)
- Low quality images (blurry, poor lighting)
- Different file formats (PNG, JPG, etc.)
- Handwritten text vs printed text

## License

LGPL-3 (same as Odoo)