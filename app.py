#!/usr/bin/env python3
"""
Name Card Reader App
Uses PaddleOCR to extract text from name card images and HuggingFace to process the extracted information.
"""

import os
import sys
from pathlib import Path
import json
from paddleocr import PaddleOCR
from PIL import Image
import argparse
from huggingface_hub import InferenceClient
import cv2
import numpy as np
import tempfile
import io
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class GoogleDriveHandler:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """Initialize Google Drive API handler."""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive API authenticated successfully")
        
    def get_folder_id_by_name(self, folder_name, parent_folder_id='root'):
        """Get folder ID by name."""
        if not self.service:
            self.authenticate()
            
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and parents in '{parent_folder_id}'"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if not items:
            return None
        return items[0]['id']
    
    def list_images_in_folder(self, folder_id):
        """List all image files in a Google Drive folder."""
        if not self.service:
            self.authenticate()
            
        # Query for image files in the folder
        image_mimes = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 
            'image/tiff', 'image/tif', 'image/gif'
        ]
        mime_query = " or ".join([f"mimeType='{mime}'" for mime in image_mimes])
        query = f"parents in '{folder_id}' and ({mime_query})"
        
        results = self.service.files().list(
            q=query,
            fields="files(id, name, size, mimeType)",
            pageSize=1000
        ).execute()
        
        return results.get('files', [])
    
    def download_image(self, file_id, file_name):
        """Download an image file from Google Drive to temporary file."""
        if not self.service:
            self.authenticate()
            
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1])
            
            downloader = MediaIoBaseDownload(temp_file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Error downloading {file_name}: {e}")
            return None



class NameCardReader:
    def __init__(self, model_name="openai/gpt-oss-20b", hf_token='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'):
        """Initialize the name card reader with PaddleOCR and HuggingFace configuration."""
        
        # Initialize PaddleOCR with multiple languages
        print("Initializing PaddleOCR for Japanese, English, and Vietnamese...")
        try:
            # Initialize OCR engines for different languages with error handling
            import os
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
            
            self.ocr_en = PaddleOCR(use_angle_cls=True, lang='en')
            print("✅ English OCR initialized")
            
            self.ocr_japan = PaddleOCR(use_angle_cls=True, lang='japan')
            print("✅ Japanese OCR initialized")
            
            self.ocr_vi = PaddleOCR(use_angle_cls=True, lang='vi')
            print("✅ Vietnamese OCR initialized")
            
        except Exception as e:
            print(f"❌ PaddleOCR initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize PaddleOCR: {e}")
            
        self.client = InferenceClient(
            provider="fireworks-ai",
            api_key="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",
        )
        
    def extract_text(self, image_path):
        """Extract text from name card image using PaddleOCR."""
        try:
            results = []
            
            # Try English OCR
            try:
                print("🇺🇸 Trying English OCR...")
                en_results = self.ocr_en.ocr(image_path)
                if en_results and en_results[0]:
                    en_processed = self._process_paddleocr_results(en_results[0], 'en')
                    if en_processed:
                        results.append(('en', en_processed))
                        print(f"✅ English: {len(en_processed)} texts found")
            except Exception as e:
                print(f"❌ English OCR failed: {e}")
            
            # Try Japanese OCR
            try:
                print("🇯🇵 Trying Japanese OCR...")
                jp_results = self.ocr_japan.ocr(image_path)
                if jp_results and jp_results[0]:
                    jp_processed = self._process_paddleocr_results(jp_results[0], 'japan')
                    if jp_processed:
                        results.append(('japan', jp_processed))
                        print(f"✅ Japanese: {len(jp_processed)} texts found")
            except Exception as e:
                print(f"❌ Japanese OCR failed: {e}")
            
            # Try Vietnamese OCR
            try:
                print("🇻🇳 Trying Vietnamese OCR...")
                vi_results = self.ocr_vi.ocr(image_path)
                if vi_results and vi_results[0]:
                    vi_processed = self._process_paddleocr_results(vi_results[0], 'vi')
                    if vi_processed:
                        results.append(('vi', vi_processed))
                        print(f"✅ Vietnamese: {len(vi_processed)} texts found")
            except Exception as e:
                print(f"❌ Vietnamese OCR failed: {e}")
            
            # Combine all results from different languages
            if not results:
                print("❌ No OCR results found")
                return []
            
            combined_results = self._combine_all_language_results(results)
            print(f"🔗 Combined results: {len(combined_results)} total texts from {len(results)} languages")
            
            return combined_results
            
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return []
    
    def _process_paddleocr_results(self, raw_results, lang_combo):
        """Process raw PaddleOCR results into standardized format"""
        processed_results = []
        
        # Handle PaddleOCR format: list of [bbox, (text, confidence)]
        for i in range(len(raw_results['rec_texts'])):
            try:
                bbox = raw_results['rec_boxes'][i]
                text_conf = raw_results['rec_texts'][i]
                confidence = raw_results['rec_scores'][i]

                if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
                    text = str(text_conf[0])
                    confidence = float(text_conf[1])
                else:
                    text = str(text_conf)
                    confidence = 1.0

                # Convert numpy array to float if needed
                if hasattr(confidence, 'item'):
                    confidence = confidence.item()

                if confidence > 0.3 and text.strip():  # Filter low confidence and empty text
                    processed_results.append({
                        'text': text.strip(),
                        'confidence': confidence,
                        'bbox': bbox,
                        'lang_combo': lang_combo
                    })
            except Exception as e:
                print(f"⚠️ Error processing OCR item: {e}")
                continue
        # for item in raw_results:
        #     try:
        #         if len(item) >= 2:
        #             bbox = item[0]
        #             text_conf = item[1]
        #
        #             if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
        #                 text = str(text_conf[0])
        #                 confidence = float(text_conf[1])
        #             else:
        #                 text = str(text_conf)
        #                 confidence = 1.0
        #
        #             # Convert numpy array to float if needed
        #             if hasattr(confidence, 'item'):
        #                 confidence = confidence.item()
        #
        #             if confidence > 0.3 and text.strip():  # Filter low confidence and empty text
        #                 processed_results.append({
        #                     'text': text.strip(),
        #                     'confidence': confidence,
        #                     'bbox': bbox,
        #                     'lang_combo': lang_combo
        #                 })
        #     except Exception as e:
        #         print(f"⚠️ Error processing OCR item: {e}")
        #         continue
                
        return processed_results
    
    def _combine_all_language_results(self, results):
        """Combine results from all languages and remove duplicates"""
        combined_results = []
        seen_texts = set()
        
        for lang_combo, processed_results in results:
            if not processed_results:
                continue
            
            print(f"📊 {lang_combo}: {len(processed_results)} texts")
            
            for item in processed_results:
                text = item['text'].strip().lower()
                
                # Check for duplicate text (case insensitive)
                if text not in seen_texts and text:
                    seen_texts.add(text)
                    combined_results.append(item)
                    print(f"  ✅ Added: {item['text']} (confidence: {item['confidence']:.3f})")
                else:
                    print(f"  ⚠️ Duplicate skipped: {item['text']}")
        
        # Sort by confidence (highest first)
        combined_results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return combined_results
    
    
    def _preprocess_image(self, image):
        """Preprocess image to improve OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        processed = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Optional: Apply morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def process_with_huggingface(self, extracted_text):
        """Process extracted text with HuggingFace to structure the information."""
        if not extracted_text:
            return {"error": "No text extracted from image"}
            
        # Combine all extracted text
        text_content = " ".join([item['text'] for item in extracted_text])
        
        prompt = f"""
        Please analyze the following text extracted from a business card and structure it into JSON format.
        Extract and organize the following information if available:
        - name (full name of the person)
        - title (job title/position)
        - company (company name)
        - email (email address)
        - phone (phone number)
        - address (physical address)
        - website (website URL)
        - university (if applicable)
        - department (if applicable)
        - language (language of the text, e.g., English, Japanese, Vietnamese)
        - social_media (any social media links)
        - notes (any additional notes or comments)
        - other (any other relevant information)
        
        Text from business card: {text_content}
        
        Return only valid JSON format without any additional explanation or markdown formatting.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            try:
                # Try to parse the response as JSON
                structured_data = json.loads(response.choices[0].message.content)
                return structured_data
            except json.JSONDecodeError:
                # If not valid JSON, return the raw response
                return {"raw_response": response}
                
        except Exception as e:
            return {"error": f"Failed to process with HuggingFace: {e}"}
    
    def process_name_card(self, image_path):
        """Complete workflow to process a name card image."""
        print(f"Processing image: {image_path}")
        
        # Check if image exists
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        # Extract text using PaddleOCR
        print("Extracting text with PaddleOCR...")
        extracted_text = self.extract_text(image_path)
        
        if not extracted_text:
            return {"error": "No text could be extracted from the image"}
        
        print(f"Extracted {len(extracted_text)} text elements")
        print("Extracted Text:")
        for item in extracted_text:
            print(f"  - {item['text']} (confidence: {item['confidence']:.3f}, lang: {item['lang_combo']})")
        # Process with HuggingFace
        print("Processing with HuggingFace...")
        structured_data = self.process_with_huggingface(extracted_text)
        print("Structured Data:")
        print(json.dumps(structured_data, indent=2, ensure_ascii=False))
        return {
            "structured_data": structured_data
        }
    
    def process_folder(self, folder_path, output_file=None):
        """Process all images in a folder."""
        print(f"Processing folder: {folder_path}")
        
        # Check if folder exists
        if not os.path.exists(folder_path):
            return {"error": f"Folder not found: {folder_path}"}
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        image_files = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(folder_path, file))
        
        if not image_files:
            return {"error": "No image files found in folder"}
        
        print(f"Found {len(image_files)} image files")
        
        # Process each image
        results = []
        for i, image_path in enumerate(image_files, 1):
            print(f"\n{'='*60}")
            print(f"Processing image {i}/{len(image_files)}: {os.path.basename(image_path)}")
            print(f"{'='*60}")
            
            result = self.process_name_card(image_path)
            result['file_index'] = i
            result['filename'] = os.path.basename(image_path)
            results.append(result)
        
        # Compile summary
        folder_result = {
            "folder_path": folder_path,
            "total_images": len(image_files),
            "processed_images": len(results),
            "results": results,
            "summary": {
                "successful": len([r for r in results if "error" not in r]),
                "failed": len([r for r in results if "error" in r])
            }
        }
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(folder_result, f, indent=2, ensure_ascii=False)
                print(f"\n📁 Results saved to: {output_file}")
            except Exception as e:
                print(f"\n⚠️ Failed to save results: {e}")
        
        return folder_result
    
    def process_google_drive_folder(self, folder_id_or_name, output_file=None, credentials_file='credentials.json'):
        """Process all images in a Google Drive folder."""
        print(f"Processing Google Drive folder: {folder_id_or_name}")
        
        # Initialize Google Drive handler
        drive_handler = GoogleDriveHandler(credentials_file)
        
        try:
            drive_handler.authenticate()
        except Exception as e:
            return {"error": f"Failed to authenticate with Google Drive: {e}"}
        
        # Get folder ID if folder name is provided
        folder_id = folder_id_or_name
        if not folder_id_or_name.startswith('1'):  # Assume it's a folder name if not starting with '1'
            folder_id = drive_handler.get_folder_id_by_name(folder_id_or_name)
            if not folder_id:
                return {"error": f"Folder '{folder_id_or_name}' not found in Google Drive"}
        
        # Get list of images
        try:
            image_files = drive_handler.list_images_in_folder(folder_id)
        except Exception as e:
            return {"error": f"Failed to list files in folder: {e}"}
        
        if not image_files:
            return {"error": "No image files found in Google Drive folder"}
        
        print(f"Found {len(image_files)} image files in Google Drive")
        
        # Process each image
        results = []
        temp_files = []  # Keep track of temp files to clean up
        
        for i, file_info in enumerate(image_files, 1):
            print(f"\n{'='*60}")
            print(f"Processing image {i}/{len(image_files)}: {file_info['name']}")
            print(f"Size: {int(file_info.get('size', 0)) / 1024:.1f} KB")
            print(f"{'='*60}")
            
            # Download image to temporary file
            temp_path = drive_handler.download_image(file_info['id'], file_info['name'])
            
            if temp_path:
                temp_files.append(temp_path)
                
                # Process the downloaded image
                result = self.process_name_card(temp_path)
                result['file_index'] = i
                result['filename'] = file_info['name']
                result['drive_file_id'] = file_info['id']
                result['file_size'] = file_info.get('size', 0)
                results.append(result)
            else:
                # Add error result if download failed
                results.append({
                    'file_index': i,
                    'filename': file_info['name'],
                    'drive_file_id': file_info['id'],
                    'error': 'Failed to download from Google Drive'
                })
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        # Compile summary
        folder_result = {
            "source": "google_drive",
            "folder_id": folder_id,
            "folder_name": folder_id_or_name,
            "total_images": len(image_files),
            "processed_images": len(results),
            "results": results,
            "summary": {
                "successful": len([r for r in results if "error" not in r]),
                "failed": len([r for r in results if "error" in r])
            }
        }
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(folder_result, f, indent=2, ensure_ascii=False)
                print(f"\n📁 Results saved to: {output_file}")
            except Exception as e:
                print(f"\n⚠️ Failed to save results: {e}")
        
        return folder_result


def main():
    parser = argparse.ArgumentParser(description="Read and process name card images")
    parser.add_argument("path", help="Path to the name card image, local folder, or Google Drive folder name/ID")
    parser.add_argument("--folder", action="store_true", help="Process all images in the specified local folder")
    parser.add_argument("--google-drive", action="store_true", help="Process all images in the specified Google Drive folder")
    parser.add_argument("--credentials", default="credentials.json", help="Google Drive credentials file (default: credentials.json)")
    parser.add_argument("--model", default="microsoft/DialoGPT-medium", help="HuggingFace model to use (default: microsoft/DialoGPT-medium)")
    parser.add_argument("--hf-token", help="HuggingFace API token")
    parser.add_argument("--output", help="Output file to save results (JSON format)")
    
    args = parser.parse_args()
    
    # Initialize name card reader
    reader = NameCardReader(model_name=args.model, hf_token=args.hf_token)
    
    # Process based on mode
    if args.google_drive:
        # Process Google Drive folder
        result = reader.process_google_drive_folder(args.path, args.output, args.credentials)
        
        # Print summary
        print("\n" + "="*60)
        print("GOOGLE DRIVE PROCESSING RESULTS")
        print("="*60)
        print(f"☁️ Drive Folder: {result.get('folder_name', 'N/A')}")
        print(f"📊 Total images: {result.get('total_images', 0)}")
        print(f"✅ Successful: {result.get('summary', {}).get('successful', 0)}")
        print(f"❌ Failed: {result.get('summary', {}).get('failed', 0)}")
        
        if not args.output:
            print("\n" + "="*60)
            print("DETAILED RESULTS")
            print("="*60)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.folder:
        # Process local folder
        result = reader.process_folder(args.path, args.output)
        
        # Print summary
        print("\n" + "="*60)
        print("LOCAL FOLDER PROCESSING RESULTS")
        print("="*60)
        print(f"📁 Folder: {result.get('folder_path', 'N/A')}")
        print(f"📊 Total images: {result.get('total_images', 0)}")
        print(f"✅ Successful: {result.get('summary', {}).get('successful', 0)}")
        print(f"❌ Failed: {result.get('summary', {}).get('failed', 0)}")
        
        if not args.output:
            print("\n" + "="*60)
            print("DETAILED RESULTS")
            print("="*60)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Process single image
        result = reader.process_name_card(args.path)
        
        # Print results
        print("\n" + "="*50)
        print("SINGLE IMAGE RESULTS")
        print("="*50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to file if requested (only for single image mode)
    if args.output and not args.folder and not args.google_drive:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()