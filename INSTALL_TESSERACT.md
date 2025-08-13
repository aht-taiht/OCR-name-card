# Tesseract OCR Installation Guide

Complete installation guide for Tesseract OCR across different operating systems.

## Quick Check

First, check if Tesseract is already installed:

```bash
python check_tesseract.py
```

This utility will:
- ✅ Detect if Tesseract is installed
- ✅ Show version and available languages
- ✅ Test Python integration
- ✅ Provide specific installation instructions

## Operating System Specific Instructions

### 🐧 Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Tesseract OCR
sudo apt install tesseract-ocr libtesseract-dev

# Install additional language packs (optional)
sudo apt install tesseract-ocr-jpn          # Japanese
sudo apt install tesseract-ocr-chi-sim      # Simplified Chinese
sudo apt install tesseract-ocr-chi-tra      # Traditional Chinese
sudo apt install tesseract-ocr-kor          # Korean
sudo apt install tesseract-ocr-ara          # Arabic

# Verify installation
tesseract --version
tesseract --list-langs
```

### 🐧 Linux (CentOS/RHEL/Fedora)

```bash
# CentOS/RHEL (with EPEL)
sudo yum install epel-release
sudo yum install tesseract

# Fedora
sudo dnf install tesseract

# Verify installation
tesseract --version
```

### 🍎 macOS

#### Using Homebrew (Recommended)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Tesseract
brew install tesseract

# Install additional languages (optional)
brew install tesseract-lang

# Verify installation
tesseract --version
tesseract --list-langs
```

#### Using MacPorts

```bash
# Install MacPorts if not already installed
# Visit: https://www.macports.org/install.php

# Install Tesseract
sudo port install tesseract

# Verify installation
tesseract --version
```

### 🪟 Windows

#### Method 1: Official Installer (Recommended)

1. **Download Installer**:
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest installer (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)

2. **Install Tesseract**:
   - Run the installer as Administrator
   - Use default installation path: `C:\Program Files\Tesseract-OCR`
   - Select additional language packs during installation

3. **Add to PATH**:
   - Open System Properties → Environment Variables
   - Add `C:\Program Files\Tesseract-OCR` to your PATH
   - Or use the full path in your application

4. **Verify Installation**:
   ```cmd
   tesseract --version
   ```

#### Method 2: Using Chocolatey

```powershell
# Install Chocolatey if not already installed
# Visit: https://chocolatey.org/install

# Install Tesseract
choco install tesseract

# Verify installation
tesseract --version
```

#### Method 3: Using Scoop

```powershell
# Install Scoop if not already installed
# Visit: https://scoop.sh/

# Add extras bucket
scoop bucket add extras

# Install Tesseract
scoop install tesseract

# Verify installation
tesseract --version
```

## Language Pack Installation

### Linux (Ubuntu/Debian)

```bash
# List available language packs
apt search tesseract-ocr-

# Install specific languages
sudo apt install tesseract-ocr-jpn          # Japanese
sudo apt install tesseract-ocr-chi-sim      # Chinese Simplified  
sudo apt install tesseract-ocr-chi-tra      # Chinese Traditional
sudo apt install tesseract-ocr-kor          # Korean
sudo apt install tesseract-ocr-ara          # Arabic
sudo apt install tesseract-ocr-fra          # French
sudo apt install tesseract-ocr-deu          # German
sudo apt install tesseract-ocr-spa          # Spanish
sudo apt install tesseract-ocr-ita          # Italian
sudo apt install tesseract-ocr-rus          # Russian
```

### macOS

```bash
# Homebrew installs many languages by default
brew install tesseract-lang

# Check available languages
tesseract --list-langs
```

### Windows

- Additional languages can be selected during Tesseract installation
- Or download language files from: https://github.com/tesseract-ocr/tessdata
- Place `.traineddata` files in: `C:\Program Files\Tesseract-OCR\tessdata\`

## Python Integration

### Install Python Package

```bash
pip install pytesseract opencv-python-headless pillow
```

### Test Python Integration

```python
import pytesseract
from PIL import Image

# Set tesseract command path (Windows only, if not in PATH)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Test version
print(pytesseract.get_tesseract_version())

# Test with sample image
img = Image.open('sample_image.jpg')
text = pytesseract.image_to_string(img, lang='eng')
print(text)
```

## Troubleshooting

### Common Issues

1. **"tesseract is not recognized as an internal or external command" (Windows)**
   - Tesseract not in PATH
   - Solution: Add installation directory to PATH or specify full path

2. **"TesseractNotFoundError"**
   - Tesseract not installed or not in PATH
   - Solution: Install Tesseract and ensure it's accessible

3. **Poor OCR Results**
   - Image quality issues
   - Wrong language setting
   - Solution: Preprocess images, use correct language codes

4. **"Failed loading language 'xxx'"**
   - Language pack not installed
   - Solution: Install required language pack

### Verification Commands

```bash
# Check if tesseract is in PATH
which tesseract          # Linux/macOS
where tesseract          # Windows

# Check version
tesseract --version

# List available languages
tesseract --list-langs

# Test OCR with image
tesseract input.jpg output.txt

# Use our comprehensive checker
python check_tesseract.py
```

## Configuration for Name Card Reader

### Automatic Detection

The name card reader will automatically detect Tesseract in common locations:

- Linux: `/usr/bin/tesseract`, `/usr/local/bin/tesseract`
- macOS: `/opt/homebrew/bin/tesseract`, `/usr/local/bin/tesseract`
- Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### Manual Configuration

If automatic detection fails, specify the path:

```bash
# Command line
python app.py namecard.jpg --tesseract-cmd "/path/to/tesseract"

# Or in Python code
import pytesseract
pytesseract.pytesseract.tesseract_cmd = '/path/to/tesseract'
```

## Performance Optimization

### 1. Image Preprocessing

The app automatically applies:
- Grayscale conversion
- Gaussian blur
- Adaptive thresholding
- Morphological operations

### 2. OCR Configuration

Best settings for name cards:
```bash
# Page Segmentation Mode (PSM)
--psm 6    # Uniform block of text (default)
--psm 8    # Single word (for single field extraction)
--psm 13   # Raw line (minimal processing)

# OCR Engine Mode (OEM)
--oem 3    # Default (LSTM + Legacy)
--oem 1    # LSTM only (faster, modern)
```

### 3. Language Selection

The app tries multiple language combinations:
1. `eng` (English only)
2. `eng+jpn` (English + Japanese)
3. `eng+chi_sim` (English + Chinese Simplified)
4. `eng+jpn+chi_sim` (All three)

## Security Considerations

- Tesseract processes images locally (no cloud dependency)
- Be cautious with file paths containing special characters
- Validate input images to prevent resource exhaustion
- Consider sandboxing in production environments

## Getting Help

1. **Run our diagnostic tool**: `python check_tesseract.py`
2. **Check Tesseract documentation**: https://tesseract-ocr.github.io/
3. **GitHub issues**: https://github.com/tesseract-ocr/tesseract/issues
4. **Stack Overflow**: Tag questions with `tesseract`

## Version Compatibility

- **Minimum supported**: Tesseract 4.0+
- **Recommended**: Tesseract 5.0+
- **Latest stable**: Check https://github.com/tesseract-ocr/tesseract/releases

The name card reader is tested with Tesseract 5.x but should work with any 4.x or 5.x version.