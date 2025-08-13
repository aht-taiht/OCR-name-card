#!/usr/bin/env python3
"""
Tesseract Installation Checker
Quick utility to verify Tesseract OCR installation and configuration.
"""

import os
import sys
import shutil
import platform
import subprocess

def find_tesseract():
    """Find Tesseract executable path"""
    # Try PATH first
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        return tesseract_path
    
    # Common installation paths
    common_paths = [
        # Linux/Unix
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract',
        # macOS (Homebrew)
        '/opt/homebrew/bin/tesseract',
        '/usr/local/bin/tesseract',
        # Windows
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def check_tesseract():
    """Check Tesseract installation"""
    print("🔍 Checking Tesseract OCR installation...")
    print("-" * 50)
    
    # Find Tesseract
    tesseract_path = find_tesseract()
    
    if not tesseract_path:
        print("❌ Tesseract NOT FOUND")
        show_installation_instructions()
        return False
    
    print(f"✅ Tesseract found at: {tesseract_path}")
    
    # Test version
    try:
        result = subprocess.run([tesseract_path, '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Version: {version_line}")
        else:
            print(f"⚠️  Version check failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not get version: {e}")
    
    # Test languages
    try:
        result = subprocess.run([tesseract_path, '--list-langs'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            langs = result.stdout.strip().split('\n')[1:]  # Skip header
            print(f"✅ Available languages: {', '.join(langs[:10])}" + ("..." if len(langs) > 10 else ""))
            
            # Check for common languages
            important_langs = ['eng', 'jpn', 'chi_sim']
            missing_langs = [lang for lang in important_langs if lang not in langs]
            if missing_langs:
                print(f"💡 Consider installing additional language packs: {', '.join(missing_langs)}")
        else:
            print(f"⚠️  Could not list languages: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Language check failed: {e}")
    
    # Test with Python
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        version = pytesseract.get_tesseract_version()
        print(f"✅ Python integration: pytesseract {version}")
        return True
    except ImportError:
        print("⚠️  pytesseract Python package not installed")
        print("   Install with: pip install pytesseract")
        return False
    except Exception as e:
        print(f"⚠️  Python integration failed: {e}")
        return False

def show_installation_instructions():
    """Show installation instructions for current platform"""
    system = platform.system().lower()
    
    print("\n📋 INSTALLATION INSTRUCTIONS")
    print("=" * 50)
    
    if system == 'linux':
        print("Ubuntu/Debian:")
        print("  sudo apt update")
        print("  sudo apt install tesseract-ocr libtesseract-dev")
        print("  sudo apt install tesseract-ocr-jpn tesseract-ocr-chi-sim  # Optional languages")
        print("\nCentOS/RHEL/Fedora:")
        print("  sudo dnf install tesseract")
        
    elif system == 'darwin':  # macOS
        print("macOS (Homebrew):")
        print("  brew install tesseract")
        print("  brew install tesseract-lang  # Optional: for additional languages")
        
    elif system == 'windows':
        print("Windows:")
        print("  1. Download installer from:")
        print("     https://github.com/UB-Mannheim/tesseract/wiki")
        print("  2. Run installer (use default location)")
        print("  3. Add to PATH or note installation path")
        
    else:
        print("Visit: https://github.com/tesseract-ocr/tesseract#installing-tesseract")
    
    print("\nPython package:")
    print("  pip install pytesseract opencv-python-headless")
    
    print("\nAfter installation, verify with:")
    print("  tesseract --version")

def test_ocr():
    """Test OCR functionality with a simple test"""
    try:
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        print("\n🧪 Testing OCR functionality...")
        
        # Create a simple test image
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default if not available
        try:
            # This might not work on all systems
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 30), "Test OCR Text", fill='black', font=font)
        
        # Convert PIL image to format pytesseract can use
        text = pytesseract.image_to_string(img, lang='eng')
        
        if "Test" in text and "OCR" in text:
            print("✅ OCR test successful!")
            print(f"   Detected: '{text.strip()}'")
            return True
        else:
            print(f"⚠️  OCR test partial: '{text.strip()}'")
            return False
            
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Tesseract OCR Installation Checker")
    print("=" * 50)
    
    # Check Tesseract
    tesseract_ok = check_tesseract()
    
    if tesseract_ok:
        # Test OCR functionality
        test_ocr()
        
        print("\n✅ Tesseract is ready to use!")
        print("\nYou can now run the name card reader:")
        print("  python app.py your_namecard.jpg")
    else:
        print("\n❌ Please install Tesseract and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())