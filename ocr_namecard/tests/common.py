import base64
import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, HttpCase


class NameCardTestCase(TransactionCase):
    """Base test case for Name Card OCR tests"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.NameCard = cls.env['ocr.namecard']
        cls.Partner = cls.env['res.partner']
        cls.ConfigParameter = cls.env['ir.config_parameter']
        
        # Set up test configuration
        cls.ConfigParameter.sudo().set_param('ocr_namecard.hf_model', 'test/model')
        cls.ConfigParameter.sudo().set_param('ocr_namecard.hf_token', 'test_token')
        
        # Create test image data (minimal PNG)
        cls.test_image_data = base64.b64encode(cls._create_test_image()).decode('utf-8')
        
        # Mock OCR and AI responses
        cls.mock_ocr_response = [
            {
                'text': 'John Smith',
                'confidence': 0.95,
                'bbox': [[100, 50], [200, 50], [200, 80], [100, 80]]
            },
            {
                'text': 'Senior Developer',
                'confidence': 0.92,
                'bbox': [[100, 90], [250, 90], [250, 110], [100, 110]]
            },
            {
                'text': 'Tech Corp Inc.',
                'confidence': 0.88,
                'bbox': [[100, 120], [280, 120], [280, 140], [100, 140]]
            },
            {
                'text': 'john.smith@techcorp.com',
                'confidence': 0.93,
                'bbox': [[100, 150], [300, 150], [300, 170], [100, 170]]
            },
            {
                'text': '+1-555-0123',
                'confidence': 0.90,
                'bbox': [[100, 180], [200, 180], [200, 200], [100, 200]]
            }
        ]
        
        # Mock Tesseract data format
        cls.mock_tesseract_data = {
            'level': [1, 2, 3, 4, 5],
            'page_num': [1, 1, 1, 1, 1],
            'block_num': [0, 1, 1, 1, 1],
            'par_num': [0, 0, 1, 1, 1],
            'line_num': [0, 0, 0, 1, 2],
            'word_num': [0, 0, 0, 1, 1],
            'left': [100, 100, 100, 100, 100],
            'top': [50, 90, 120, 150, 180],
            'width': [100, 150, 180, 200, 100],
            'height': [30, 20, 20, 20, 20],
            'conf': [95, 92, 88, 93, 90],
            'text': ['John Smith', 'Senior Developer', 'Tech Corp Inc.', 
                    'john.smith@techcorp.com', '+1-555-0123']
        }
        
        cls.mock_ai_response = json.dumps({
            'name': 'John Smith',
            'title': 'Senior Developer', 
            'company': 'Tech Corp Inc.',
            'email': 'john.smith@techcorp.com',
            'phone': '+1-555-0123',
            'website': 'www.techcorp.com',
            'address': '123 Tech Street, Silicon Valley, CA 94000'
        })
    
    @staticmethod
    def _create_test_image():
        """Create minimal valid PNG image data"""
        # Minimal 1x1 PNG image
        return bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D,  # IHDR chunk length
            0x49, 0x48, 0x44, 0x52,  # IHDR
            0x00, 0x00, 0x00, 0x01,  # Width: 1
            0x00, 0x00, 0x00, 0x01,  # Height: 1
            0x08, 0x02,              # Bit depth: 8, Color type: 2 (RGB)
            0x00, 0x00, 0x00,        # Compression, filter, interlace
            0x90, 0x77, 0x53, 0xDE,  # CRC
            0x00, 0x00, 0x00, 0x0C,  # IDAT chunk length
            0x49, 0x44, 0x41, 0x54,  # IDAT
            0x08, 0x99, 0x01, 0x01, 0x00, 0x01, 0x00, 0xFE, 0xFF, 0x00, 0x00, 0x00,
            0x02, 0x00, 0x01,        # Image data
            0xE5, 0x27, 0xDE, 0xFC,  # CRC
            0x00, 0x00, 0x00, 0x00,  # IEND chunk length
            0x49, 0x45, 0x4E, 0x44,  # IEND
            0xAE, 0x42, 0x60, 0x82   # CRC
        ])
    
    def create_test_namecard(self, **kwargs):
        """Create a test name card with default values"""
        default_values = {
            'image': self.test_image_data,
            'image_filename': 'test_card.jpg',
            'processing_status': 'draft'
        }
        default_values.update(kwargs)
        return self.NameCard.create(default_values)
    
    def mock_ocr_extraction(self):
        """Mock EasyOCR extraction"""
        return patch('easyocr.Reader') 
    
    def mock_ai_processing(self, response=None):
        """Mock HuggingFace AI processing"""
        if response is None:
            response = self.mock_ai_response
            
        mock_client = MagicMock()
        mock_client.text_generation.return_value = response
        
        return patch('huggingface_hub.InferenceClient', return_value=mock_client)


class NameCardHttpTestCase(HttpCase):
    """Base test case for HTTP controller tests"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.NameCard = cls.env['ocr.namecard']
        
        # Create test user with proper access rights
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })
        
        # Create test image data
        cls.test_image_data = NameCardTestCase._create_test_image()
    
    def authenticate_user(self):
        """Authenticate test user for HTTP requests"""
        self.authenticate('test_user', 'test_user')