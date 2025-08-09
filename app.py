#!/usr/bin/env python3
"""
Name Card Reader App
Uses EasyOCR to extract text from name card images and Ollama to process the extracted information.
"""

import os
import sys
from pathlib import Path
import json
import requests
import easyocr
from PIL import Image
import argparse


class NameCardReader:
    def __init__(self, ollama_host="http://localhost:11434"):
        """Initialize the name card reader with EasyOCR and Ollama configuration."""
        self.reader = easyocr.Reader(['en'])
        self.ollama_host = ollama_host
        
    def extract_text(self, image_path):
        """Extract text from name card image using EasyOCR."""
        try:
            results = self.reader.readtext(image_path)
            extracted_text = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filter out low-confidence results
                    extracted_text.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
            
            return extracted_text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return []
    
    def process_with_ollama(self, extracted_text, model="gpt-oss:20b"):
        """Process extracted text with Ollama to structure the information."""
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
        - other (any other relevant information)
        
        Text from business card: {text_content}
        
        Return only valid JSON format without any additional explanation or markdown formatting.
        """
        
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                try:
                    # Try to parse the response as JSON
                    structured_data = json.loads(result['response'])
                    return structured_data
                except json.JSONDecodeError:
                    # If not valid JSON, return the raw response
                    return {"raw_response": result['response']}
            else:
                return {"error": f"Ollama request failed with status {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to Ollama: {e}"}
    
    def process_name_card(self, image_path, model="gpt-oss:20b"):
        """Complete workflow to process a name card image."""
        print(f"Processing image: {image_path}")
        
        # Check if image exists
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        # Extract text using EasyOCR
        print("Extracting text with EasyOCR...")
        extracted_text = self.extract_text(image_path)
        
        if not extracted_text:
            return {"error": "No text could be extracted from the image"}
        
        print(f"Extracted {len(extracted_text)} text elements")
        
        # Process with Ollama
        print("Processing with Ollama...")
        structured_data = self.process_with_ollama(extracted_text, model)
        
        return {
            "image_path": image_path,
            "extracted_text": extracted_text,
            "structured_data": structured_data
        }


def main():
    parser = argparse.ArgumentParser(description="Read and process name card images")
    parser.add_argument("image_path", help="Path to the name card image")
    parser.add_argument("--model", default="gpt-oss:20b", help="Ollama model to use (default: gpt-oss:20b)")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama host URL")
    parser.add_argument("--output", help="Output file to save results (JSON format)")
    
    args = parser.parse_args()
    
    # Initialize name card reader
    reader = NameCardReader(ollama_host=args.ollama_host)
    
    # Process the image
    result = reader.process_name_card(args.image_path, args.model)
    
    # Print results
    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()