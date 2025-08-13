import json
import base64
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from io import BytesIO
from odoo.tests.common import HttpCase
from odoo.http import request
from .common import NameCardHttpTestCase


class TestNameCardController(NameCardHttpTestCase):
    """Test cases for name card HTTP controllers"""

    def setUp(self):
        super().setUp()
        self.authenticate('admin', 'admin')

    def test_upload_namecard_success(self):
        """Test successful name card upload"""
        # Create file-like object
        image_data = self.test_image_data
        
        with patch('odoo.http.request') as mock_request:
            # Mock the request object
            mock_file = MagicMock()
            mock_file.filename = 'test_card.jpg'
            mock_file.read.return_value = image_data
            
            mock_request.httprequest.files = {'image': mock_file}
            mock_request.env = self.env
            
            # Import and test controller
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.upload_namecard()
            result = json.loads(response)
            
            self.assertTrue(result['success'])
            self.assertIn('namecard_id', result)
            self.assertIn('message', result)

    def test_upload_namecard_no_file(self):
        """Test upload without file"""
        with patch('odoo.http.request') as mock_request:
            mock_request.httprequest.files = {}
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.upload_namecard()
            result = json.loads(response)
            
            self.assertFalse(result.get('success', True))
            self.assertIn('error', result)
            self.assertIn('No image file provided', result['error'])

    def test_upload_namecard_empty_filename(self):
        """Test upload with empty filename"""
        with patch('odoo.http.request') as mock_request:
            mock_file = MagicMock()
            mock_file.filename = ''
            mock_request.httprequest.files = {'image': mock_file}
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.upload_namecard()
            result = json.loads(response)
            
            self.assertFalse(result.get('success', True))
            self.assertIn('No image file selected', result['error'])

    def test_upload_namecard_invalid_extension(self):
        """Test upload with invalid file extension"""
        with patch('odoo.http.request') as mock_request:
            mock_file = MagicMock()
            mock_file.filename = 'test_card.txt'
            mock_request.httprequest.files = {'image': mock_file}
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.upload_namecard()
            result = json.loads(response)
            
            self.assertFalse(result.get('success', True))
            self.assertIn('Invalid file type', result['error'])

    def test_get_processing_status_success(self):
        """Test getting processing status of existing namecard"""
        # Create test namecard
        namecard = self.NameCard.create({
            'image': base64.b64encode(self.test_image_data).decode('utf-8'),
            'image_filename': 'test.jpg',
            'processing_status': 'done',
            'contact_name': 'John Smith',
            'company_name': 'Tech Corp',
            'email': 'john@techcorp.com',
            'extraction_confidence': 0.95
        })
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            result = controller.get_processing_status(namecard.id)
            
            self.assertEqual(result['status'], 'done')
            self.assertEqual(result['contact_name'], 'John Smith')
            self.assertEqual(result['company_name'], 'Tech Corp')
            self.assertEqual(result['email'], 'john@techcorp.com')
            self.assertEqual(result['confidence'], 0.95)

    def test_get_processing_status_not_found(self):
        """Test getting status of non-existent namecard"""
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            result = controller.get_processing_status(99999)
            
            self.assertIn('error', result)
            self.assertIn('not found', result['error'])

    def test_export_namecard_json(self):
        """Test exporting namecard as JSON"""
        # Create test namecard
        namecard = self.NameCard.create({
            'image': base64.b64encode(self.test_image_data).decode('utf-8'),
            'image_filename': 'test.jpg',
            'contact_name': 'John Smith',
            'company_name': 'Tech Corp',
            'email': 'john@techcorp.com',
            'phone': '+1-555-0123'
        })
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.make_response = MagicMock()
            mock_request.not_found = MagicMock()
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            controller.export_namecard(namecard.id, 'json')
            
            # Check that make_response was called
            mock_request.make_response.assert_called_once()
            args, kwargs = mock_request.make_response.call_args
            
            # Parse the JSON response
            json_data = json.loads(args[0])
            self.assertEqual(json_data['name'], 'John Smith')
            self.assertEqual(json_data['company'], 'Tech Corp')
            self.assertEqual(json_data['email'], 'john@techcorp.com')

    def test_export_namecard_vcard(self):
        """Test exporting namecard as vCard"""
        # Create test namecard
        namecard = self.NameCard.create({
            'image': base64.b64encode(self.test_image_data).decode('utf-8'),
            'image_filename': 'test.jpg',
            'contact_name': 'John Smith',
            'company_name': 'Tech Corp',
            'email': 'john@techcorp.com',
            'phone': '+1-555-0123'
        })
        
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.make_response = MagicMock()
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            controller.export_namecard(namecard.id, 'vcard')
            
            # Check that make_response was called
            mock_request.make_response.assert_called_once()
            args, kwargs = mock_request.make_response.call_args
            
            # Check vCard content
            vcard_content = args[0]
            self.assertIn('BEGIN:VCARD', vcard_content)
            self.assertIn('FN:John Smith', vcard_content)
            self.assertIn('ORG:Tech Corp', vcard_content)
            self.assertIn('EMAIL:john@techcorp.com', vcard_content)
            self.assertIn('END:VCARD', vcard_content)

    def test_export_namecard_not_found(self):
        """Test exporting non-existent namecard"""
        with patch('odoo.http.request') as mock_request:
            mock_request.env = self.env
            mock_request.not_found = MagicMock()
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            controller.export_namecard(99999, 'json')
            
            mock_request.not_found.assert_called_once()

    def test_generate_vcard(self):
        """Test vCard generation"""
        namecard = self.NameCard.create({
            'image': base64.b64encode(self.test_image_data).decode('utf-8'),
            'image_filename': 'test.jpg',
            'contact_name': 'John Smith',
            'company_name': 'Tech Corp',
            'job_title': 'Developer',
            'email': 'john@techcorp.com',
            'phone': '+1-555-0123',
            'mobile': '+1-555-0456',
            'website': 'www.techcorp.com',
            'address': '123 Main St',
            'other_info': 'Additional notes'
        })
        
        from odoo.addons.ocr_namecard.controllers.main import NameCardController
        controller = NameCardController()
        
        vcard = controller._generate_vcard(namecard)
        
        expected_lines = [
            'BEGIN:VCARD',
            'VERSION:3.0',
            'FN:John Smith',
            'N:Smith;John;;;',
            'ORG:Tech Corp',
            'TITLE:Developer',
            'EMAIL:john@techcorp.com',
            'TEL;TYPE=WORK:+1-555-0123',
            'TEL;TYPE=CELL:+1-555-0456',
            'URL:www.techcorp.com',
            'ADR;TYPE=WORK:;;123 Main St;;;;',
            'NOTE:Additional notes',
            'END:VCARD'
        ]
        
        for line in expected_lines:
            self.assertIn(line, vcard)

    def test_bulk_upload_success(self):
        """Test successful bulk upload"""
        image_data = self.test_image_data
        
        with patch('odoo.http.request') as mock_request:
            # Mock multiple files
            mock_file1 = MagicMock()
            mock_file1.filename = 'card1.jpg'
            mock_file1.read.return_value = image_data
            
            mock_file2 = MagicMock()
            mock_file2.filename = 'card2.jpg'
            mock_file2.read.return_value = image_data
            
            mock_request.httprequest.files.getlist.return_value = [mock_file1, mock_file2]
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.bulk_upload_namecards()
            result = json.loads(response)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['total_files'], 2)
            self.assertEqual(result['successful_uploads'], 2)
            self.assertEqual(len(result['results']), 2)

    def test_bulk_upload_mixed_results(self):
        """Test bulk upload with mixed success/failure"""
        image_data = self.test_image_data
        
        with patch('odoo.http.request') as mock_request:
            # Mock files with mixed valid/invalid types
            mock_file1 = MagicMock()
            mock_file1.filename = 'card1.jpg'
            mock_file1.read.return_value = image_data
            
            mock_file2 = MagicMock()
            mock_file2.filename = 'card2.txt'  # Invalid type
            
            mock_request.httprequest.files.getlist.return_value = [mock_file1, mock_file2]
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.bulk_upload_namecards()
            result = json.loads(response)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['total_files'], 2)
            self.assertEqual(result['successful_uploads'], 1)
            
            # Check individual results
            results = result['results']
            self.assertTrue(results[0]['success'])
            self.assertFalse(results[1]['success'])
            self.assertIn('Invalid file type', results[1]['error'])

    def test_bulk_upload_no_files(self):
        """Test bulk upload without files"""
        with patch('odoo.http.request') as mock_request:
            mock_request.httprequest.files.getlist.return_value = []
            mock_request.env = self.env
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.bulk_upload_namecards()
            result = json.loads(response)
            
            self.assertFalse(result.get('success', True))
            self.assertIn('No image files provided', result['error'])

    def test_controller_exception_handling(self):
        """Test controller exception handling"""
        with patch('odoo.http.request') as mock_request:
            mock_request.env.side_effect = Exception("Database error")
            
            from odoo.addons.ocr_namecard.controllers.main import NameCardController
            controller = NameCardController()
            
            response = controller.upload_namecard()
            result = json.loads(response)
            
            self.assertIn('error', result)
            self.assertIn('Database error', result['error'])